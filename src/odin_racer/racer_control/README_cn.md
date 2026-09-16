# racer_control

[English](README.md) | 简体中文

低速路径跟踪、显式使能与指令失效停车。

已实现 C++17 节点 `line_controller`，算法和 ROS 接口分离。运行参数为 `config/line_controller.yaml`；
`*.template.yaml` 仍是设计规格表，不能作为运行参数。

实现、话题、参数、启动与测试命令见[低速视觉循线](../../../simulation/LINE_FOLLOWING_cn.md)。
完整有序路线与交叉点选择已在仿真整圈控制器中实现；实车标定及 F4 接入仍待完成。

已有 `config/simulation_controllers.yaml` 保留 ros2_control 差速底盘、轮状态广播器与底层指令超时。

## 当前实现 — 2026-09-16

`lap_controller` 是当前完整地图连续跑圈控制器，包含有序进度、全图视觉校正、轮式里程计、显式使能和故障锁存停车。`line_controller` 保留用于局部视觉/角点实验；启动时二者选一。

入口、参数与验收见[competition lap](../../../simulation/COMPETITION_LAP_cn.md).
