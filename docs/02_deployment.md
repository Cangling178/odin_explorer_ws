# 02 环境部署与构建

以下命令中的工作区路径按实际设备调整。两台设备各自在本机编译，不能把电脑的 x86 编译产物直接复制到 Jetson ARM 平台使用。

## 厂商源码与补丁

厂商独立工作空间位于 `vendor_ws`。驱动源码和 SDK 不纳入主仓库；目标版本为 `f51051f2d861f7643d4d33d2ade2952efe1a4672`（导入记录为 v0.14.4，固件要求需与实物核对）。新机器没有厂商目录时获取：

```bash
mkdir -p vendor_ws/src
git clone https://github.com/manifoldsdk/odin_ros_driver.git vendor_ws/src/odin_ros_driver
git -C vendor_ws/src/odin_ros_driver checkout --detach f51051f2d861f7643d4d33d2ade2952efe1a4672
for patch in vendor_ws/patches/*.patch; do
  patch_path="$(realpath "$patch")"
  git -C vendor_ws/src/odin_ros_driver apply --check "$patch_path" || exit 1
  git -C vendor_ws/src/odin_ros_driver apply "$patch_path" || exit 1
done
```

先获取并修补厂商源码，再执行本页 Jetson 编译步骤。上述循环用于刚检出的厂商版本；已有部分补丁的机器只应用尚未应用的编号，已复制完整修补后源码的机器不要重复应用。补丁使驱动实际读取 `config_file`、隔离 SDK 与 FastDDS 的同名符号，并改善 RGB 配置失败诊断，不修改定位算法。厂商许可证为 Apache-2.0，原许可证和第三方内容保留在厂商仓库内。

## Jetson 端

先准备匹配的 Ubuntu、ROS 2 Humble 与 ODIN 厂商驱动环境。厂商源码和 `.bin/.pgm` 等本地数据可能被 Git 忽略，部署时需要单独确认它们已经复制。

```bash
cd ~/odin_explorer_ws
source /opt/ros/humble/setup.bash

# 首次准备依赖；已有正确环境则不必重复安装。
rosdep install --from-paths src/odin_explorer --ignore-src -r -y --rosdistro humble

# 厂商独立工作空间；应用补丁后必须重新编译一次。
CMAKE_BUILD_PARALLEL_LEVEL=2 colcon --log-base vendor_ws/log build \
  --base-paths vendor_ws/src \
  --build-base vendor_ws/build \
  --install-base vendor_ws/install \
  --packages-select odin_ros_driver \
  --executor sequential \
  --cmake-args -DBUILD_SYSTEM=ROS2

source vendor_ws/install/local_setup.bash
CMAKE_BUILD_PARALLEL_LEVEL=2 colcon build \
  --base-paths src/odin_explorer \
  --packages-up-to explorer_bringup \
  --symlink-install --executor sequential \
  --cmake-args -DBUILD_TESTING=OFF
source install/local_setup.bash
```

### 终端 1：启动 ODIN 与导航

以下为当前实机已确认可用的启动命令。用户于 2026-09-22 确认启动问题已解决，且当前定位正确。`base_to_imu` 使用当前车体模型中的 ODIN IMU 中心位置。

此启动包含厂商驱动，不要同时另开一份 ODIN 驱动。

```bash
cd ~/odin_explorer_ws
source /opt/ros/humble/setup.bash
source vendor_ws/install/local_setup.bash
source install/local_setup.bash

ros2 launch explorer_bringup navigation_jetson.launch.py \
  map:="$PWD/data/maps/lab_01_edit.yaml" \
  odin_map:="$PWD/data/maps/lab_02.bin" \
  driver_config:="$PWD/vendor_ws/src/odin_ros_driver/config/control_command.yaml" \
  base_to_imu:='[0.201939,0.000258,0.063250,0.0,0.0,0.0]'
```

当前地图对齐默认值已保存为 `[0.95,5.05,0.0,0.0,0.0,-1.5708]`，重开终端、重启电脑后仍然有效。启动命令不需要填写 `map_from_odin`；若显式传入该参数，则会覆盖保存的默认值。安装外参通过上述 `base_to_imu` 参数提供。

## 电脑端

电脑不需要编译厂商驱动或适配节点。安装 RViz 和 Nav2 官方交互插件，并构建界面资源所在的包：

```bash
sudo apt install ros-humble-rviz2 ros-humble-nav2-rviz-plugins \
  ros-humble-navigation2 ros-humble-nav2-bringup \
  ros-humble-xacro ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher

cd ~/odin_explorer_ws
source /opt/ros/humble/setup.bash
colcon build --base-paths src/odin_explorer \
  --packages-select explorer_description explorer_navigation explorer_bringup \
  --symlink-install --cmake-args -DBUILD_TESTING=OFF
source install/local_setup.bash
```

### 终端 2：启动 RViz 交互界面

另开终端执行；同机调试可在导航所在电脑执行，分机部署时在显示界面的电脑执行。

```bash
cd ~/odin_explorer_ws
source /opt/ros/humble/setup.bash
source install/local_setup.bash

ros2 launch explorer_bringup navigation_rviz.launch.py
```

电脑要能找到模型资源，否则会有地图和 TF，却没有完整机器人外观。电脑不需要本地加载实验室地图文件，地图由 Jetson 发布。

## 两台 Ubuntu 的网络

两端在同一可互通局域网，`ROS_DOMAIN_ID` 一致，`ROS_LOCALHOST_ONLY=0`。建议使用相同 ROS 2 发行版和中间件，启用系统时间同步。这里使用 ROS 2 自身通信，不新增 TCP、串口或 CAN 节点。

分机部署时，在两个启动终端运行各自的 `ros2 launch` 前统一设置，例如：

```bash
export ROS_DOMAIN_ID=35
export ROS_LOCALHOST_ONLY=0
```

电脑可检查：

```bash
ros2 topic list
ros2 action list
ros2 run tf2_ros tf2_echo map base_link
```

应能发现 `/map`、`/odom`、`/navigation/obstacle_points`，以及 `/navigate_to_pose`、`/follow_waypoints`。发现不到时先核对网络、域编号和防火墙，不要在电脑上启动第二套导航来代替网络排查。

## 工作目录与数据

- `src/odin_explorer/` 只放五个当前使用的 ROS 包。
- `data/maps/` 保存正在使用的 `.bin`、`.yaml` 和 `.pgm`；地图原点与安装外参见[导航说明](04_navigation.md)。
- `data/odin_records/` 归档先前误生成在 `src/odin_ros_driver/` 下的地图、标定与设备状态日志；该目录不是 ROS 包。
- `data/calibration/cam_in_ex.txt` 保存先前位于 `image/` 的标定导出文件。
- `data/results/` 保留已有测量结果；`hardware/` 保留原始 CAD、设备标定和部件资料。
- `build/`、`install/`、`log/` 为可重新生成的构建产物，不属于源码。更换架构后应在目标设备重新构建。

[返回项目首页](../README.md) · [下一步：建图与地图](03_mapping.md)
