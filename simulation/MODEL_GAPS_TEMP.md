# Simulation model gaps (temporary)

English | [Chinese](MODEL_GAPS_TEMP_cn.md)

This is a code-state snapshot, not hardware acceptance. Work proceeds from stable
ground contact and motion to perception integration and then hardware fidelity.
Update, 2026-09-13: contact and ros2_control motion checks pass; moving sensors are next.

## Completed

- CAD plate and Odin1 meshes; user-provided wheel dimensions and documented motor/bracket approximations.
- Assigned mass: motors 340 g, brackets 94 g, tires/hubs 92 g, ball assemblies 71 g,
  Odin1 280 g. The **877 g subtotal is not the complete vehicle mass**.
- Uniform-geometry inertia estimates, not measured tensors.
- 25 primitive collisions on 16 visual links, all retained in the dynamic model.
- RViz preview of the assembly and sensor frames.
- Standalone Odin image, CameraInfo, cloud and stationary IMU checks.
- Drop/settling, forward/reverse, turns, arc, limits and stops checked; moving sensor generation is pending.

## 1. Existing inertias defined; unknown masses deferred

Scope confirmed on 2026-09-13: do not add unknown plate, standoff, battery, Jetson,
F4 or driver-board masses or invent their inertias. Extra fasteners remain omitted.
Nine links have mass, COM and tensors: boxes for motors/brackets/Odin, Y-axis solid
cylinders for wheels and Z-axis cylinders for complete ball-transfer assemblies.
Motor mass is lumped into its fixed housing; shafts are not counted again and
internal rotating inertia is not separately represented.

Xacro expansion, finite COM/tensors, positive masses/principal moments and triangle
inequalities pass. Mass remains 0.877 kg. These checks do not establish measured inertia.
contact_world.py aggregates fixed groups with frame rotation and parallel-axis
terms into a 0.785 kg body and two 0.046 kg wheels, preserving massless-part geometry.
The source URDF TF tree is unchanged; simulation uses generated SDF. Mass,
aggregation and geometry-transform tests pass. Dynamics represent this partial model.

## 2. Ground contact configured and drop checked

All 25 collisions survive generation. Initial friction coefficients are tire 0.8,
ball 0.02, other parts 0.5 and ground 1.0. Fixed balls approximate low-friction
sliding supports, not rotating balls. Initial contact kp=100000 N/m, kd=100 N s/m,
min_depth=0.1 mm and max_vel=0.1 m/s; ODE uses 1 ms steps and 80 iterations.
These are engineering choices, not measurements.

A 20 mm clearance drop observed for 10.036 simulated seconds passed settling checks
over the final five seconds. base_link settled at about 33.1267 mm versus nominal
33.25 mm, without sustained sinking or obvious drift. A separate approximately
one-second capture contained 987 contact records per support, with only both tires
and both balls touching. SDF check, build and the then-current 11 tests passed.
See [contact reproduction](README.md#chassis-ground-contact-test).

Driven checks now pass under item 3, but contact/slip/braking are not calibrated
against hardware. Conservative plate envelopes fill gaps and cannot validate
precise assembly. Real ball rolling dynamics remain absent. Calibrate contact
parameters against actual ground and vehicle response later.

## 3. ros2_control basic motion integrated

racer_bringup/simulation.launch.py loads GazeboSystem, joint_state_broadcaster and
diff_drive_controller on the existing three-body model. Rear wheels expose velocity
commands and position/velocity/effort feedback; a bounded PI loop applies torque.
Interfaces use /sim/racer. The controller publishes wheel odometry and odom to
base_link; robot_state_publisher owns internal TF. Gazebo truth is only a comparator.

Control is 100 Hz, odometry 50 Hz. Limits are +/-0.2 m/s and +/-1 rad/s, acceleration
+/-0.3 m/s^2 and +/-1.5 rad/s^2, command timeout 0.25 s, wheel speed +/-12 rad/s
and effort +/-0.1 N m. Geometry comes from Xacro; total mass stays 0.877 kg.
The 1.10 effective-separation correction was fitted to current simulated contacts;
CAD separation remains unchanged and the correction is not hardware calibration.

Validation, 2026-09-13: controllers active; forward, reverse, both in-place turns,
arc and excessive-input stages pass, as do speed/acceleration/effort limits,
stale commands, publisher silence, zero-command stops, feedback and TF checks.
Repeated straight speed was about 0.1000 m/s; turns about +0.4998/-0.5057 rad/s.
After 0.1 m/s command silence, sampled braking began around 0.30 s and reached
the stopping threshold around 0.60 s after about 44.9 mm additional travel.
The timeout is not the complete stopping time. Maximum stage odometry displacement
increment error was about 11.3 mm and yaw increment error about 0.0079 rad.
These are planar simulation results, not hardware positioning accuracy.

F4 communication, race arbitration, line tracking and on-vehicle sensors remain
unimplemented. PI, effort, contact and effective separation are simulation estimates;
simulation-time timeout does not replace an independent lower-controller watchdog.
See [motion guide](README.md#ros2_control-vehicle-motion-simulation) and
[validator](../tools/validate_sim_drive.py).

## 4. High priority: moving sensor integration pending

The vehicle has odin_sim_* frames, but data comes from a separate fixed sensor at
0.5 m, not the actual front mounting height. Standalone bench and preview can
publish duplicate sensor TF. Integrate sensor generation with the vehicle and share
geometry, /clock, use_sim_time, topic/QoS conventions and TF ownership. Verify
image/cloud/IMU response under translation and rotation without duplicate TF.

## 5. High priority: Odin installation, extrinsics and view unaccepted

Forward-facing, flush mounting is assumed. Official 84.3 x 30.7 mm holes differ
from plate 84 x 30.3 mm. Housing-to-lidar uses a CAD lens-center estimate, not a
calibrated optical center; camera relative extrinsics use a local device copy.
Check actual bracket height/pitch, ground-line coverage, self-occlusion, cooling
clearance and raised-installation guidance. Validate known ground-point projection
and cloud direction; simulation TF is not hardware calibration.

## 6. High priority: camera and localization differ from hardware

The 1600 x 1296, 129-degree horizontal-FOV camera is pinhole, not FishPoly. Aspect
ratio determines vertical FOV, so official 104 degrees is not simultaneously matched.
There is no vendor SLAM, cloud_slam, relocalization or map service. Choose a rectified
pinhole algorithm input or implement a closer projection. Add SLAM if required, or
explicitly labeled truth; never present truth as vendor estimation. Projection and
CameraInfo must agree, and localization source/error/time semantics must be explicit.

## 7. Medium priority: noise, latency and actuation uncalibrated

Angular ray clouds omit DTOF reflectivity/light behavior, confidence and offset_time.
IMU is ideal; 400 Hz is a simulation setting, not verified hardware sampling.
Encoder counting, communication latency, motor deadband and full saturation behavior
are absent; the relationship of 500 lines to wheel counts needs firmware confirmation.
Record stationary, straight, turning and acceleration data to calibrate noise and
response. Acceptance requires reproducing major hardware error trends.

## 8. Medium priority: track, closed loop and evaluation missing

There are sensor and planar contact scenes, but no complete black-line track,
crossings, lighting or occlusion suite. Perception-control closure, frame-loss
recovery, end-to-end latency and real-time performance are unverified. Build straight,
curve and crossing cases; record repeatable tracking error, success rate, stop
distance and real-time factor, then disturbances/faults. Results should distinguish
geometry, perception and control failures.

## 9. Lower priority: mechanical details simplified

Gearbox/cover thickness, wheel gap and L bracket include documented assumptions.
Ball flanges are absent; 42 mm pillars are derived. Product 40 mm ball-mount spacing
differs from CAD 38.3 mm; the model follows CAD by user instruction. These usually
matter less unless contact, mass distribution, assembly or visibility is affected.
The model is not a fabrication drawing. Refine from drawings/measurements later;
screws are not a prerequisite.

## Suggested order

1. Existing 877 g aggregation and drop checks complete; unknown masses deferred.
2. ros2_control straight, turning and stopping checks complete.
3. Integrate moving sensors, mounting/projection checks and algorithm closure (4-6).
4. Calibrate against hardware and establish track evaluation (7-8).
5. Refine appearance as needed (9).

Basic motion simulation is usable. Hardware equivalence requires subsequent comparison.

## Code and records

- [Chassis Xacro](../src/odin_racer/racer_description/urdf/robot.urdf.xacro)
- [Motor assembly](../src/odin_racer/racer_description/urdf/motor_assembly.xacro)
- [Odin assembly](../src/odin_racer/racer_description/urdf/odin1.xacro)
- [Contact generator](../src/odin_racer/racer_description/racer_description/contact_world.py)
- [Contact settings](../src/odin_racer/racer_description/config/ground_contact.yaml)
- [Drop validator](../tools/validate_ground_contact.py)
- [Sensor world](../src/odin_racer/racer_description/worlds/odin_sensors.world)
- [Mechanical record](../hardware/mechanical/chassis_plate/README.md)
- [Odin mounting](../hardware/mechanical/odin1/README.md)
- [Simulation guide](README.md)
