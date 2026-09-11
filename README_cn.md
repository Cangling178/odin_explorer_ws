# Odin Racer

[English](README.md) | 简体中文

这是一个基于 ROS 2 的四轮小车工作空间，使用 Jetson Orin Nano 和留形科技（Manifold）的 ODIN1 模组。首要目标是：**不使用专用循迹模块，准确、快速地沿比赛标线行驶**。

**当前阶段：项目基础工程，尚不能直接驱动实车。** 已有底盘采用两只后轮分别由电机驱动、两只前轮为被动万向轮的结构，并配有独立的 F4 下位机。具体开发板、电机和编码器参数尚未确认。传感器适配、电机驱动、感知和自主控制仍待实现。

## 从这里开始

1. 阅读[需求文档](docs/01_requirements_cn.md)，确认剩余的评分规则和路线细节。
2. 填写[硬件清单](hardware/bom.csv)和[机器人参数表](hardware/robot_spec.template.yaml)。
3. 阅读[系统架构](docs/02_architecture_cn.md)和[赛道方案](docs/05_course_strategy_cn.md)。
4. 按[开发流程](docs/07_development_cn.md)构建基础工程。
5. 依据[里程碑](management/ROADMAP_cn.md)和[任务清单](management/BACKLOG_cn.md)推进开发。

## 设计重点

- 利用相机局部观测测量相对黑线的误差。项目负责人已允许使用相机，但仍需实测 ODIN1 的地面可见范围。
- 利用轮速反馈和 ODIN1 定位维持运动连续性，并提供路线位置背景。
- 跟踪**有顺序的路线**，在交叉点选择正确分支。
- 先建立可重复的精度表现，再逐步提高速度。
- 将通用 Nav2 导航作为后续可选能力。

建议的软件基线是 Ubuntu 22.04 / ROS 2 Humble，以及兼容的 JetPack 6.x。锁定版本前，需要同时确认实际 Jetson 系统镜像、驱动和固件。参见[平台决策](docs/adr/0001_platform_cn.md)。

## 工作空间结构

```text
odin_racer_ws/
  src/odin_racer/       十个自研 ROS 2 包
  vendor_ws/           后续独立构建 ODIN1 厂商驱动的底层工作空间
  docs/                需求、设计、接口、操作流程和决策文档
  hardware/            硬件清单、尺寸、电气和标定记录
  firmware/            后续下位机固件与通信协议说明
  tracks/              参考图片、实测路线和赛道元数据
  simulation/          后续仿真场景与验收条件
  tools/               离线评测和仓库检查工具
  tests/               离线评测工具的回归测试
  experiments/         实验清单、流程和简要结果表
  data/                不纳入 Git 的录包、录像、地图和生成结果
  management/          路线图、任务、风险和决策记录
  .github/             可选的 Issue/PR 模板和基础持续集成检查
```

仓库根目录同时也是 colcon 工作空间根目录。`build/`、`install/` 和 `log/` 是构建产物，不纳入 Git。参见[验证记录](management/VALIDATION_cn.md)和[各包职责](src/README_cn.md)。以 `*.template.yaml` 命名的文件是设计规格模板，不是可直接运行的 ROS 参数文件。

## 目前可用的功能

```bash
cd ~/odin_racer_ws
python3 tools/check_workspace.py
python3 -m unittest discover -s tests -v
python3 tools/evaluate_run.py experiments/examples/synthetic_samples.csv \
  --metadata experiments/examples/synthetic_run.json
source /opt/ros/humble/setup.bash
colcon build --symlink-install --base-paths src
source install/local_setup.bash
ros2 launch racer_bringup preview.launch.py
```

预览会发布示意机器人模型和静止关节状态，不连接硬件。需要查看画面时可单独启动 RViz。接入实车前必须把预览尺寸替换成实测几何参数。评测示例是合成数据，结果不代表机器人实际表现。

## 实现状态

| 能力 | 状态 |
| --- | --- |
| 英文文档、对应中文版和本地项目管理 | 已包含 |
| ROS 包发现、资源构建和模型预览 | 已包含 |
| 基于校验后的 CSV 和元数据生成离线误差/时间报告 | 已包含 |
| ODIN1 驱动和标定适配层 | 已规划；尚未下载厂商代码 |
| 电机接口、看门狗和编码器里程计 | 已规划 |
| 视觉黑线提取和交叉点关联 | 已规划 |
| 轨迹生成、速度曲线和跟踪控制器 | 已规划 |
| 比赛模式启动和实车验证 | 已规划 |
| Nav2 集成和物理仿真 | 已规划 |

这是本地仓库，尚未配置远程托管或发布。原始工程的许可由项目负责人决定，目前保留相关权利，见 [LICENSE](LICENSE)。资料来源与上游项目的适用边界见[参考资料](docs/REFERENCES_cn.md)。
