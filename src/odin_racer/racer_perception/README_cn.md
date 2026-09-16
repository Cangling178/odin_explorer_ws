# racer_perception

[English](README.md) | 简体中文

局部视觉黑线检测与地面中心线。

已实现 C++17 节点 `line_perception`，算法和 ROS 接口分离。运行参数为 `config/line_perception.yaml`；
`*.template.yaml` 仍是设计规格表，不能作为运行参数。

实现、话题、参数、启动与测试命令见[低速视觉循线](../../../simulation/LINE_FOLLOWING_cn.md)。
完整有序路线与交叉点选择已在仿真整圈控制器中实现；实车标定及 F4 接入仍待完成。

## 当前实现 — 2026-09-16

同一 C++ 感知节点服务于两种控制器。整圈控制器使用地面黑线掩膜进行地图对齐，并通过 LineObservation 检查图像健康。

入口、参数与验收见[competition lap](../../../simulation/COMPETITION_LAP_cn.md).
