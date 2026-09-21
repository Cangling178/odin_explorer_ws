# Odin FishPoly camera simulation

English | [Simplified Chinese](FISHPOLY_CAMERA_cn.md)

As of 2026-09-14, both bench and onboard Odin cameras use the FishPoly geometry of device
O1-P040100136. The original [calib_device.yaml](../hardware/mechanical/odin1/calib_device.yaml)
is unchanged and installed verbatim at `share/racer_description/config/calib_device.yaml`.
Intrinsics, distortion and output dimensions come from that file; existing Xacro relative extrinsics remain in use.
The fixed competition overview camera remains pinhole inspection instrumentation.

## Model and sources

- [Vendor data-output specification, section 5.3](https://github.com/ManifoldTechLtd/wiki/blob/master/docs/odin_series/odin1/5.%20Data%20output_.md)
- [Vendor PolynomialCamera](https://github.com/manifoldsdk/odin_ros_driver/blob/main/include/polynomial_camera.hpp), local reference revision `f51051f2d861f7643d4d33d2ade2952efe1a4672`
- [Gazebo Classic wide-angle camera](https://classic.gazebosim.org/tutorials?tut=wide_angle_camera)
- [ROS Humble CameraInfo](https://github.com/ros2/common_interfaces/blob/humble/sensor_msgs/msg/CameraInfo.msg)

Optical axes are X right, Y down, Z forward. For `(X,Y,Z)`, define `r=hypot(X,Y)` and `theta=atan2(r,Z)`:

```text
theta_d = theta + k2*theta^2 + k3*theta^3 + ... + k7*theta^7
xd = theta_d * X/r
yd = theta_d * Y/r
u = A11*xd + A12*yd + u0
v = A22*yd + v0
```

The optical axis explicitly maps to the principal point. Inversion uses 48 bounded bisection iterations
in the forward hemisphere; derivative extrema are checked at load time to reject nonmonotonic models.
Only zero `p1/p2` is supported; nonzero tangential distortion is rejected. The archived `isFast`,
`numDiff` and `maxIncidentAngle` fields do not configure this implementation's solver, which builds
its own per-pixel lookup table. `maxIncidentAngle: 120` is not treated as image FOV.
Continuous powers two through seven differ from OpenCV fisheye and ROS equidistant parameterization.

Calibration-derived FOV is 128.8504 degrees horizontally, 103.2996 vertically, and 171.1627 along
one diagonal, measured between edge pixel centers. Maximum corner incidence is about 86.18 degrees.
These are calculated values, not measurements or forced fits to the nominal 129/104/173-degree specification.

## Rendering and interface

Gazebo scene -> six-face cubemap -> 2048x2048 equidistant image -> FishPoly inverse sampling -> 1600x1296 RGB.
Cubemap faces default to 1024x1024. The plugin precomputes OpenCV fixed-point maps and applies bilinear
resampling per frame. The intermediate image covers the forward hemisphere, including rays missing
from the former pinhole image. Calibration pixels too close to 90 degrees are rejected to avoid the
stock shader's cutoff feathering; the device calibration is fully covered. Finite texture resolution,
interpolation and antialiasing affect thin lines and boundaries, and do not model the physical lens resolution.

Implementation:

- [Geometry](../src/odin_racer/racer_description/racer_description/fishpoly.py): projection, unprojection, calibration and CameraInfo readers.
- [Gazebo plugin](../src/odin_racer/racer_description/plugins/odin_fishpoly_camera.cpp): resampling and ROS publication.
- [Shared configuration](../src/odin_racer/racer_description/config/odin_sensors.yaml): calibration path, render resolution, 10 Hz rate and clip distances.
- [World generator](../src/odin_racer/racer_description/racer_description/sensor_world.py): common bench/vehicle settings and calibration injection.

`calibration_file` is relative to the sensor configuration directory or absolute. The default is resolved
from hardware in a source checkout and from the package after installation. Rebuild and restart after
changing calibration. A custom calibration replaces intrinsics only; changing devices also requires checking extrinsics.

Existing `/sim/odin1` and `/sim/racer/odin1` namespaces remain:

| Topic | Contract |
| --- | --- |
| `image` | sensor_msgs/Image, rgb8, 1600x1296, 10 Hz |
| `camera_info` | Same acquisition stamp and odin_sim_camera_optical frame; Reliable, Volatile, depth=5 |

The custom CameraInfo contract is `distortion_model="fishpoly"`, `D=[k2,k3,k4,k5,k6,k7]`,
`K=[[A11,A12,u0],[0,A22,v0],[0,0,1]]`, `R=I`, `P=0`, default binning/ROI.
K retains skew. Zero P means no rectified pinhole projection is provided; it cannot project the raw image.
Standard ROS image pipelines do not automatically support this contract. Use
`FishPoly.from_info(info).project/unproject`. A future rectified stream needs separate standard pinhole CameraInfo.

## Build and validation

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src
source install/setup.bash
python3 tools/check_workspace.py
python3 -m unittest discover -s tests -v
python3 tools/validate_fishpoly_render.py
```

Build dependencies include gazebo_dev, gazebo_ros, rclcpp, sensor_msgs and libopencv-dev.
The angular-target test requires DISPLAY and starts/cleans up its own gzserver. Defaults are ROS domain 90
and Gazebo port 11389; use `--domain` and `--port` for available alternatives. It uses the shared sensor
generator but removes housing/ground occlusion to isolate lens geometry. Results are written to
`data/generated/fishpoly_render_validation.{json,png,log}`.

Run the moving sensor test using the [onboard instructions](README.md), with an empty world and sensor_targets.
Run the competition test using the [course instructions](COMPETITION_COURSE.md).
Both validators now use FishPoly: densely sampled curved target edges, and calibrated pixel rays intersected with the floor.

Local results on Historical validation date 2026-09-14; model scope:

| Check | Result |
| --- | --- |
| Build and unit tests | Three packages built; 27 tests passed, including vendor projection comparison, full-frame round trip, optical axis, FOV and invalid models |
| Corners, edges, center and cube seams | All 13 targets detected, max center error 0.230 px; no unrendered black pixels on uniform background; exactly matching image/info stamps |
| Stationary, forward, left/right turns, acceleration/braking | Passed; maximum target bound error 2.09 px, ground marker 2.99 px, threshold 8 px |
| Standalone bench | Matching 1600x1296 FishPoly image/info at 10 Hz; cloud about 9.35 Hz, IMU about 332.2 Hz; stationary gravity passed |
| Onboard rates | Image/CameraInfo 10 Hz, cloud about 10 Hz, IMU about 399.1 Hz in simulation time |
| Competition | Onboard black-line IoU 0.9787/0.9777 before/after motion; overview IoU 0.8534/0.8518; short motion and floor checks passed |
| Competition rates | Image/CameraInfo/cloud about 10 Hz, overview 2 Hz, IMU about 332.3 Hz, below the configured 400 Hz |
| Real-time factor | About 0.57 onboard and 0.85 competition; current computer/load, not Jetson performance |

Bench report: `data/generated/fishpoly_bench_validation.json`. Vehicle reports: `data/generated/fishpoly_sim_sensors_validation.json` and
`data/generated/fishpoly_competition_course_validation.json`; course PNGs share the report prefix.
These checks establish geometry/basic response, not hardware equivalence or full-course visibility.
Exposure, motion blur, noise, vignetting, JPEG compression, device processing latency and vendor SLAM remain absent.
