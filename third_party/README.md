# Official Odin navigation stack integration

English | [简体中文](README_cn.md)

Upstream: [Odin-Nav-Stack](https://github.com/ManifoldTechLtd/Odin-Nav-Stack), [quick start](https://github.com/ManifoldTechLtd/Odin-Nav-Stack#quick-start), [Docker setup](https://github.com/ManifoldTechLtd/Odin-Nav-Stack/blob/main/docs/DOCKER_SETUP.md).

This is a ROS 1 Noetic / Ubuntu 20.04 stack for Unitree Go2, with NeuPAN as the recommended local planner, not a ROS 2 Nav2 driver. It is an isolated integration candidate for our Humble/F4 base. Sources, a driver patch and Docker configuration copies are prepared; no ROS1 build, runtime installation or hardware connection has been performed.

## Layout and pinned versions

`third_party/Odin-Nav-Stack` is a Git submodule preserving upstream `ros_ws/src`, `NeuPAN`, `yolov5`, `scripts` and `docker`. `third_party/COLCON_IGNORE` excludes it from first-party discovery. `odin_nav_stack.lock.json` records revisions and the driver override; `patches/odin_driver_ros1_navigation.patch` records modifications.

- Stack: `e6a28acef044bad8aa5daaef3a8f4b07904ca85b`.
- NeuPAN: `0fd78fd6232356bd80ec61db7737f2232077765d`.
- YOLOv5: `1f1e7b9086131bc24039970f6ebbb67c5fe55b77` (fetched, semantic features not deployed).
- Upstream driver gitlink: `13aa528...`; tutorial upgrade pinned to inspected revision `f51051f2d861f7643d4d33d2ade2952efe1a4672`, with a local integration patch.

Preserve upstream licenses; the top-level Apache-2.0 license does not replace dependency licenses. The parent repository stores gitlinks, patch, setup tool and documentation rather than copying upstream implementation as first-party code.

## Reproduce preparation

From the project root:

```bash
bash tools/setup_odin_nav_stack.sh
```

The tool initializes dependencies with a one-command HTTPS rewrite for NeuPAN's upstream SSH URL, pins the driver and applies the patch. It preserves existing Docker configurations and refuses to switch a modified driver revision.

The patch sets host timestamps (`use_host_ros_time: 1`) and mapping mode (`custom_map_mode: 1`), moves only ROS1 odom-to-imu TF publication from STANDARD to HIGHFREQ, preserves its enable switch and device extrinsics, and selects the provided ROS1 package manifest. The ROS2 branch is unchanged. Driver v0.14 uses `imu`, not the older tutorial's `odin1_base_link` name.

Four upstream configurations are copied to `docker/configs/`; `docker/maps/{grid,relocalization,pcd}` are created. The container driver copy writes maps to the mounted `/opt/odin/maps/relocalization`. Host-time mode uses receive time in the pinned driver, not proven sensor acquisition time; timing and firmware still require validation.

The stack submodule intentionally appears modified after preparation due to the driver override/patch and local configuration. Use the setup tool and lock file to reproduce this state; do not use force-reset or submodule update --remote to remove the indicator. The existing ROS2 driver under `vendor_ws/src` is untouched.

## Environment and mapping workflow

This machine is x86_64 with Humble only; Docker, Conda/Mamba and Noetic are absent. Upstream Dockerfiles target Jetson L4T R35 and hard-code aarch64 Miniforge. They are not ready-made x86 images. Choose a matching JetPack/L4T image on the actual Jetson; that target is not yet validated. Changing ROS_DISTRO in a Humble shell does not install Noetic.

In a separately prepared Noetic environment, the tutorial's catkin build can initially select only mapping/navigation utility packages, excluding the Go2 SDK-dependent package:

```bash
# From the navigation stack root, in a prepared Noetic environment
source /opt/ros/noetic/setup.bash
cd ros_ws
catkin_make -DCMAKE_BUILD_TYPE=Release -DBUILD_SYSTEM=ROS1 \
  -DCATKIN_WHITELIST_PACKAGES='odin_ros_driver;pointcloud_saver;pcd2pgm;map_planner;fake360'
```

Not executed here. Install Noetic PCL, cv_bridge, TF, map_server and other declared dependencies first. NeuPAN needs the separate Python environment described upstream. None of these are required for the first-party colcon build.

After the ROS1 build and device validation, use two terminals at the stack root:

```bash
# Terminal 1
source ros_ws/devel/setup.bash
roslaunch odin_ros_driver odin1_ros1.launch

# Terminal 2
bash scripts/map_recording.sh laboratory
```

The interactive script captures PCD, requests a device map save and generates a grid. Outputs: `ros_ws/src/pcd2pgm/maps/` and `ros_ws/src/map_planner/maps/`; the device binary path follows driver configuration. Use container paths for mounted storage. The script may update mode/map name, but the actual binary path must still be set manually before restarting for relocalization. Skip automatic config edits for read-only Docker mounts; edit the host copies instead.

## Integration gaps found in pinned source

- `whole.launch` enables Unitree control and Go2 extrinsics/sensor parameters. Replace them with the F4 command interface and measured geometry. The default NeuPAN DUNE model is Go2-specific; upstream requires training/tuning for other chassis.
- The ODIN driver include is commented out in `whole.launch`, contrary to the Docker documentation's automatic-start description. Start it separately or explicitly add the include.
- The Dockerfile does not supply the launch's foxglove_bridge, pointcloud_to_laserscan and Go2 control node. The default image/launch combination is not a validated deployment.
- ROS1 `/cmd_vel` uses Twist. Future integration must adapt it to `/navigation/cmd_vel`, add sequence/freshness checks, limits and disconnect stopping, then feed arbitration. The tutorial UDP snippet is not the project's final drive interface.
- Verify map/odom direction and unique TF ownership before bridging. Do not run both driver copies against one device or with conflicting TF.
- Manual mapping, relocalization and goal navigation do not implement autonomous exploration. Frontier goals, online mapping and completion logic remain pending.
