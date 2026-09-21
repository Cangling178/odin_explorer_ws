# 架构与循迹设计

[English](02_architecture.md) | 简体中文

2026-09-21 按仓库现状核对。[各包实现状态](../src/README_cn.md)与下述实车目标分开记录。

## 当前仿真链路

```text
FishPoly 图像＋CameraInfo＋采集时刻 TF
    → line_perception → LineObservation＋地面 black_mask
轮式里程计＋有序 CSV 路线＋观测
    → lap_controller → TwistStamped → diff_drive_controller → 轮速 PI／Gazebo
Gazebo 真值 → 独立 Python 评测器（不反馈控制）
```

`line_perception` 将图像投影到平地米制网格并提取黑线几何。`lap_controller` 用可见骨架匹配完整地图路线，校正 odom 到路线的变换；控制选路只在当前进度附近投影，进度单调前进，从而区分交叉点的不同访问。地图对齐目前在控制器内部，尚不是独立定位节点，也没有发布 `map -> odom` TF。

Pure Pursuit 通过前视目标、按曲率限速和速度变化率限制生成指令。健康图像与里程计必须持续新鲜；无成功视觉校正时最多允许推进 0.65 m 路线距离。有序路线来自图片重建，不是实测赛道。限值和启动方法见[整圈循迹](../simulation/COMPETITION_LAP_cn.md)。

`line_controller` 是另一套局部视觉基线，在 odom 中保留已观测几何，支持单角点停车、转向和重捕获，没有完整赛道路线。每个指令出口只运行一套控制器。见[局部循线](../simulation/LINE_FOLLOWING_cn.md)。

## 实车目标与职责

| 部件 | 实车仍需接入的职责 |
| --- | --- |
| `racer_odin` | 厂商适配、图像标定、时间戳和设备健康 |
| `racer_hardware`／F4 | 通信与实测轮状态／轮速反馈闭环与独立看门狗 |
| `racer_localization` | 连续局部状态、复位语义和 TF 归属 |
| `racer_trajectory` | 有序路线元数据、预测加减速约束 |
| `racer_control`／bringup | 最终指令选择、就绪检查和部署 |
| `racer_evaluation` | 实车同步记录与独立路线关联 |

F4 接收有界的 rad/s 轮速目标，返回实测轮反馈。上位机由唯一指令选择器管理最终驱动出口，遥控、比赛和可选 Nav2 不能争用该出口。上位机卡死时 F4 必须独立停车，上电默认未使能。这些实车功能不会因对应包可构建而自动具备。

## 坐标、时序与状态

使用 SI 单位；车体 x 前、y 左、z 上，相机光学 x 右、y 下、z 前。当前模型 `base_link` 位于后轴中点；比赛评分参考点待确认。

```text
map → odom → base_link → 车轮／odin_link → 传感器坐标系
```

这是目标坐标树。仿真由差速控制器发布 `odom -> base_link`，`robot_state_publisher` 发布车内变换，话题为 `/sim/racer/tf` 和 `/sim/racer/tf_static`；没有发布全局 map/world 对齐 TF。实车每条 TF 也必须有唯一发布者，添加估计器前先核对厂商广播。

数据按采集时间对齐，上位机看门狗使用单调时钟，不给旧观测重新打时间戳。ODIN 位姿可能已使用自身 IMU，不能无相关性模型地把二者当作独立测量融合。仿真控制周期为 50 Hz，目标平台频率和端到端延迟需要实测。

整圈状态为 `DISARMED -> READY -> RUNNING -> FINISHED`，故障锁存 `STOPPED`。数据恢复不会自动重启，需要显式重新使能；重新完整跑圈须重启仿真以复位进度与初始位姿。实车标定检查和模式仲裁尚在计划中。

## 设计决策与后续算法

| 决策 | 状态／原因 |
| --- | --- |
| ADR-0001，2026-09-10：Humble 基线 | 开发机基线；锁定 Jetson 前仍需验证镜像、固件及 ARM64 兼容性 |
| ADR-0002，2026-09-10：有序路线＋视觉反馈 | 已选择；负责人允许建图、预录和相机；最短路径导航不能跳过规定分支 |
| ADR-0003，2026-09-10：自研工作空间＋厂商底层空间 | 已采用；厂商版本和许可证单独记录 |

原独立 ADR 页面合并于此，保留决策编号与状态。后续更改须记录替代决策及依据。

后续速度规划可沿路线传播加减速约束：

```text
v_curve <= sqrt(a_lateral_max / abs(kappa))
v_yaw <= omega_max / abs(kappa)
v_next^2 <= v_current^2 + 2*a_accel*ds
v_current^2 <= v_next^2 + 2*a_brake*ds
d_stop >= v*total_latency + v^2/(2*a_brake) + margin
```

这些预测限制是方案，不是已标定的实车能力。还需考虑轮速饱和、可见范围、车体扫掠，并处理零曲率。有界角速度下，运动中的机器人无法精确跟踪数学尖角，应根据允许偏差和停车规则选择可行机动。[需求](01_requirements_cn.md)与[评测](08_evaluation_cn.md)分别记录未决条件和测量原则。
