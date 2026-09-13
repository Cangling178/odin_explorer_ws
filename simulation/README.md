# Simulation plan

English | [Chinese](README_cn.md)

A Gazebo Classic 11 standalone Odin sensor bench and a dynamic chassis contact test using the existing masses are available; ros2_control vehicle drive is integrated.
Select the simulator after the ROS/JetPack and drive-model decisions.
Run compute-heavy simulation on the workstation where practical.

Begin with deterministic planar tests: straight, constant-radius arc, S-curve,
crossing with repeated coordinates, sharp corner and controlled data dropout.
Then model measured wheel geometry, actuator delay, saturation, slip and camera
field of view. Test that the chassis can traverse the surveyed corridor.

Acceptance: correct ordered progress, bounded command output, explicit invalid
state on missing observations, no corner shortcuts, and reproducible error/time
reports. Simulation results do not substitute for independent physical trials.

## Odin sensor bench

Uses locally installed Gazebo Classic 11 / ROS2 Humble gazebo_plugins;
this is an existing-environment test backend, not a long-term platform decision.

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-select racer_description
source install/local_setup.bash
ros2 launch racer_description odin_sensors.launch.py
```

Optional gui:=false still requires graphics for camera rendering. Stop the URDF
preview first to avoid duplicate simulated sensor TF. Topics: /sim/odin1/image,
/sim/odin1/camera_info, /sim/odin1/cloud_raw, /sim/odin1/imu and /clock.
Consumers use use_sim_time=true. Stationary sensor at 0.5 m, target at 2 m;
not the chassis mounting height or a drivable robot.

RGB: 1600x1296, 10 Hz, horizontal FOV 129 degrees, PINHOLE approximation.
Vertical FOV follows aspect ratio, not official 104 degrees. No FishPoly model;
CameraInfo describes the simulated pinhole, not device fisheye calibration.
Ray cloud: 240x180, 120x90 degrees, 10 Hz, 0.2-30 m. Not actual DTOF imaging;
invalid returns may be filtered, no confidence/offset_time fields or calibrated
noise, reflectivity or 70 m bright-target behavior.
IMU: ideal, no drift/noise, 400 Hz simulation setting from SDK smooth-send default,
not verified hardware rate. Official IMU<-LiDAR translation used.
Camera relative transform from local O1-P040100136 calibration (archived under
hardware/mechanical/odin1/calib_device.yaml), rotation orthonormalized then inverted.
Housing->LiDAR approximate CAD RX lens center (15.55,5.5,31) mm, NOT calibrated.
Simulation TF names odin_sim_* do not replace vendor frames.
No proprietary SLAM, relocalization, map saving or AE/AWB services implemented.

Sources: [specifications](https://manifoldtechltd.github.io/wiki/odin_series/odin1/14.%20Technical%20Specifications_.html),
[data output](https://manifoldtechltd.github.io/wiki/odin_series/odin1/5.%20Data%20output_.html).

Validation: locally received 1600x1296 image/CameraInfo, XYZ/intensity cloud and IMU (stationary Z acceleration 9.81 m/s^2). Motion response and hardware equivalence unvalidated.

## Chassis ground-contact test

An independent dynamic scene is generated from the current Xacro without adding
unknown component masses. Fixed-joint groups have their masses, COMs and inertias
combined using frame rotations and the parallel-axis theorem; all visuals and
collisions are transferred. The result has three bodies: a 0.785 kg chassis and
two 0.046 kg wheels, totaling 0.877 kg, with all 25 collisions and two free wheel
joints. Front balls act as low-friction sliding supports, without ball rotation.
The source URDF TF tree and component inertias remain unchanged; SDF mass is not
double-counted.

Settings live in [ground_contact.yaml](../src/odin_racer/racer_description/config/ground_contact.yaml).
The world generator reads this file; it is not a ROS node parameter file.
All values below are initial engineering choices, not measured calibration:

| Parameter | Initial value | Purpose |
| --- | --- | --- |
| Rear tire mu / mu2 | 0.8 / 0.8 | Tire contact friction |
| Front ball mu / mu2 | 0.02 / 0.02 | Low-friction support approximation, not measured rolling resistance |
| Other parts / ground friction | 0.5 / 1.0 | Ground does not limit smaller object coefficients |
| Contact kp / kd | 100000 N/m / 100 N s/m | Contact stiffness and damping |
| min_depth | 0.0001 m | Correction tolerance, not a hard penetration limit |
| max_vel | 0.1 m/s | Penetration correction speed limit, not vehicle speed |
| Restitution coefficient | 0 | No added restitution bounce |
| Maximum contacts | 10 per collision | Tire contact solution |
| ODE step / iterations / SOR | 1 ms / 80 / 1.3 | Quick solver, pyramid friction model |
| Wheel joint damping | 0.0001 N m s/rad | Small damping on free wheels, not a motor brake |
| Initial ground clearance | 20 mm | Release height derived from lowest geometry |

kp and kd are assigned to both ground and object surfaces; ODE combines the
surface properties for the resulting contact response. Parameter meanings follow
[Gazebo physics parameters](https://classic.gazebosim.org/tutorials?tut=physics_params)
and [SDFormat contact specification](https://sdformat.org/spec/1.7/collision/);
the numeric settings are this project's initial choices.

Launch from the workspace root:

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-select racer_description
source install/local_setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
ros2 launch racer_description ground_contact.launch.py
```

Append gui:=false for headless testing, or contact_config:=/absolute/path/config.yaml
to select settings. The dedicated ROS domain and Gazebo master isolate this test
from existing preview/device sessions; use the same environment in another test
terminal. The entry point provides Gazebo visualization, /clock,
/contact_test/model_states, /contact_test/link_states and
/contact_test/get_entity_state. It publishes no vehicle TF, drive commands or
simulated Odin data. The state service is simulation truth, not estimator output.

Reproduce the drop check (--reset resets the entire simulation world; use it only
with the dedicated test world above):

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
python3 tools/validate_ground_contact.py --reset \
  --output data/generated/ground_contact_validation.json
python3 -m unittest discover -s tests -v
```

The checker observes 10 simulated seconds and evaluates the final 5 seconds:
height error <1 mm, vertical span <0.5 mm, horizontal drift <1 mm, speed <0.005 m/s,
angular speed <0.02 rad/s and orientation change from identity <0.5 degrees.
These are scene-specific engineering checks, not hardware performance metrics;
review the checks when changing geometry or release height.

Local validation, 2026-09-13, Gazebo 11.10.2 / ROS 2 Humble: SDF check, package
build and 11 unit tests passed. Released with base_link at 53.25 mm, observed for
10.036 s; settled height was about 33.1267 mm (nominal 33.25 mm). Settled maximum
speed was about 0.0000323 m/s, angular speed 0.0000541 rad/s and orientation angle
0.00460 degrees. A separate approximately one-second Gazebo contacts capture
contained 987 records for each of the four supports, with no other parts touching
the floor. Driven traction, turning, braking, real ground/ball behavior and hardware
equivalence with omitted masses remain unvalidated.

Commit preparation corrected CAD binary scanning and vendor directory boundaries,
and added the English gap-list counterpart. Full repository checks, builds and
unit tests pass; dynamic results retain the scope stated above.

## ros2_control vehicle motion simulation

The racer_bringup simulation.launch.py entry reuses the existing collision,
contact and inertia aggregation. The simulation URDF enables sim_control:=true
and declares velocity commands with position/velocity/effort feedback for both
wheel joints. GazeboSystem realizes velocity commands using a PI effort loop.
Only joint_state_broadcaster and diff_drive_controller are activated; no real F4
interface or line-following algorithm runs. The preview joint_state_publisher is
not started, so it cannot overwrite actual wheel feedback.

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-select racer_description racer_control racer_bringup
source install/local_setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
ros2 launch racer_bringup simulation.launch.py
```

Append gui:=false for headless use. Run this instead of the standalone contact
scene; only one server may use the same Gazebo master. In another terminal with
the same environment, confirm both controllers are active:

```bash
source /opt/ros/humble/setup.bash
source install/local_setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
ros2 control list_controllers -c /sim/racer/controller_manager
ros2 topic pub --use-sim-time -r 20 -t 60 \
  /sim/racer/diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  '{header: {stamp: now, frame_id: base_link}, twist: {linear: {x: 0.1}, angular: {z: 0.0}}}'
```

Command stamps must use /clock. When publishing ends, the controller times out
and brakes. The 0.25 s deadline starts timeout handling; physical stopping also
includes acceleration limiting and wheel-loop response. The timeout pauses with
simulation time and does not replace the independent F4 watchdog. Launch activates
simulation controllers but sends no nonzero velocity.

| Setting | Value / meaning |
| --- | --- |
| Control / odometry publication | 100 Hz / 50 Hz, simulation time |
| Wheel radius / nominal separation | Read from Xacro: 0.03325 m / 0.257 m |
| Effective separation multiplier | 1.10 for current simulated contacts only; effective separation 0.2827 m |
| Linear / angular speed limits | +/-0.2 m/s / +/-1.0 rad/s |
| Linear / angular acceleration limits | +/-0.3 m/s^2 / +/-1.5 rad/s^2 |
| Command age | TwistStamped, cmd_vel_timeout=0.25 s |
| Wheel velocity / effort limits | +/-12 rad/s / +/-0.1 N m, simulation initial values |
| Wheel PI | Kp=0.02, Ki=0.05, Kd=0; integral torque clamp +/-0.03 N m, antiwindup |
| Odometry | position_feedback=true, open_loop=false; wheel position feedback |

Controller settings are in [simulation_controllers.yaml](../src/odin_racer/racer_control/config/simulation_controllers.yaml),
actuator initial values in [sim_actuation.yaml](../src/odin_racer/racer_description/config/sim_actuation.yaml).
The generator injects geometry into temporary runtime YAML and rejects combined
linear/angular limits exceeding wheel velocity limits. Joint effort/velocity
limits are written to both URDF and SDF. Override controller settings with
controllers:=/absolute/path/file.yaml; restart after model/contact/config edits.

Effective separation evidence: with nominal separation and PI wheel feedback,
the ratio of wheel-derived yaw rate to Gazebo world yaw rate was approximately
1.101 in both in-place directions and an arc. This reflects contact/sliding of
the current wide cylinder tires. A 1.10 multiplier was then checked in a separate
run; CAD separation remains unchanged. This is simulator calibration, not measured
hardware geometry. Revalidate after changing tires, contact settings or ground.

| Interface | Publisher / meaning |
| --- | --- |
| /sim/racer/diff_drive_controller/cmd_vel | External test input, TwistStamped |
| /sim/racer/diff_drive_controller/cmd_vel_out | Limited command from controller |
| /sim/racer/diff_drive_controller/odom | Wheel-derived controller odometry |
| /sim/racer/joint_states | Actual simulated wheel states from joint_state_broadcaster |
| /sim/racer/tf, /sim/racer/tf_static | Controller owns odom to base_link; robot_state_publisher owns internal transforms |
| /contact_test/get_entity_state, /contact_test/link_states | Independent Gazebo truth for comparison, not an odometry input |

odom is a local planar reference initialized at startup; Gazebo world is the
physical world. No artificial world-to-odom transform is published. Odometry z=0
is not Gazebo ground height. Odin has moving geometry/TF only, without integrated
on-vehicle sensor generation.

```bash
# Same isolated ROS domain as the simulation; this actively moves the robot.
python3 tools/validate_sim_drive.py --output data/generated/sim_drive_validation.json
```

The validator runs forward, reverse, both in-place turns, an arc and excessive
commands. It compares wheel feedback and odometry against world truth, checking
zero-command stops, publisher silence, stale commands, limits, effort and TF
publishers; it sends zero on exit. Test speeds and thresholds assume the default
configuration. It does not reset the world; run without other command publishers.
Interface references: [gazebo_ros2_control](https://control.ros.org/humble/doc/gazebo_ros2_control/doc/index.html),
[diff_drive_controller](https://control.ros.org/humble/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html).

Motion validation (2026-09-13, Gazebo 11.10.2 / ROS 2 Humble): the initial configured
run and subsequent repeat passed. Final repeat forward/reverse speeds were about
+0.1000/-0.1000 m/s; left/right turns +0.4998/-0.5057 rad/s; arc 0.1002 m/s and
0.4983 rad/s. Excessive input was limited to 0.2 m/s and 1 rad/s. After publisher
silence, observed braking began at about 0.30 s and the stop threshold was reached
at 0.60 s, after about 44.9 mm additional travel. Zero-command stops took about
0.4-0.9 s across scenarios. Stop thresholds are |v|<0.005 m/s, |w|<0.02 rad/s,
and near-zero limited commands. Across six stages, maximum odometry displacement
increment error was about 11.3 mm and yaw increment error about 0.0079 rad.
Displacement comparison uses world/odom axes separately, so accumulated heading
drift also contributes. Speed, acceleration, effort, stale-command, height and
TF checks passed; 14 unit tests passed. This demonstrates basic planar motion,
not competition line following or real motor performance. The script produces full metrics.
