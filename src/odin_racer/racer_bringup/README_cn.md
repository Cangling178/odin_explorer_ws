# racer_bringup

[English](README.md) | 简体中文

预览和仿真启动组合，[构建方法](../../../docs/07_development_cn.md)。

| 启动文件 | 范围 |
| --- | --- |
| `preview.launch.py` | RViz 静态模型／TF，无驱动指令 |
| `simulation.launch.py` | ros2_control 底盘、可选随车传感器／赛道／目标 |
| `line_following.launch.py` | 局部视觉循线，显式使能 |
| `competition_lap.launch.py` | 图像地图辅助有序整圈，显式使能及终点停车 |

[仿真选项](../../../simulation/README_cn.md) · [局部循线](../../../simulation/LINE_FOLLOWING_cn.md) · [整圈运行](../../../simulation/COMPETITION_LAP_cn.md)。
尚无实车比赛启动，硬件适配、就绪检查和指令仲裁待实现。`robot_profile.template.yaml` 是规格表，不能直接部署。
