# Hardware bringup and calibration

English | [Chinese](09_bringup_cn.md)

As of the 2026-09-21 repository review, simulation tracking works, but the host hardware adapters, F4 communication, real wheel odometry and race startup remain unfinished. Vendor-driver workstation build and point-cloud display are the only recorded device bringup progress; see [vendor record](../vendor_ws/README.md).

## 1. Confirm hardware and rules

Fill [BOM](../hardware/bom.csv), [robot specification](../hardware/robot_spec.template.yaml) and [platform lock](../hardware/platform_lock.template.yaml). Mechanical records already identify MG513X GMR 500-line, 1:28 reference motors; voltage/current ratings, encoder counting interpretation, actual board, driver and transport still require verification. The word F4 alone does not identify pin assignments or a toolchain.

Confirm the carrier, RAM, JetPack/OS, device firmware, USB link and power wiring. Record battery, regulators, fuse, stop circuit, common grounds and cable restraint; verify ratings against actual boards. Measure loaded voltage drop, temperature and disconnects. Confirm course dimensions, direction, crossing order, scoring point and tolerances in [requirements](01_requirements.md).

## 2. Wheel-control bench

With wheels clear of the ground, verify directions, measured encoder counts, bounded wheel-speed commands and feedback. Implement and test the [F4 protocol](../firmware/README.md): malformed/stale/repeated packets, reconnect, reset, saturation and watchdog. Removing communication or restarting the host must stop the motors and require deliberate re-enable. Record physical stop latency and distance separately from the timeout setting.

## 3. ODIN images and stationary projection

Load the reviewed vendor version and inspect actual topics, types, frames, QoS and acquisition timestamps. Capture straight lines, tight turns and crossings at the intended installation and lighting; measure near/far ground coverage, black-line pixel width, exposure and processing delay.

The repository's 2026-09-16 vendor-source inspection found `odin1/image` but no matching CameraInfo publisher. Recheck the installed driver during integration. Current `line_perception` requires matching image/CameraInfo timestamps and dimensions, the custom `fishpoly` model and acquisition-time TF. `racer_odin` must provide correctly matched calibration while retaining acquisition time; distinguish raw and rectified images. [FishPoly convention](../simulation/FISHPOLY_CAMERA.md) is not interchangeable with OpenCV fisheye coefficients.

Measure `base_link -> ODIN1`, mounting height/pitch and ground plane. Existing [device calibration](../hardware/mechanical/odin1/calib_device.yaml) is not vehicle installation calibration. Verify known ground points and self-occlusion before moving. If visibility fails, fix installation/calibration or evaluate another permitted ordinary camera. Dedicated line-sensor modules remain outside scope.

## 4. Motion calibration and simple tracking

Measure loaded rolling circumference and counts per wheel revolution, including quadrature and gearing. Fit forward/backward distance scale with residuals. Use low-speed turns and arcs on the actual floor to estimate effective wheel separation, then check at another speed. Characterize passive-support alignment, slip and asymmetry; do not copy the simulation's 1.10 wheel-separation multiplier.

Check TF ownership and device reset semantics. Measure acquisition-to-callback and command-to-motion delays, clock offset and restart behavior; retain raw timestamps and uncertainty. Begin with straight lines and broad arcs, independently measure error, and verify invalid input stops before testing degraded operation.

## 5. Surveyed route and full laps

Measure board corners and internal reference points, ordered centerline samples, line width and uncertainty. Retain distinct visits at identical crossing coordinates. Verify tight turns using the full body footprint and permitted corridor, then run the full prescribed route. Use calibrated overhead measurement or another independent reference. Repeat before raising speed; preserve failed attempts. Predictive braking needs measured actuator response.

Store each calibration revision under `hardware/calibration/<revision>/` with device ID, date, units, source data/hash, residuals, conditions and uncertainty. Recalibrate after changes to wheels, load, supports or camera configuration. No calibration results currently exist in that location; create it when measurements are available.

## Troubleshooting

| Symptom | Check first |
| --- | --- |
| Wrong rotation or drifting TF | Encoder/IMU signs, transform direction, competing publishers, vendor relocalization |
| Straight-line oscillation | Timestamp delay, wheel response, lookahead and exposure |
| Wrong crossing branch | Ordered progress association and pose correction |
| Tight-turn cutting | Feasible turn, lookahead, speed and swept footprint |
| Sensor disconnect under load | Power drop, USB/cables and temperature |
| Low internal error but visible drift | Calibration, reference frame and independent measurement |

There is no real-vehicle `race.launch.py`. Current simulation launch files are not hardware deployment entry points. Remaining work and acceptance gates are maintained in [planning](planning/README.md).
