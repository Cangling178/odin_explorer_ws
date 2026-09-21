# racer_control

[English](README.md) | 简体中文

C++17 循迹、显式使能及故障锁存停车，每个驱动出口选择一套控制器：

- `lap_controller`：有序 CSV 路线、完整地图视觉对齐与轮式里程计，见[整圈运行](../../../simulation/COMPETITION_LAP_cn.md)。
- `line_controller`：已观测局部路径、有界角点停车／转向／重捕获，见[局部循线](../../../simulation/LINE_FOLLOWING_cn.md)。

`config/line_controller.yaml` 配置局部循线；整圈参数来自启动文件和节点默认值。`config/simulation_controllers.yaml` 配置仿真差速控制器与轮状态广播器。路线在 `config/competition_lap.csv`，同目录保留来源元数据。`test/` 覆盖跟踪几何与有序路线行为。
实车指令仲裁、F4 接入和标定待完成，`control_contract.template.yaml` 仅为规格表。
