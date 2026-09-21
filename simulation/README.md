# Simulation entry points

English | [Chinese](README_cn.md)

Current backend: Gazebo Classic 11 / ROS 2 Humble on the workstation. The default competition map is 4×3 m. [Model assumptions](MODEL.md) and [recorded validation](../experiments/README.md) are maintained separately from commands.

## Choose an entry point

| Purpose | Entry / guide |
| --- | --- |
| Continuous full lap | [competition_lap.launch.py guide](COMPETITION_LAP.md) |
| Local visual tracking and corner experiments | [line_following.launch.py guide](LINE_FOLLOWING.md) |
| Competition texture, scale and projection check | [Course world](COMPETITION_COURSE.md) |
| FishPoly projection and camera tests | [Camera model](FISHPOLY_CAMERA.md) |
| Base drive, sensor targets or drop test | Commands below |

Build once using [development](../docs/07_development.md). In every test terminal:

```bash
source /opt/ros/humble/setup.bash
source install/local_setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
```

Use an unused ROS domain/master pair and one world at a time. `gui:=false` hides the window; camera rendering still needs a usable DISPLAY. Sensor consumers use `use_sim_time=true`; the two control nodes must not publish competing commands.

## Base motion

```bash
ros2 launch racer_bringup simulation.launch.py
```

This activates the wheel-state broadcaster and differential drive controller without automatically sending motion commands. In a second terminal with the same environment, the following test actively moves the simulated vehicle:

```bash
ros2 control list_controllers -c /sim/racer/controller_manager
python3 tools/validate_sim_drive.py --output data/generated/sim_drive_validation.json
```

The validator checks forward/reverse, both rotations, arc, saturation, zero command, stale command and stream loss against wheel feedback and independent truth. It sends zero at exit; run without other command publishers. For a camera-free base test use `sensors:=false`.

## Onboard sensor targets

Start a new world for each sensor validation:

```bash
ros2 launch racer_bringup simulation.launch.py gui:=false sensor_targets:=true
```

In the matching second terminal:

```bash
python3 tools/validate_sim_sensors.py --output data/generated/sim_sensors_validation.json
```

The validator actively moves the robot. It checks parked FishPoly target boundaries (8 px), cloud target/ground P95 distances (20/10 mm), IMU response, TF and message freshness/frequency. LinkStates has no acquisition timestamp; motion comparisons are basic response checks, not precision timing calibration. These target tests use the empty course, not `course:=competition`.

## Ground contact

```bash
ros2 launch racer_description ground_contact.launch.py gui:=false
```

Then, only in this isolated drop-test world:

```bash
python3 tools/validate_ground_contact.py --reset --output data/generated/ground_contact_validation.json
```

`--reset` resets the entire test world. This scene has gravity and passive wheels but no drive commands, vehicle TF or Odin outputs. It uses the existing 0.877 kg mass subtotal and 25 collisions. The validator observes 10 simulation seconds and checks the last 5 seconds for height error <1 mm, vertical variation <0.5 mm, horizontal drift <1 mm, speed <0.005 m/s, angular speed <0.02 rad/s and attitude deviation <0.5°. `contact_config:=/absolute/path/config.yaml` replaces contact settings.

## Independent Odin bench

```bash
ros2 launch racer_description odin_sensors.launch.py gui:=false
```

The fixed bench mounts the device at 0.5 m above ground with a target 2 m ahead; it is not the vehicle installation. Stop competing preview/bench TF publishers. Messages are under `/sim/odin1/` rather than `/sim/racer/odin1/`. The world file is a generated-scene template, not a complete standalone sensor world.

## Vehicle interfaces and options

| Interface | Meaning |
| --- | --- |
| `/sim/racer/diff_drive_controller/cmd_vel` | `TwistStamped` input; use `/clock` timestamps |
| `/sim/racer/diff_drive_controller/cmd_vel_out` | Limited command |
| `/sim/racer/diff_drive_controller/odom` | Wheel-position-feedback odometry |
| `/sim/racer/joint_states` | Actual simulated joint states |
| `/sim/racer/tf`, `/sim/racer/tf_static` | Local odometry and robot transforms |
| `/sim/racer/odin1/image`, `camera_info` | FishPoly image and same-frame calibration |
| `/sim/racer/odin1/cloud_raw`, `imu` | Ray cloud and ideal IMU |
| `/contact_test/link_states`, `get_entity_state` | Evaluation-only Gazebo truth |

Remap consumer `/tf` and `/tf_static` to the vehicle namespaces. For RViz image display use Reliable/Volatile, depth 5; cloud/IMU use sensor-data QoS. Local-vision launches configure lockstep and enlarged DDS shared memory; details are in [local tracking](LINE_FOLLOWING.md).

`controllers:=...`, `sensor_config:=...` and `contact_config:=...` select configuration files; restart after changes. `sensor_targets` defaults false and cannot be combined with the competition course. `course_overview:=true` adds an evaluation-only overhead camera in the competition world. Configuration/physical limits are listed once in [model scope](MODEL.md).
