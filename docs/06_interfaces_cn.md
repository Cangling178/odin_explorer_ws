# 接口约定

[English](06_interfaces.md) | 简体中文

以下是目标接口，尚无实车适配实现；不是厂商话题名称声明。

| 接口 | 类型 | 发布者 → 使用者 |
| --- | --- | --- |
| `/sensors/odin/points` | sensor_msgs/PointCloud2 | ODIN 适配 → 建图、障碍物处理 |
| `/sensors/odin/odometry` | nav_msgs/Odometry | ODIN 适配 → 所选定位方案 |
| `/wheel/odometry` | nav_msgs/Odometry | 轮反馈估计 → 定位 |
| `/joint_states` | sensor_msgs/JointState | 实车轮反馈 → 模型 |
| `/odometry/filtered` | nav_msgs/Odometry | 连续局部状态 → 导航 |
| `/map` | nav_msgs/OccupancyGrid | 建图 → 探索、Nav2 |
| `NavigateToPose` action | nav2_msgs/action/NavigateToPose | 探索目标选择 → Nav2；命名空间待配置 |
| `/navigation/cmd_vel` | geometry_msgs/TwistStamped | 导航适配 → 仲裁 |
| `/teleop/cmd_vel` | geometry_msgs/TwistStamped | 遥控 → 仲裁 |
| `/drive/cmd_vel` | geometry_msgs/TwistStamped | 最终停车控制 → 差速控制器 |
| `/diagnostics` | diagnostic_msgs/DiagnosticArray | 组件 → 日志、操作者 |

`/drive/cmd_vel` 只有最终出口发布，按安装的差速控制器实际订阅名重映射。Nav2 输出类型按锁定版本核对，必要时适配；不可丢弃时间戳或将过期命令重新标新。单位为 m、rad、s；轮速目标为 rad/s。

按采集时间做 TF 查询；核对 QoS、时钟映射、数据年龄和设备复位。地图供晚加入订阅者获取完整内容；不能无记录地混用不同地图原点。实时点云只代表观测范围，不自动证明盲区可通行。

F4 协议沿用[固件约定](../firmware/README_cn.md)。上位机完成差速运动学，F4 完成轮速闭环和独立超时停车。通信、采样频率、超时、协方差、TF 发布归属均须实测确定。
