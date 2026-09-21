# Simulation model and hardware gaps

English | [Chinese](MODEL_cn.md)

Reviewed 2026-09-21 against the current model and configuration. This replaces the component comparison and temporary model-gap checklist. Commands are in [simulation](README.md); priorities in [planning](../docs/planning/README.md).

## Geometry and dynamics

| Item | Current model | Remaining difference |
| --- | --- | --- |
| Chassis / ODIN | Source CAD visuals, conservative primitive collisions | No flex or precision interference assessment; installation not measured |
| Rear wheels | 66.5 mm diameter, 26 mm width, 257 mm nominal spacing | Rigid cylinders; no measured tire deformation or rolling resistance |
| Front supports | Fixed CY-15A-like ball/housing geometry | Low-friction sliding instead of ball rotation/bearing behavior |
| Motors / supports | Simplified MG513X geometry and estimated inertia | No gearbox backlash, internal rotor inertia or compliance |
| Standoffs | 4.5 mm hex width, derived 42 mm length | No threads; mounting flange omitted; 38.3 mm CAD vs 40 mm product hole spacing |
| ODIN mounting | Forward-facing, plate-mounted assumption | Hole spacing mismatch, visibility and cooling clearance unresolved |

[Chassis dimensions](../hardware/mechanical/chassis_plate/README.md) and [ODIN source/install](../hardware/mechanical/odin1/README.md) retain provenance. Source URDF contains 25 primitive collision shapes over 16 visual/entity links. Chassis holes/gaps are conservatively filled; internal overlaps are allowed and self-collision is disabled.

Included reference masses: motors 340 g, brackets 94 g, wheels/hubs 92 g, passive-support assemblies 71 g, ODIN 280 g: **877 g subtotal, not total vehicle mass**. The plate, standoffs, battery, Jetson, F4 and driver masses remain deferred. Inertia uses uniform boxes/cylinders, not measurements. Fixed-joint merging produces a 0.785 kg body and two 0.046 kg wheels; rotation and parallel-axis terms preserve mass/inertia without duplicating fixed parts.

## Ground contact and actuation

[ground_contact.yaml](../src/odin_racer/racer_description/config/ground_contact.yaml) holds uncalibrated initial values: rear/front/other/ground friction 0.8/0.02/0.5/1.0, kp 100000 N/m, kd 100 N·s/m, min_depth 0.1 mm, correction max_vel 0.1 m/s, ODE step 1 ms and 80 iterations. Contact correction velocity is not a vehicle speed limit. Friction settings do not imply zero slip.

[sim_actuation.yaml](../src/odin_racer/racer_description/config/sim_actuation.yaml) applies wheel PI torque feedback: Kp=0.02, Ki=0.05, integral torque ±0.03 N·m, total torque ±0.1 N·m, wheel speed ±12 rad/s. No voltage/current/PWM/dead-zone/thermal or encoder-quantization model is provided.

[simulation_controllers.yaml](../src/odin_racer/racer_control/config/simulation_controllers.yaml): control 100 Hz, odometry 50 Hz; body limits ±0.2 m/s, ±1 rad/s and ±0.3 m/s², ±1.5 rad/s². Wheel radius is 0.03325 m. A 1.10 effective-separation multiplier compensates this simulation contact model (0.2827 m effective spacing), not real geometry. Wheel feedback comes from simulated joint position, not commanded velocity or world truth.

The 0.25 s command timeout starts braking, not instant physical rest, and pauses with simulation time. The F4 watchdog, host transport delays, power and electrical stop behavior are absent. Real hardware requires independent validation.

## Sensors and course

| Item | Current implementation | Omitted / unverified |
| --- | --- | --- |
| RGB | Device O1-P040100136 FishPoly geometry, 1600×1296 at 10 Hz | Exposure, blur, noise, compression and real-device timing |
| Point cloud | 240×180 rays, 120°×90°, 0.2–30 m at 10 Hz | DTOF material/light behavior, noise, confidence and offset_time |
| IMU | Ideal acceleration/angular rate, configured 400 Hz | Bias, noise, thermal drift; actual hardware output frequency |
| Extrinsics | Xacro fixed chain, device camera calibration conversion | Housing-to-LiDAR uses CAD lens-center approximation; vehicle mount uncalibrated |
| Vendor localization | Not simulated | SLAM, cloud_slam, relocalization and map services |
| Course | Image-derived 4×3 m default, approx. 21.2 mm lines | Physical survey, official order, illumination and dirt variation |

Shared settings: [odin_sensors.yaml](../src/odin_racer/racer_description/config/odin_sensors.yaml). Camera projection and custom CameraInfo are defined in [FishPoly](FISHPOLY_CAMERA.md); cloud `resolution_m=0.001` is a setting, not 1 mm hardware accuracy. Cameras render visuals while ray clouds intersect collisions, so flat black ink is not a line-shaped LiDAR return. Simulated frames use `odin_sim_*` and must not be adopted as hardware calibration.

Physics, sensors and ordered-route tracking have simulation evidence in [validation](../experiments/README.md). Measured frame rates and real-time factor depend on the recorded workload; 400 Hz IMU is a target, not a guarantee. No current result establishes real-vehicle accuracy, stopping distance, tight-turn clearance or Jetson throughput. Calibrate the dominant errors from actual images and motion before adding cosmetic model detail.
