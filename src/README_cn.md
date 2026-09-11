# 自研 ROS 2 包

[English](README.md) | 简体中文

| 包 | 职责 | 状态 |
| --- | --- | --- |
| `racer_description` | 机器人几何与坐标系定义 | 资源预览 |
| `racer_hardware` | 电机通信、车轮反馈与驱动集成 | 规划中的子系统 |
| `racer_odin` | ODIN1 厂商适配与时间戳/坐标约定 | 规划中的子系统 |
| `racer_localization` | 连续车体状态与全局对齐 | 规划中的子系统 |
| `racer_perception` | 局部视觉黑线观测与候选分支 | 规划中的子系统 |
| `racer_trajectory` | 有序路线进度与可行速度曲线 | 规划中的子系统 |
| `racer_control` | 路径跟踪、运行状态与指令控制 | 规划中的子系统 |
| `racer_navigation` | 可选 Nav2 集成 | 规划中的子系统 |
| `racer_bringup` | 启动组合与机器人运行配置 | 资源预览 |
| `racer_evaluation` | 比赛记录与指标导出集成 | 规划中的子系统 |

十个包都可由 ament_cmake 发现并构建资源。只有 description/bringup 预览有启动实现。在工作空间根目录运行 `colcon build --base-paths src`。厂商代码隔离在 `vendor_ws/`。

项目维护者地址在负责人指定联系地址前，故意使用不可投递的占位符；它不用于 Git 提交身份。
