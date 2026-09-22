# 01 项目结构与接口

## 当前范围

本项目实现实验室已有地图上的目标点导航、固定和临时障碍物避让、RViz 选择多个点后的顺序巡航，并保留人工移动建图与模型预览。主体处理代码使用 C++，启动编排使用 Python；规划、局部控制、航点执行和点云过滤直接使用 Nav2、OctoMap 与 PCL。

不包含自主探索、赛道循迹、下位机程序、底盘通信、失效停车节点或无限循环巡航管理器。当前 `/cmd_vel` 需要后续底盘执行接口才能驱动真实小车。

## 两端分工

| 设备 | 运行内容 |
| --- | --- |
| Jetson | ODIN 驱动及重定位、C++ 数据适配、地图服务、Nav2 规划与控制、官方航点执行器、机器人模型发布 |
| 电脑 | RViz 官方 Nav2 面板、目标与航点选择、地图和导航状态显示 |

电脑端使用 `explorer_bringup/launch/navigation_rviz.launch.py` 和 `explorer_navigation/rviz/navigation_real.rviz`，需要模型资源及官方 `nav2_rviz_plugins`，没有自写 C++ 界面插件。电脑不运行第二套 Nav2，不直接连接 ODIN。

## 五个功能包

| 包 | 主要内容 |
| --- | --- |
| `explorer_description` | Xacro、STL、模型预览 |
| `explorer_odin` | `odin_nav_adapter`：定位、坐标和点云适配 |
| `explorer_localization` | `odin_cloud_gate` 与 OctoMap 建图启动配置 |
| `explorer_navigation` | `nav2_real.yaml` 和 `navigation_real.rviz` |
| `explorer_bringup` | 预览、建图、Jetson 导航和电脑 RViz 四个入口 |

导航数据流：

```text
ODIN .bin 重定位 → 厂商位姿与 TF → odin_nav_adapter → /odom、导航 TF
ODIN 实时点云 → 自身包络/高度过滤 → 小簇过滤 → 障碍标记点云
                                  └→ 保留真实回波 → 射线清除点云
二维地图 YAML/PGM → map_server → /map
/map + 实时点云 + 定位 → Nav2 → /cmd_vel
电脑 RViz → NavigateToPose / FollowWaypoints → Jetson Nav2
Jetson 的地图、模型、点云、路径和任务反馈 → 电脑 RViz
```

建图数据流：

```text
ODIN 实时点云 + 厂商采集时刻 TF → odin_cloud_gate → OctoMap → /map → YAML/PGM
```

## 导航接口

| 接口 | 类型或含义 |
| --- | --- |
| `/odin1/odometry` | 厂商 `nav_msgs/Odometry`，`odom` 到 `imu` |
| `/odin1/cloud_raw` | 厂商本帧 `sensor_msgs/PointCloud2`，`lidar` 坐标 |
| `/odin_vendor/tf`、`/odin_vendor/tf_static` | 导航入口隔离后的厂商坐标变换 |
| `/odom` | 适配后的车体连续里程计，`nav_msgs/Odometry` |
| `/navigation/obstacle_points` | 碰撞高度内的点，供障碍标记 |
| `/navigation/clearing_points` | 保留地面及高回波的点，供三维射线清除 |
| `/map` | `nav_msgs/OccupancyGrid`，保存地图由 map_server 发布 |
| `/plan`、`/local_plan` | 全局路径和局部轨迹 |
| `/global_costmap/costmap`、`/local_costmap/costmap` | 全局与局部代价地图 |
| `/cmd_vel` | `geometry_msgs/Twist`，Nav2 平滑后的速度输出 |
| `/navigate_to_pose` | `nav2_msgs/action/NavigateToPose`，单点导航 |
| `/follow_waypoints` | `nav2_msgs/action/FollowWaypoints`，按列表巡航一轮 |
| `/navigate_through_poses` | 官方途经点导航动作 |
| `/robot_description`、`/joint_states` | 模型及显示用关节状态，不是底盘运动反馈 |
| `/waypoints` | RViz 官方面板生成的航点标记 |

导航坐标树：

```text
map → odom → base_link → odin_imu → odin_lidar
                   └→ 机器人模型中的其他 link
```

`base_to_imu` 必须实测。厂商 `odom → map` 经过求逆和地图对齐后用于导航坐标树；不同时启用 AMCL。当前导航配置 `use_host_ros_time: 1`，由厂商驱动以主机接收时间打戳；适配器保留输入时间戳，不再补发当前时间。该模式不同于设备采集时间对齐模式 `2`。

障碍标记在车体坐标系中额外过滤低矮小簇：4 cm 邻接距离、最长边不超过 25 cm、最高点不超过 `base_link` 上方 4 cm。清除点云不应用小簇过滤。参数与使用范围见[导航与巡航](04_navigation.md)。

## 建图接口与模式区别

建图时直接使用厂商 `odom → imu → lidar`，网关输出 `/sensors/odin/points` 和 `/mapping/status`，OctoMap 发布 `/map`。默认地图消息的坐标系是 `odom`，不是导航时的 `map`。保存栅格图不等于保存 ODIN `.bin` 重定位地图，两者对应关系需要核对。

建图和导航入口不可在同一 ROS 域内同时争用 `/map` 或厂商设备。建图详细说明见[建图与地图](03_mapping.md)。

[返回项目首页](../README.md) · [下一步：部署与构建](02_deployment.md)
