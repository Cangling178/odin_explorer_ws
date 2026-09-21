# Odin 官方导航栈接入

[English](README.md) | 简体中文

上游：[Odin-Nav-Stack](https://github.com/ManifoldTechLtd/Odin-Nav-Stack)，[快速开始](https://github.com/ManifoldTechLtd/Odin-Nav-Stack#quick-start)，[Docker 教程](https://github.com/ManifoldTechLtd/Odin-Nav-Stack/blob/main/docs/DOCKER_SETUP.md)。

这是 ROS 1 Noetic / Ubuntu 20.04 导航栈，官方平台为 Unitree Go2，推荐局部规划器为 NeuPAN；不是 ROS 2 Nav2 驱动。当前 ROS 2 Humble + F4 工程将其作为独立第三方集成候选。此次已准备源码、驱动补丁和官方 Docker 配置副本，未安装运行环境、编译此导航栈或连接设备。

## 位置与版本

```text
third_party/
├── COLCON_IGNORE                    # 隔离于自研 ROS 2 构建
├── odin_nav_stack.lock.json          # 精确版本及集成覆盖记录
├── patches/odin_driver_ros1_navigation.patch
└── Odin-Nav-Stack/                   # Git 子模块，保留官方布局
    ├── ros_ws/src/                   # ROS 1 catkin 包
    │   ├── odin_ros_driver/          # 导航专用驱动副本
    │   ├── map_planner/              # 栅格上的 A* 和目标状态机
    │   ├── fake360/                  # 障碍观测记忆
    │   ├── pointcloud_saver/         # 点云录制
    │   └── pcd2pgm/                  # 点云转换栅格
    ├── NeuPAN/                      # 官方指定 fork 的子模块
    ├── yolov5/                      # 官方子模块；本阶段不部署语义功能
    ├── scripts/                     # 建图等官方脚本
    └── docker/                      # 官方容器构建、配置和地图目录
```

- 导航栈：`e6a28acef044bad8aa5daaef3a8f4b07904ca85b`。
- NeuPAN：`0fd78fd6232356bd80ec61db7737f2232077765d`。
- YOLOv5：`1f1e7b9086131bc24039970f6ebbb67c5fe55b77`。
- 上游锁定驱动 `13aa528...`；按教程升级到当前核对的 `f51051f2d861f7643d4d33d2ade2952efe1a4672`，并显式记录本地补丁。

保留所有上游许可证；顶层 Apache-2.0 不覆盖各子模块自己的许可。主仓库只记录 Git 子模块引用、补丁、准备工具和文档，不复制第三方源码为自研代码。

## 获取与准备

从工程根目录执行：

```bash
bash tools/setup_odin_nav_stack.sh
```

脚本初始化上游及子模块，对 NeuPAN 的 SSH URL 使用一次性的 HTTPS 替换，无须设置 GitHub SSH 密钥；锁定上述驱动版本并应用补丁。重复执行保留已有 Docker 配置，不覆盖用户修改；版本不一致且已有驱动修改时会停止。

按教程完成的驱动调整：

1. `use_host_ros_time: 1`，`custom_map_mode: 1`，先做建图。
2. 仅将 ROS 1 分支的 `odom → imu` 广播从 STANDARD 移到 HIGHFREQ；保留发布开关及原设备外参广播，ROS 2 分支不变。v0.14 使用 `imu`，不套用旧教程的 `odin1_base_link` 名称。
3. 使用仓库已有 `package_ros1.xml` 作为该副本的 `package.xml`，避免 catkin 将它当作 ament 包。
4. 按 Docker 教程复制四个默认配置到 `docker/configs/`，建立 `docker/maps/{grid,relocalization,pcd}`；容器版地图输出指向 `/opt/odin/maps/relocalization`，对应宿主机持久化目录。

`use_host_ros_time=1` 在锁定驱动中使用主机接收时间，不能声称是设备采集时间；上车前还需验证延迟及时间语义。固件版本尚未核对。

准备后 `git status` 中导航子模块会显示已修改：这是驱动版本覆盖、补丁及本地配置的预期结果。重建方法由准备工具与锁文件记录。不要对它执行 `git submodule update --remote` 或强制重置来消除提示。原有 `vendor_ws/src/odin_ros_driver` 是 ROS 2 接入副本，不受这些补丁影响。

## 教程在当前机器上的适用范围

本次检查：本机是 x86_64，只有 `/opt/ros/humble`；没有 Docker、Conda/Mamba 或 Noetic。上游 Dockerfile 默认 Jetson L4T R35，且硬编码 aarch64 Miniforge，因此不能直接作为本机 x86 镜像。Jetson 也需先按实际 JetPack/L4T 选择镜像；当前工程未验证目标 Jetson 版本。

官方完整构建/启动流程见上方链接。不要在当前 Humble shell 中用 `export ROS_DISTRO=noetic` 冒充 Noetic 环境。具有完整 Noetic 环境后，可先按官方 `catkin_make` 流程只构建建图所需包，避免要求 Go2 SDK：

```bash
# 在已准备好 Noetic 依赖的独立环境中，从导航栈根目录执行
source /opt/ros/noetic/setup.bash
cd ros_ws
catkin_make -DCMAKE_BUILD_TYPE=Release -DBUILD_SYSTEM=ROS1 \
  -DCATKIN_WHITELIST_PACKAGES='odin_ros_driver;pointcloud_saver;pcd2pgm;map_planner;fake360'
```

该命令尚未在本机执行。还需 Noetic 的 PCL、cv_bridge、TF、map_server 等依赖；NeuPAN 的 Python 环境按官方教程另建。自研 `colcon build --base-paths src` 不需要这些 ROS 1 依赖。

## 后续先验证人工移动建图

在完成 Noetic 建图包构建和设备验证后，按官方流程打开两个终端（均从导航栈根目录）：

```bash
# 终端 1
source ros_ws/devel/setup.bash
roslaunch odin_ros_driver odin1_ros1.launch

# 终端 2
bash scripts/map_recording.sh laboratory
```

脚本交互控制开始/停止，保存 PCD、请求保存设备地图并生成栅格。PCD 在 `ros_ws/src/pcd2pgm/maps/`，栅格在 `ros_ws/src/map_planner/maps/`；设备 `.bin` 路径取决于实际驱动配置。容器中使用对应挂载路径。脚本末尾可修改建图模式和地图名，但仍需手动填写实际 `.bin` 的 `relocalization_map_abs_path` 并重启驱动。Docker 配置以只读方式挂载时，跳过脚本自动修改配置，在宿主机编辑。

## 与 F4 / ROS 2 集成前必须改的部分

- `whole.launch` 启用 `unitree_control`、包含 Go2 安装偏移和传感器参数，不能直接作为本车入口；需要移除 Go2 出口并用实测参数替换。NeuPAN 默认加载 Go2 DUNE 模型，官方要求按本车几何训练和调参。
- 当前 `whole.launch` 的 ODIN 驱动 include 被注释；Docker 文档所述“自动启动驱动”与此提交不同，需单独启动或明确增加 include。
- 当前 Dockerfile 未安装 `whole.launch` 使用的 `foxglove_bridge`、`pointcloud_to_laserscan`、Go2 控制节点；它提供的默认镜像/启动组合尚不能视为已验证部署。
- 输出是 ROS 1 `geometry_msgs/Twist /cmd_vel`。未来适配到 `/navigation/cmd_vel`，补足序号、时效、限幅和断连停车，再接统一仲裁；官方简化 UDP 示例不能直接充当本项目最终驱动出口。
- 驱动本身还发布全局变换；桥接前核对 `map/odom` 方向及唯一发布者，不能和现有 ROS 2 驱动同时占用同一设备或争用 TF。
- 官方教程主要是人工建图、重定位和指定目标导航，尚不等于本项目的自主探索建图。前沿目标选择、在线地图更新与结束条件仍需实现。

以上差异直接来自锁定源码的检查；本次没有为 F4 编造安装外参、运动参数或可运行导航入口。
