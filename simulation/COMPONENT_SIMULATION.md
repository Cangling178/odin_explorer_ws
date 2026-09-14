# Component simulation scope and hardware differences

English | [Chinese](COMPONENT_SIMULATION_cn.md)

Status date: 2026-09-13. Applies to the current Gazebo Classic 11 / ROS 2 Humble
vehicle motion scene with onboard Odin sensors enabled by default. This document
describes modeled behavior, approximations and missing hardware effects by component.
Commands and acceptance data are in the [simulation guide](README.md), gap priorities
in the [model gap list](MODEL_GAPS_TEMP.md), and engineering tasks remain in the
[project plan](../docs/planning/README.md).

The implementation combines simplified vehicle dynamics, onboard sensor output and
base velocity control. Appearance, collisions, dynamics and data output are distinct:
CAD appearance does not imply exact collisions, and mass/inertia do not establish a
complete motor or electronics model. Without complete hardware comparisons, omissions
can be identified but a percentage difference from hardware cannot be claimed.

## 1. Mechanical structure

| Component | Currently modeled | Main differences from hardware |
| --- | --- | --- |
| Chassis plate | CAD appearance, placement and simplified collision envelopes | Mass omitted; boxes fill some holes/gaps; no plate deformation |
| Two rear drive wheels | Diameter 66.5 mm, width 26 mm, nominal separation 257 mm; rotating joints, mass, inertia and ground friction | Rigid cylinders without rubber deformation, tread detail or measured rolling resistance |
| Two front ball transfers | Ball/housing appearance, assembly mass and ground support | Balls are fixed to the body and use low-friction sliding to approximate rolling; no ball rotation, internal bearings or real rolling resistance |
| Motor brackets | Simplified L shapes, collisions, mass and approximate inertia | Some dimensions are assumptions; no joint clearance, looseness or elasticity |
| Standoffs | Hexagonal appearance, cylindrical collision approximation and placement | The 42 mm length is derived; mass, threads and nuts are omitted |
| Output shafts and hub attachment | Shafts rotate with wheels, with simplified appearance and collisions | Rigid attachment without bearing resistance, looseness or backlash; shaft mass is not counted twice |
| Odin housing and mount | CAD appearance, collision envelope, 280 g mass and approximate inertia | Mount height/orientation include assumptions; no bracket vibration, mounting compliance or thermal behavior; physical assembly clearances are unaccepted |

Sources: [vehicle Xacro](../src/odin_racer/racer_description/urdf/robot.urdf.xacro),
[motor assembly](../src/odin_racer/racer_description/urdf/motor_assembly.xacro),
[Odin assembly](../src/odin_racer/racer_description/urdf/odin1.xacro).

## 2. Mass, inertia and rigid bodies

| Included components | Mass subtotal |
| --- | ---: |
| Two motor assemblies | 340 g |
| Two motor brackets | 94 g |
| Two tire/hub assemblies | 92 g |
| Two ball-transfer assemblies | 71 g |
| Odin1 | 280 g |
| Total | **877 g** |

These are adopted reference values, not a complete weighed vehicle. The 877 g total
is a subtotal of included components. Plate, standoff, battery, Jetson, F4 and driver
board masses remain deferred under the current agreement; extra fasteners are omitted.
Centers of mass and inertias use uniform boxes/cylinders, not measured tensors.
Motor internal rotating inertia is not modeled separately.

The [contact generator](../src/odin_racer/racer_description/racer_description/contact_world.py)
aggregates fixed parts into a 0.785 kg body and two 0.046 kg wheels: three dynamic bodies
retaining 25 collisions. Aggregation includes tensor rotation and parallel-axis terms
without double counting; the source URDF retains its part-level TF tree. Connections
have no flexibility or looseness, and self-collision is disabled. This does not establish
precision assembly interference or structural vibration acceptance.

## 3. Motors, gearboxes and encoders

| Item | Current implementation | Main differences from hardware |
| --- | --- | --- |
| Motor appearance and mass | Simplified shapes/collisions, 170 g per assembly | Some dimensions are assumptions; inertia uses a uniform bounding box |
| Drive force | PI feedback compares target and simulated wheel speed and applies joint torque | No voltage, current, back EMF, PWM, starting deadband or thermal model |
| Gearbox | Housing geometry; output shaft rotates with the wheel | No internal 1:28 gearing, efficiency loss, backlash or internal rotating inertia |
| Encoder | Gazebo joint positions and velocities directly supply wheel states | No GMR pulses, count quantization, wraparound, missed counts or device sampling delay; the relation between 500 lines and counts per wheel revolution remains unconfirmed |
| Actuator limits | Wheel speed +/-12 rad/s and effort +/-0.1 N m | Simulation initial values, not confirmed motor ratings or performance limits |
| Stopping | Zero targets or command timeout decelerate through the drive controller and wheel loop | Real driver-board brake/coast modes and power-loss behavior are absent |

The wheel loop uses Kp=0.02, Ki=0.05, Kd=0, an integral torque clamp of +/-0.03 N m,
and antiwindup. Motion is computed through torque, inertia and contact rather than
direct body-position changes. Acceleration, turning and braking have not been matched
to the physical MG513X motors and drivers and cannot establish hardware performance.
See [sim_actuation.yaml](../src/odin_racer/racer_description/config/sim_actuation.yaml).

## 4. Odin1 sensors and internal functions

| Sensor or function | Current simulation | Main differences from the device |
| --- | --- | --- |
| RGB camera | 1600x1296, 10 Hz, 129-degree horizontal FOV; onboard rendered images and CameraInfo | Pinhole model versus the device's FishPoly calibration; vertical FOV follows aspect ratio; no real lens projection, exposure response, motion blur or image noise |
| Depth/cloud | 240x180 rays, 120x90-degree FOV, 0.2-30 m, 10 Hz; collision intersections exported as PointCloud2 | Ray intersection approximates DTOF; no reflectivity/light effects, range noise, multipath, confidence, offset_time or condition-dependent long-range detection |
| IMU | About 400 Hz onboard angular velocity and acceleration, including stationary gravity response | Ideal, without noise, bias drift or thermal drift; 400 Hz is a simulation choice, not a verified device sampling/send rate |
| Sensor extrinsics | Composed from the Xacro fixed-joint chain; camera relative extrinsics use converted values from the device calibration copy | Housing-to-lidar uses a CAD lens-center estimate; body installation is not measured calibration |
| Internal Odin SLAM | Not simulated | No vendor fused pose, cloud_slam, mapping, relocalization or map saving |

Camera/cloud rates are about 10 Hz and IMU about 400 Hz in simulation time. Bench and
vehicle share [odin_sensors.yaml](../src/odin_racer/racer_description/config/odin_sensors.yaml),
with sensors generated by [sensor_world.py](../src/odin_racer/racer_description/racer_description/sensor_world.py).

Keeping [calib_device.yaml](../hardware/mechanical/odin1/calib_device.yaml) does not mean
Gazebo renders FishPoly images. Only converted relative extrinsics are reused; images
and CameraInfo still describe a simulated pinhole camera. Cloud `resolution_m: 0.001`
is a ray range-resolution setting, not a claim of 1 mm device measurement accuracy.

The camera observes visual geometry while rays intersect collision geometry. The red
test box has both and can be observed by both sensors. The blue ground marker is
visual-only: the camera sees it while the cloud returns the ground underneath.
Simplified collision envelopes therefore affect simulated cloud shapes.

## 5. Ground, electronics and control interfaces

| Part | Current simulation | Missing hardware effects |
| --- | --- | --- |
| Ground contact | Gravity, contact stiffness/damping, friction, settling and sliding | Default flat ground; no measured unevenness, material variation or calibrated tire-contact model |
| Competition course | 2.00 x 1.50 m black/white board reconstructed from the drawing, including bends and crossing; camera-visible line | Image-estimated width about 21 mm, not surveyed; visual-only line with flat cloud returns; no official start/finish, route order or penalties |
| Turning and slip | Contact-based motion with a 1.10 effective-separation correction | Correction applies only to this model, not hardware geometry; real slip trends have not been compared |
| F4 | The simulated wheel PI loop approximates some execution functions | No F4 firmware, timers, protocol parsing, hardware faults or independent watchdog simulation |
| Jetson | ROS nodes run on the development computer | No Jetson compute, scheduling, power or thermal-throttling model; perception and autonomous tracking nodes remain unimplemented |
| Communication and time | ROS topics, simulation time and a 0.25 s command timeout | No physical serial/CAN delays, packet loss or device clock offsets; timeout time also pauses with simulation |
| Battery and driver board | No electrical model | No battery voltage change, voltage sag, driver efficiency, current limiting or undervoltage behavior |
| Localization output | Differential drive controller computes odometry from wheel positions | No wheel/ODIN1 fused localization; Gazebo truth is only an independent validation input |

Initial friction coefficients are tire 0.8, front ball 0.02, other parts 0.5 and
ground 1.0, all uncalibrated. See
[ground_contact.yaml](../src/odin_racer/racer_description/config/ground_contact.yaml).
Having friction does not establish hardware slip fidelity, and `slip1/slip2=0` does
not establish that tires cannot slide.

Body command limits are +/-0.2 m/s and +/-1 rad/s, acceleration limits +/-0.3 m/s^2
and +/-1.5 rad/s^2, controller rate 100 Hz and odometry rate 50 Hz. These come from
[simulation_controllers.yaml](../src/odin_racer/racer_control/config/simulation_controllers.yaml)
for current simulation validation, not measured hardware limits. The 0.25 s value
is a command timeout, not the complete physical stopping time.

## 6. Verified capabilities and applicability

Settling, basic straight/turn/arc motion, limits and stopping, and basic onboard
image/cloud/IMU geometry and motion response have passed validation. Full commands,
thresholds, historical metrics and local report locations are in the [simulation guide](README.md).

The [competition drawing scene](COMPETITION_COURSE.md) passes initial-straight overhead/onboard
projection and short forward-motion checks. Line recognition and autonomous full-course tracking
remain absent. With the overview camera enabled, this run received about 333 Hz IMU and 10 Hz
image/cloud output; 400 Hz in configuration is a target, so use the actual run report.

Current checks support model placement, basic motion interfaces, sensor transforms
and known-target observations as a foundation for algorithm integration. They do
not establish hardware lap times, braking distance, positioning accuracy, perception
under complex lighting or complete-course feasibility. The last onboard sensor
acceptance run measured a real-time factor of about 0.62 for that development computer
and rendering/subscription load; it does not represent Jetson performance.

Update the relevant entries when components or models change. Record errors, data
sources and operating conditions after hardware comparisons become available.
