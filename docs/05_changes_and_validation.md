# 05 修改与验证记录

当前进展：上位机基本功能已完成，Jetson 与电脑跨机导航已运行，低矮小簇过滤已部署。最新实机输入测试及数值见[2026-09-23 导航验证](diagnostics/2026-09-23-navigation-validation.md)。本页后半部分的 2026-09-22 记录是历史基线，不代表当前仍未部署 Jetson。

导航实现沿用现成 Nav2 和 PCL 组件。部署、建图及操作说明分别见[部署](02_deployment.md)、[建图](03_mapping.md)和[导航](04_navigation.md)。

## 直接使用的开源算法和组件

没有自行编写路径搜索、轨迹采样、三维射线清除或航点执行算法。

| 功能 | 使用的现成组件 | 本项目所做的工作 |
| --- | --- | --- |
| 全局路径规划 | `nav2_navfn_planner/NavfnPlanner` | 配置地图、包络和规划参数 |
| 局部轨迹与避障 | `dwb_core::DWBLocalPlanner` | 配置差速车速度、加速度和轨迹评价 |
| 地图内障碍 | `nav2_costmap_2d::StaticLayer` | 加载已有二维栅格地图 |
| 实时障碍物 | `nav2_costmap_2d::VoxelLayer` | 接入标记点云和清除点云 |
| 障碍物周围代价 | `nav2_costmap_2d::InflationLayer` | 设置膨胀范围 |
| 车体形状碰撞检查 | DWB 的 `ObstacleFootprint` 评价器 | 使用不对称车体多边形，而非只看圆半径 |
| 去除车体点云 | PCL 的 `CropBox` | 填入自身包络，保留包络外点 |
| 高度过滤 | PCL 的 `PassThrough` | 分开选择障碍回波和清除回波 |
| 无效点处理 | PCL 的 `removeNaNFromPointCloud` | 删除无效坐标 |
| 顺序巡航 | Nav2 的 `FollowWaypoints` | 配置不可达点处理和短暂停留 |
| RViz 交互 | `nav2_rviz_plugins` | 提供适合实车话题的 RViz 配置 |

相关官方实现：[Nav2 Humble 启动代码](https://api.nav2.org/nav2-humble/html/navigation__launch_8py_source.html)、[Nav2 Humble RViz 面板源码](https://github.com/ros-navigation/navigation2/blob/humble/nav2_rviz_plugins/src/nav2_panel.cpp)、[PCL 包络过滤](https://pointclouds.org/documentation/classpcl_1_1_crop_box.html)、[PCL 直通过滤](https://pointclouds.org/documentation/classpcl_1_1_pass_through.html)。

## 逐项修改说明

以下路径均相对于工作区根目录，说明当前保留的导航实现。目录整理与删除项见本页末尾。

### 1. 新增定位与点云适配节点

文件：`src/odin_explorer/explorer_odin/src/odin_nav_adapter.cpp`

这是本次新增的主要 C++ 程序，带有必要的中文注释。

订阅：

| 话题 | 内容 |
| --- | --- |
| `/odin1/odometry` | 厂商连续位姿，父坐标为 `odom`，子坐标为 `imu` |
| `/odin_vendor/tf` | 隔离后的厂商动态变换 |
| `/odin_vendor/tf_static` | 隔离后的厂商静态变换 |
| `/odin1/cloud_raw` | 本帧原始雷达点云，坐标为 `lidar` |

发布：

| 话题或变换 | 作用 |
| --- | --- |
| `/odom`，`nav_msgs/Odometry` | Nav2 使用的车体连续位姿与差分速度 |
| `map → odom` | 全局重定位修正及二维地图对齐 |
| `odom → base_link` | 连续车体运动，平面化为二维位置和朝向 |
| `base_link → odin_imu → odin_lidar` | 实测车体外参和设备内部雷达外参 |
| `/navigation/obstacle_points` | 碰撞高度范围内的点，仅负责障碍标记 |
| `/navigation/clearing_points` | 保留地面和高处有效回波，仅负责三维射线清除 |

位姿处理采用以下关系，`T_A_B` 表示 B 坐标系在 A 坐标系中的位姿：

```text
T_厂商odom_车体 = T_厂商odom_imu × inverse(T_车体_imu)
T_二维map_车体 = T_二维map_厂商map × inverse(T_厂商odom_厂商map) × T_厂商odom_车体
T_导航odom_车体 = 平面化(T_厂商odom_车体)
T_二维map_导航odom = 平面化(T_二维map_车体) × inverse(T_导航odom_车体)
```

厂商源码实际发布 `odom → map`，适配节点会求逆，不是简单交换坐标名字。全局修正在两次厂商更新之间保持，局部里程计不会因为这项全局修正而跳变。适配针对实验室平整地面，不是坡道或三维导航方案。

旧版厂商消息可能不填写速度，因此适配节点从连续车体位姿计算平面速度。不复制厂商的协方差数组，也不把显示用轮关节当作运动反馈。

点云先用设备外参变换到车体坐标中调用 PCL 过滤，然后变回雷达坐标输出。这样 Nav2 清除射线仍从真实雷达原点发出。驱动输入时间戳保持不变，当前导航配置使用主机接收时间。标记高度和清除回波分别处理，避免因删除地面或远处高回波导致旧障碍无法清除。

### 2. 新增适配参数

文件：`src/odin_explorer/explorer_odin/config/nav_adapter.yaml`

主要参数：

| 参数 | 当前起始值 | 含义 |
| --- | --- | --- |
| `floor_z_in_base` | `-0.03325` | 地面相对车体原点的高度；参考现有轮半径 |
| `obstacle_min_z` | `0.02` | 障碍标记的最低车体坐标高度 |
| `obstacle_max_z` | `1.2` | 障碍标记的最高车体坐标高度 |
| `small_cluster_tolerance` | `0.04` | 点簇邻接距离，单位米 |
| `small_cluster_max_extent` | `0.25` | 允许删除的簇最长边，设为 0 关闭 |
| `small_cluster_max_z` | `0.04` | 允许删除的簇最高点，车体坐标高度 |
| `self_box` | `[-0.06,0.25,-0.16,0.16,-0.04,0.20]` | 自身点云排除包络 |

这些是实车调参起点，不代表传感器安装已经标定。`self_box` 只应包含车体自身；设得过大会删掉真实障碍。障碍高度应覆盖可能碰到车体或上方设备的桌腿、桌沿等区域。

### 3. 修改适配包的构建和依赖

文件：

- `src/odin_explorer/explorer_odin/CMakeLists.txt`
- `src/odin_explorer/explorer_odin/package.xml`

增加 C++17 可执行程序 `odin_nav_adapter`，声明 ROS 消息、TF、PCL 和消息转换依赖，并安装到 ROS 包可执行目录。不修改厂商 SDK 或定位算法；另有一处厂商配置参数读取修补，见后文。

### 4. 新增实车 Nav2 配置

文件：`src/odin_explorer/explorer_navigation/config/nav2_real.yaml`

这是当前唯一的 Nav2 运行配置；旧纯模拟导航配置及入口已在整理中移除。

主要变化：

1. 不配置 AMCL，由 ODIN 适配提供全局定位。
2. 全局和局部代价地图都使用静态层、体素层和膨胀层。地图中已有的桌子由静态层表示，临时桌椅由实时点云加入体素层。
3. 障碍点云只标记，清除点云只清除。清除观测保留较高的远处回波，由 Nav2 将射线裁剪到体素网格边界；没有把视野外区域直接当作空地。
4. 使用实际车体坐标方向的多边形包络：后侧 `-0.06 m`，前侧 `0.25 m`，左右各 `0.16 m`，另加 `0.02 m` 包络余量；上车前应按实物核对。
5. 局部地图为 `4 m × 4 m`，分辨率 `0.05 m`；体素高度从 `-0.1 m` 起，每层 `0.1 m`、共 16 层，最高到 `1.5 m`。
6. 线速度上限起始值为 `0.20 m/s`，角速度为 `0.70 rad/s`，位置和朝向容差各为 `0.15 m`、`0.15 rad`。
7. 巡航遇到不可达点时结束该次任务，不跳过该点；正常到点短暂停留 `200 ms` 后执行下一个点。
8. 使用 Nav2 官方导航行为树、恢复行为和速度平滑器；未新增停车保护节点。

修改参数文件后重新启动 Jetson 导航入口使其生效。改变障碍高度或传感器安装高度时，需要一起核对适配参数、两张代价地图中的观测高度和体素范围。雷达原点也必须位于体素网格高度范围内，否则无法进行射线清除。

### 5. 新增 Jetson 启动文件

文件：`src/odin_explorer/explorer_bringup/launch/navigation_jetson.launch.py`

负责启动驱动、适配、机器人模型、地图服务和 Nav2，不启动 RViz。

启动时读取厂商配置并生成临时副本，强制设置本链路所需的内容：

- 重定位模式 `custom_map_mode=2`。
- `.bin` 地图路径使用 `odin_map` 参数。
- 开启里程计、原始点云和设备 TF。
- `use_host_ros_time` 保留厂商配置文件的值（当前为 `1`，主机接收时间），不再强制改成 `2`。原强制覆盖未经过实机验证，现已撤销；时间戳与 ROS 时间是否一致仍需结合实际输出检查。
- 关闭额外 TF 预测重发，使用实际位姿时间戳。
- 将厂商 `/tf`、`/tf_static` 重映射到 `/odin_vendor/tf`、`/odin_vendor/tf_static`。

**不修改你正在编辑的 `vendor_ws/src/odin_ros_driver/config/control_command.yaml`。** 临时副本在正常退出时删除。原配置中的其他设备设置仍被保留。

地图生命周期管理器延迟两秒启动，给服务发现留出时间。Nav2 仅加载 `navigation_launch.py`，地图服务单独启动，因此不会偷偷再启动 AMCL。界面中的 `Localization: active` 对应这里的地图生命周期管理器状态，不代表 ODIN 重定位质量已经通过检查。

### 6. 新增电脑 RViz 配置与启动文件

文件：

- `src/odin_explorer/explorer_navigation/rviz/navigation_real.rviz`
- `src/odin_explorer/explorer_bringup/launch/navigation_rviz.launch.py`

这是**电脑显示交互部分**。启动文件只运行 `rviz2`，其动作请求通过 ROS 2 网络交给 Jetson。

显示内容包括：

- `/map` 二维地图。
- `/robot_description` 机器人模型及 TF。
- `/navigation/obstacle_points` 实时障碍点云。
- 全局和局部代价地图。
- `/plan` 全局路径、`/local_plan` 局部轨迹。
- 机器人碰撞包络。
- `/waypoints` 航点标记。
- Nav2 官方面板中的任务状态和反馈。

固定坐标系为 `map`。移除了模拟激光、AMCL 粒子和 `2D Pose Estimate` 工具，保留官方 `Nav2 Goal`。点云显示使用适合传感器流的尽力传输订阅。

### 7. 修改启动包依赖

文件：`src/odin_explorer/explorer_bringup/package.xml`

补充适配包、Nav2 地图与生命周期组件、机器人显示、Xacro 和 YAML 等运行依赖。现有安装规则会自动安装新增的 launch、参数和 RViz 文件，不需要另写安装脚本。

### 8. 修补厂商配置文件参数读取

文件：

- `vendor_ws/src/odin_ros_driver/src/host_sdk_sample.cpp`
- `vendor_ws/patches/0001-respect-config-file.patch`

当前厂商 launch 虽然声明了 `config_file`，但原 C++ 主程序没有读取它，仍固定使用源码目录里的 `control_command.yaml`。本次补上 ROS 2 参数声明与读取，使新导航入口生成的配置副本真正被使用。默认不传参数时，仍保持厂商原来的路径。没有改动厂商定位算法或 SDK。

厂商目录是独立仓库且不纳入主仓库源码，因此同时保存补丁文件。将项目部署到另一台机器、重新获取同版本厂商源码时，在工作区根目录应用一次：

```bash
git -C vendor_ws/src/odin_ros_driver apply --check ../../patches/0001-respect-config-file.patch
git -C vendor_ws/src/odin_ros_driver apply ../../patches/0001-respect-config-file.patch
```

以上命令仅说明 `0001` 配置参数补丁。后续还增加了 `0002` SDK 符号隔离和 `0003` RGB 失败诊断；完整部署按[部署与构建](02_deployment.md)依次应用所有补丁。如果复制的是已经修补的厂商源码，不要重复应用补丁。应用后需要重新编译厂商包；`0001`～`0003` 不修改运行配置；`0004-save-navigation-config.patch` 则保存本实验室导航配置，换机后需调整其中的绝对路径。

### 运行排查后的点云修复

2026-09-22 根据实机传输排查，将导航适配器 `/odin1/cloud_raw` 输入改为 Reliable，并在厂商驱动链接时隐藏静态 SDK 的动态导出符号，避免 SDK 与 FastDDS 的同名 MD5 实现冲突。RGB 失败日志补充耗时、错误类别和实际帧率；这是诊断改善，设备配置应答超时尚未根治。

两个包已编译并安装。正式适配器经隔离输出验证，障碍点云约 10.26 Hz、最大收帧间隔约 0.14 秒；安装驱动的 SDK MD5 动态导出符号为 0。运行中的原节点未重启，新驱动共享内存和 RGB 命令结果需在下次启动确认。证据与验证边界见[运行排查报告](diagnostics/2026-09-22-runtime-check.md)。

## 2026-09-23 小簇过滤

新增 `explorer_odin/src/small_obstacle_filter.hpp`，使用 PCL 欧氏聚类按包围盒尺寸及最高点过滤低矮小簇。`odin_nav_adapter.cpp` 仅在障碍标记分支调用；射线清除分支不调用。构建新增 PCL segmentation/search 组件，`BUILD_TESTING=ON` 时构建并注册 `test/small_obstacle_filter_test.cpp`。电脑和 Jetson 均编译并通过该测试，参数、源码及安装产物已同步到 Jetson。

## 2026-09-22 历史验证记录与适用边界

本机验证日期：2026 年 9 月 22 日。环境为开发电脑上的 ROS 2 Humble，测试使用隔离的 ROS 域，没有连接或控制真实底盘。

| 验证项目 | 实际结果 |
| --- | --- |
| 本项目相关包编译 | 5 个包构建成功；关闭单元测试构建，没有新增单元测试 |
| 厂商配置参数补丁 | 厂商驱动重新编译成功；传入不存在的配置路径时，日志准确报告该路径并在连接设备前退出，确认参数已实际生效 |
| 启动及配置语法 | 两个新增 launch、适配参数、Nav2 参数和 RViz 配置检查通过 |
| 外参和地图变换 | 使用非零 IMU 安装位置、安装偏航角，以及非零厂商地图平移与旋转，验证转换后的车体地图位置正确 |
| PCL 过滤 | 障碍点保留；自身点、无效点不进入输出；地面和高回波仅保留在清除点云中 |
| 静态障碍规划 | 在人工构造的二维地图中，规划路径绕过固定矩形障碍 |
| 临时障碍规划 | 栅格地图未包含的新障碍进入全局代价地图，并使路径改道 |
| 临时障碍清除 | 障碍移走并改变观测朝向后，检查区域中的致命占据单元从 10 个降至 1 个；有限观测下仍有边缘残留，未宣称瞬间完全清除 |
| 单点导航 | `NavigateToPose` 返回成功；目标 `(1.7, 0.9)`，最终模拟位置约 `(1.581, 0.852)`，位置误差约 `0.128 m` |
| 顺序巡航 | `FollowWaypoints` 执行两个航点成功，没有遗漏点；最终目标 `(4.0, 0.0)`，位置约 `(3.932, 0.118)`，误差约 `0.136 m` |
| 绕障轨迹 | 联调中车体原点到矩形障碍边界的最小距离约 `0.342 m`；此数值仅描述该人工场景 |
| RViz 显示 | 实际启动官方面板，确认地图、机器人、实时点云、代价地图、路径及导航反馈可以显示 |

临时验证脚本和临时场景数据在验证后删除，没有加入交付源码。随后项目整理已删除原有建图测试和纯模拟导航测试；本页保留历史验证结果，不保留这些旧场景的测试代码；2026-09-23 新增的小簇过滤回归测试单独保留。

以上证明本次软件接口与 Nav2 链路在受控输入下能够工作，不等同于 Jetson 实物运行、ODIN 实测视场或跨机网络已验收。当时没有可用的 Jetson 实机连接，因此 ARM 环境依赖、设备时钟对齐质量、实际安装外参、两份实验室地图的对齐及网络表现，需要按[操作建议](04_navigation.md#建议的操作顺序)现场核对。

实时障碍的清除依赖真实回波经过旧体素。遮挡、视野变化、无有效远处回波和体素离散都可能留下部分旧占据；本实现直接使用 Nav2 官方射线清除，不额外添加无观测依据的定时擦除。


## 2026-09-22 历史目录整理

文档统一为中文，按项目结构、部署、建图、导航、修改与验证五个主题连续编号。删除旧迁移记录、人员分工和自主探索规划、英文重复说明、下位机协议占位目录和 `explorer_hardware` 空壳包，以及未使用的接口模板。

删除纯模拟导航启动文件、模拟器、模拟参数和对应 RViz 配置；删除建图与模拟导航测试、测试依赖、旧检查脚本及 CI 中的测试命令。保留当前五个功能包、模型预览、人工建图、实车导航、电脑 RViz 和厂商配置补丁。

地图、标定、实测结果和 CAD 原件没有删除。原 `src/odin_ros_driver/` 中只有设备生成的数据，已整体归位到 `data/odin_records/`；原 `image/cam_in_ex.txt` 归位到 `data/calibration/`。第三方厂商代码、SDK、许可证和独立 Git 历史保持完整。

清理自有工作空间旧 `build/install/log` 后重新构建，避免已删除的包和模拟入口仍留在安装目录。CI 仅安装依赖并编译当前包，不运行已移除的测试。

整理后验证：从干净目录编译五个功能包成功；16 份自有中文文档的本地链接有效；包间依赖和启动配置语法检查通过。未运行单元测试，未保留本次检查脚本。

另清理根目录测试缓存及 `data/results/alignment/` 中一次性离线验证脚本、下载工具、导出点云和中间数组；保留输入地图、对齐报告、JSON 结果、图片与配置记录。归档报告统一命名为 `README.md`。
