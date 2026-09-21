# Architecture and tracking design

English | [Chinese](02_architecture_cn.md)

Reviewed against the repository on 2026-09-21. [Package implementation status](../src/README.md) is distinct from the hardware target below.

## Current simulation pipeline

```text
FishPoly image + CameraInfo + acquisition-time TF
    -> line_perception -> LineObservation + ground black_mask
wheel odometry + ordered CSV route + observations
    -> lap_controller -> TwistStamped -> diff_drive_controller -> wheel PI / Gazebo
Gazebo truth -> independent Python evaluator (no feedback to control)
```

`line_perception` projects images onto a flat metric grid and extracts black-line geometry. `lap_controller` aligns visible skeleton points against the full mapped route to correct the odom-to-route transform. It constrains driving projection to a local, monotonically advancing progress window to distinguish repeated crossing visits. Map alignment currently lives inside the controller; it is not a standalone localization node or a published `map -> odom` TF.

Pure Pursuit uses a forward target, curvature-based speed limiting and command slew limits. Healthy images and odometry must remain fresh; travel without successful visual alignment is limited to 0.65 m of route progress. The ordered route comes from image reconstruction, not a surveyed course. Exact limits and startup are documented in [competition lap](../simulation/COMPETITION_LAP.md).

`line_controller` is a separate local-vision baseline. It retains observed geometry in odom and can stop/turn/reacquire at individual corners; it has no full-course route. Use one controller per command output. See [local tracking](../simulation/LINE_FOLLOWING.md).

## Hardware target and ownership

| Component | Responsibility still to integrate on hardware |
| --- | --- |
| `racer_odin` | Vendor adaptation, image calibration, timestamps and device health |
| `racer_hardware` / F4 | Communication and measured wheel states / wheel-speed feedback and independent watchdog |
| `racer_localization` | Continuous local state, reset semantics and TF ownership |
| `racer_trajectory` | Ordered route metadata and predictive acceleration/braking constraints |
| `racer_control` / bringup | Final command selection, readiness and deployment |
| `racer_evaluation` | Synchronized real-vehicle recording and independent route association |

F4 receives bounded wheel-speed targets in rad/s and returns measured wheel feedback. A single upper-level command selector owns the final drive output. Teleoperation, racing and optional Nav2 must not compete on that output. F4 must stop independently if the host freezes, and boot disabled. These hardware components are not implemented merely because their packages build.

## Coordinates, timing and state

Use SI units, body x forward/y left/z up and optical x right/y down/z forward. `base_link` is the rear axle midpoint in the current model. The scoring reference point remains unconfirmed.

```text
map -> odom -> base_link -> wheels / odin_link -> sensor frames
```

This is the target tree. In simulation the differential drive controller owns `odom -> base_link`; `robot_state_publisher` owns internal transforms on `/sim/racer/tf` and `/sim/racer/tf_static`. No global map/world alignment TF is published. Each hardware TF edge must also have one owner; audit vendor broadcasts before adding an estimator.

Align data at acquisition timestamps and use monotonic time for host watchdogs. Never re-stamp stale observations as new. ODIN pose may already incorporate its IMU; do not fuse correlated pose/IMU as independent measurements without a model. Simulation control ticks at 50 Hz; target-platform rates and end-to-end delays require measurement.

Lap states: `DISARMED -> READY -> RUNNING -> FINISHED`; faults latch `STOPPED`. Healthy data alone does not restart motion; explicit re-enable is required. A fresh full lap requires restarting the simulation to reset progress and initial pose. Hardware calibration checks and mode arbitration remain planned.

## Design decisions and next algorithm work

| Decision | Status / reason |
| --- | --- |
| ADR-0001, 2026-09-10: Humble baseline | Workstation baseline; Jetson image, firmware and ARM64 compatibility must be verified before platform lock |
| ADR-0002, 2026-09-10: ordered route plus visual feedback | Selected; mapping/pre-recording/cameras are allowed by the owner; shortest-path navigation must not skip prescribed branches |
| ADR-0003, 2026-09-10: first-party workspace plus vendor underlay | Adopted; vendor versions and licenses remain separately recorded |

The former standalone ADR pages are consolidated here; decision identities and status are retained. Future changes should record the superseding decision and evidence.

Next speed planning can propagate acceleration/braking bounds along the route:

```text
v_curve <= sqrt(a_lateral_max / abs(kappa))
v_yaw <= omega_max / abs(kappa)
v_next^2 <= v_current^2 + 2*a_accel*ds
v_current^2 <= v_next^2 + 2*a_brake*ds
d_stop >= v*total_latency + v^2/(2*a_brake) + margin
```

These predictive limits are proposals, not calibrated hardware capabilities. Check wheel saturation, available view and full-body swept clearance, and guard zero curvature. A moving robot with bounded angular velocity cannot track a mathematical sharp corner exactly; permissible error and stopping rules must determine the feasible maneuver. [Requirements](01_requirements.md) and [evaluation](08_evaluation.md) define the remaining decisions and measurement principles.
