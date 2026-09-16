# ODIN1 integration

English | [Chinese](04_odin1_integration_cn.md)

## Verified upstream context

The [manufacturer product page](https://www.manifoldtech.cn/products/odin1/)
describes RGB, IMU, point-cloud and pose outputs. Its listed SLAM accuracy is
approximately +/-5 cm + 1%; this is not a guarantee of centimeter-level line
tracking on this course. Validate local observations and independent error.

The [vendor driver README](https://github.com/manifoldsdk/odin_ros_driver)
recommends Humble on Ubuntu 22.04 and identifies version-specific firmware
requirements. On 2026-09-10 the live README listed driver v0.14.4 with firmware
v0.14.0; search indexes showed older versions. Ubuntu 24.04 was not officially
supported by that README at the time of review.

Driver v0.14.4 was imported on 2026-09-11 with its exact commit recorded. It has
been built on the development laptop, and the user confirmed RViz point cloud display;
see [vendor integration notes](../vendor_ws/README.md). This identifies the local
source revision, but the device firmware and Jetson platform pair are not yet accepted
or locked. The `racer_odin` adapter, image/IMU quality and vehicle integration remain pending.

## Integration sequence

1. Record sensor model, device firmware, Jetson OS and architecture.
2. Review the exact vendor commit and its ROS 2 build script before execution.
3. Use `vendor_ws/src/odin_ros_driver` so the source sits directly under a ROS
   workspace `src/` directory. The underlay is isolated from first-party packages.
4. Match firmware requirements, build the vendor package and save its commit SHA
   and build evidence in `vendor_ws/README.md` and the platform lock template.
5. Inspect actual topics, message types, frames, timestamps and QoS. The names in
   our interface document are adapter contracts, not assumed vendor topics.
6. Record a stationary sample, slow translation, slow rotation and ground view.
7. Add explicit remaps and transformations in `racer_odin`, then validate them.

Do not copy ROS 1 launch files into this overlay or silently modify upstream code.
The manufacturer's Odin-Nav-Stack example is based on ROS 1 Noetic / Unitree Go2;
use its integration concerns as reference, not as a drop-in ROS 2 dependency.

## Observations to record

| Check | Evidence |
| --- | --- |
| RGB access | Encoding, resolution, exposure and measured frame rate |
| Camera model | Device-specific calibration and projection model |
| Ground visibility | Closest/farthest usable ground distance and line pixel width |
| Timing | Acquisition clock, host clock offset, transport and processing delay |
| Pose | Parent/child frames, reset behavior, covariance, stationary jitter |
| TF | Publisher inventory and transform direction |
| Recovery | USB unplug/replug, driver restart and invalid-data signaling |
| Compute | CPU/GPU/RAM, USB bandwidth and thermal behavior |

Use the supplied camera model correctly. A wide-angle image must not be treated
as an ideal pinhole image without validating rectification. A planar homography
applies to calibrated ground geometry; it does not fix arbitrary lens distortion.
Preserve acquisition timestamps and do not restamp old observations as new.

## First feasibility decision

Capture a short sequence containing a straight, crossing and tight bend under
expected lighting. Confirm that a visible line can be projected into a stable
ground frame with error small enough for the proposed budget. If that fails,
resolve mounting/calibration or choose a rule-compatible sensing alternative
before spending time tuning a high-speed controller.

## Real-camera integration gap — 2026-09-16

Local vendor source publishes `odin1/image`; this source inspection found no companion CameraInfo publisher. Current perception requires exact image/CameraInfo timestamps, the `fishpoly` model and acquisition-time TF. An adapter must supply matching calibration while preserving image acquisition timestamps and distinguish raw from rectified image models. The existing device calibration copy does not establish measured mounting extrinsics or ground height. Next validate real images, frame rate/latency and ground projection, then moving replay and chassis closure. Current simulation launches are not hardware entry points.
