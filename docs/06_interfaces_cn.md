# 当前接口与实车提案

[English](06_interfaces.md) | 简体中文

独立场景使用 `racer_interfaces/LineObservation` v0.1.0，通过 `/sim/racer/line/observation` 将路径、
图像健康、置信度、角点和出口证据与 `path.header` 中的采集时间原子关联；`local_path` 保留为调试视图。
详见[消息约定](../src/odin_racer/racer_interfaces/README_cn.md)。

以下是自研模块的设计约定。实车适配仍待实现；仿真循线接口见上方入口，这些名称不是对厂商驱动当前 API 的声明。优先使用标准 ROS 消息；只有标准消息不能明确表达分支/进度语义时才添加自定义消息，并先记录版本。

## 当前仿真

`lap_controller` 使用 `observation`、`black_mask`、轮式 `odom` 和采集时刻 TF，从 CSV 加载路线；发布 `cmd_vel`、`tracking_status`、`control_debug`，用 `~/enable`（`SetBool`）显式使能。实际命名与重映射见[整圈运行](../simulation/COMPETITION_LAP_cn.md)，下表实车话题仍是提案。

## 拟定实车接口

| 话题 | 类型 | 发布者 → 使用者 | 约定 |
| --- | --- | --- | --- |
| `/sensors/odin/image_raw` | sensor_msgs/msg/Image | ODIN 适配层 → 感知 | 采集时间、光学坐标系 |
| `/sensors/odin/camera_info` | sensor_msgs/msg/CameraInfo | ODIN 适配层 → 感知 | 仅在正确转换为受支持的相机模型后发布 |
| `/sensors/odin/imu` | sensor_msgs/msg/Imu | ODIN 适配层 → 所选估计器 | 已核对单位和协方差 |
| `/sensors/odin/points` | sensor_msgs/msg/PointCloud2 | ODIN 适配层 → 可选环境检查 | 米制坐标系、限定数据年龄 |
| `/sensors/odin/odometry` | nav_msgs/msg/Odometry | ODIN 适配层 → 定位 | 真实位姿参考系和复位含义 |
| `/wheel/odometry` | nav_msgs/msg/Odometry | 硬件 → 定位 | 实测编码器反馈、车体速度 |
| `/joint_states` | sensor_msgs/msg/JointState | 硬件 → 模型 | 一致车轮顺序、SI 单位 |
| `/odometry/filtered` | nav_msgs/msg/Odometry | 定位 → 跟踪 | 连续局部位姿、质量依据 |
| `/track/local_path` | nav_msgs/msg/Path | 感知 → 轨迹 | 所选候选的有序点；不能暗含未说明的分支选择 |
| `/race/reference_path` | nav_msgs/msg/Path | 轨迹 → 控制器 | 明确坐标系；路线元数据另存 |
| `/race/cmd_vel` | geometry_msgs/msg/TwistStamped | 控制器 → 指令选择器 | 带时效检查的车体目标 |
| `/teleop/cmd_vel` | geometry_msgs/msg/TwistStamped | 遥控 → 指令选择器 | 仅在该模式选中时使用 |
| `/navigation/cmd_vel` | geometry_msgs/msg/TwistStamped | 导航适配层 → 选择器 | 显式转换已装 Nav2 的输出 |
| `/drive/cmd_vel` | geometry_msgs/msg/TwistStamped | 最终停止控制 → 硬件 | 只有最终指令出口可以发布 |
| `/diagnostics` | diagnostic_msgs/msg/DiagnosticArray | 各组件 → 操作者/日志 | 设备健康信息；不是电机停止机制 |

比赛进度需要路线 ID/哈希、分段 ID、有方向的进度 `s`、检查点状态、横向误差、航向误差、置信度、有效性和源时间戳。仅靠 `nav_msgs/Path` 没有分段 ID 或速度曲线；未来轨迹 API 需要用定义清楚的消息或同步约定另行传输。拟定结构见 `racer_trajectory/config/route_contract.template.yaml`。

## 时间与 QoS

核对发布者兼容性后，才能选择 best-effort 传感器 QoS；限制队列长度，避免处理过期图像。指令使用可靠的小队列，并明确检查数据年龄。拒绝非有限数值、过期/未来时间戳和不可信的坐标系 ID。看门狗时长使用单调时钟，数据对齐使用 ROS 时间戳；回放时各节点一致使用 `/clock`。

不能无记录地将带时间戳指令转换为不带时间戳的指令，从而丢失时效检查。差速控制器应重映射到其真实命名空间下的指令话题，并明确配置 `use_stamped_vel`。预览不包含指令发布者。

## 下位机通信

F4 下位机已确认；Jetson 到 F4 使用 CAN 还是串口仍未决定。最终协议需要版本、序列号、有界的左右轮 rad/s 目标、校验和/错误检测、状态、反馈、心跳和明确使能状态。参见[协议计划](../firmware/README_cn.md)。
