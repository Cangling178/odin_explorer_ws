# Calibration plan

English | [Chinese](10_calibration_cn.md)

## Wheel geometry and motion

Measure loaded rolling circumference and encoder counts per wheel revolution.
Repeat forward and reverse travel over a measured distance; fit scale factors
and retain residuals. For the two rear drive wheels, estimate effective separation from slow rotations
and arcs on the competition surface, then test another speed. Inspect passive
caster realignment, tire slip and left/right response asymmetry; nominal geometry
alone may not explain dynamic turning error.

## Sensor extrinsics and optics

Record `base_link` origin explicitly. Measure the rigid base-to-ODIN1 transform,
verify rotation conventions and validate against known ground points. Save the
device-specific intrinsic model, calibration method, device identity, date and
residuals. Validate any vendor-model-to-ROS camera conversion before publishing
CameraInfo. Account for chassis pitch and floor nonplanarity in the error budget.

## Track survey

Measure board corners and several interior control points. Establish a world
frame, start/finish and travel direction. Survey the line center in ordered
segments with extra samples near curvature changes. Keep crossing branches
distinct despite coincident coordinates. Store line width, survey uncertainty,
allowed corridor and robot reference point.

## Time alignment

Identify device, ROS and monotonic clocks. Measure acquisition-to-callback and
command-to-motion delay. Estimate clock offsets using observable motion or
timestamp-supported synchronization, and check them after restart. Attach
uncertainty to delay compensation; do not overwrite original timestamps.

## Records and versioning

Create one calibration directory per revision under `hardware/calibration/`.
Include a short report, exact units, fit data location, validity conditions and
residual summary. Recalibrate after changing tires, gearing, payload, mount or
camera settings that affect the model. Reference the revision from every run.
