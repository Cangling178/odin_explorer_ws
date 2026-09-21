# 源码导航

[English](README.md) | 简体中文

十一个自研 ROS 2 包位于 `src/odin_racer/`，在工作空间根目录执行 `colcon build --base-paths src`。厂商代码隔离在 `vendor_ws/`。

| 包 | 当前实现 |
| --- | --- |
| [racer_interfaces](odin_racer/racer_interfaces/README_cn.md) | 原子 `LineObservation` 消息 |
| [racer_description](odin_racer/racer_description/README_cn.md) | 模型资源、物理／传感器／赛道生成及 FishPoly 插件 |
| [racer_perception](odin_racer/racer_perception/README_cn.md) | C++ 地面投影、黑线观测及离线图像处理 |
| [racer_control](odin_racer/racer_control/README_cn.md) | 局部和有序整圈控制、使能／停车、仿真底盘设置 |
| [racer_bringup](odin_racer/racer_bringup/README_cn.md) | 预览、底盘仿真、局部循线和整圈启动 |
| [racer_hardware](odin_racer/racer_hardware/README_cn.md) | 仅规格，尚无 F4 通信或真实轮反馈 |
| [racer_odin](odin_racer/racer_odin/README_cn.md) | 仅规格，尚无实机适配 |
| [racer_localization](odin_racer/racer_localization/README_cn.md) | 仅规格，当前地图对齐在整圈控制器中 |
| [racer_trajectory](odin_racer/racer_trajectory/README_cn.md) | 仅规格，当前路线进度／曲率限速在整圈控制器中 |
| [racer_evaluation](odin_racer/racer_evaluation/README_cn.md) | 仅规格，可运行独立评测在 `tools/` |
| [racer_navigation](odin_racer/racer_navigation/README_cn.md) | 可选后续导航 |

运行[完整整圈](../simulation/COMPETITION_LAP_cn.md)或[局部循线](../simulation/LINE_FOLLOWING_cn.md)，均为仿真入口，不是实车部署。
[架构](../docs/02_architecture_cn.md)区分现有数据流与未来职责，[开发流程](../docs/07_development_cn.md)定义配置和测试规范。保留 CMake 安装所需包 README，通过链接引用状态与命令，避免重复。
