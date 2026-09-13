# Simulation plan

English | [Chinese](README_cn.md)

A Gazebo Classic 11 standalone Odin sensor bench is available; vehicle contact and drive are pending.
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
