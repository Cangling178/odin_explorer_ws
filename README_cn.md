# Odin Racer

[English](README.md) | 简体中文

基于 ROS 2 的四轮循迹小车项目：Jetson Orin Nano + ODIN1 + F4 下位机。目标是不使用专用循迹模块，准确、快速地沿比赛标线行驶。

**当前是工程骨架。可运行模型预览和离线评测，尚不能自主驱动实车。**

## 从哪里开始

| 要做什么 | 入口 |
| --- | --- |
| 找主要代码、了解模块职责 | [源码导航](src/README_cn.md) → `src/odin_racer/` |
| 构建工程、启动模型预览 | [开发流程](docs/07_development_cn.md) |
| 了解设计和接口 | [系统架构](docs/02_architecture_cn.md)、[接口约定](docs/06_interfaces_cn.md) |
| 查看下一步任务 | [项目计划](docs/planning/README_cn.md) |
| 查找其他说明 | [文档导航](docs/README_cn.md) |

## 工作空间结构

| 目录 | 内容 |
| --- | --- |
| `src/odin_racer/` | 自研 ROS 2 包；主要功能在这里实现 |
| `firmware/` | F4 下位机固件与协议，目前仅有说明 |
| `hardware/` | 硬件清单、实测尺寸、接线和标定 |
| `tracks/` | 赛道参考图片与待填写的路线数据 |
| `tools/`、`tests/` | 可运行的离线评测器、仓库检查器及评测测试 |
| `experiments/` | 实验记录、结果表和合成示例 |
| `data/` | 大型本地采集数据和生成结果，不纳入 Git |
| `vendor_ws/` | 独立厂商驱动工作空间，目前未导入驱动 |
| `simulation/` | 仿真预留目录，目前只有计划说明 |
| `docs/` | 技术文档、协作规范、更新日志；规划集中在 `planning/` |

根目录也是 colcon 工作空间根目录。`build/`、`install/`、`log/` 是自动生成的构建产物。`*.template.yaml` 是待填写的规格表，不能直接作为 ROS 运行参数。

## 先运行离线示例

在工作空间根目录执行，无需连接机器人：

```bash
python3 tools/evaluate_run.py experiments/examples/synthetic_samples.csv \
  --metadata experiments/examples/synthetic_run.json
```

输出来自合成数据，不代表实车性能。构建、预览和完整检查命令统一见[开发流程](docs/07_development_cn.md)。

接入实车前，先填写[硬件清单](hardware/bom.csv)和[机器人参数表](hardware/robot_spec.template.yaml)，再按[项目计划](docs/planning/README_cn.md)推进。底盘已确认是后双驱动轮、前双被动万向轮；具体 F4 板、电机和编码器参数仍待核实。

许可见 [LICENSE](LICENSE)，资料来源见[参考资料](docs/REFERENCES_cn.md)。
