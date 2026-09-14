# racer_perception

[English](README.md) | 简体中文

局部视觉黑线检测与地面中心线。

已实现 C++17 节点 `line_perception`，算法和 ROS 接口分离。运行参数为 `config/line_perception.yaml`；
`*.template.yaml` 仍是设计规格表，不能作为运行参数。

实现、话题、参数、启动与测试命令见[低速视觉循线](../../../simulation/LINE_FOLLOWING_cn.md)。
完整比赛路线、交叉点选择、实车标定及 F4 接入仍待完成。
