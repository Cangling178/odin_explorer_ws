# Odin Racer

[English](README.md) | 简体中文

基于 ROS 2 的循迹小车：Jetson Orin Nano＋ODIN1＋F4，后轮双电机差速驱动、前轮为被动支撑。

**C++ 感知与有序路线控制已完成仿真整圈；实车通信、Jetson 部署、标定及整车接入尚未完成。**
Gazebo 赛道默认 4×3 m、约 21.2 mm 线宽。已有记录：0.05 m/s 独立启动 3/3 次通过，0.10 m/s 单次通过；默认仍为 0.05 m/s。具体指标与适用范围见[整圈验收](experiments/competition_lap/RESULTS_cn.md)。

## 从这里开始

| 要做什么 | 文档 |
| --- | --- |
| 构建、检查或参与开发 | [开发流程](docs/07_development_cn.md) |
| 运行完整仿真整圈 | [整圈循迹](simulation/COMPETITION_LAP_cn.md) |
| 运行部件或局部循线仿真 | [仿真入口](simulation/README_cn.md) |
| 理解代码和数据流 | [源码导航](src/README_cn.md)、[架构](docs/02_architecture_cn.md)、[接口](docs/06_interfaces_cn.md) |
| 接入实车 | [联调与标定](docs/09_bringup_cn.md)、[硬件资料](hardware/README_cn.md) |
| 查看剩余工作 | [项目计划](docs/planning/README_cn.md)、[需求](docs/01_requirements_cn.md) |
| 查找测试依据 | [验证索引](experiments/README_cn.md) |

## 工作空间

`src/odin_racer/` 包含十一个自研 ROS 包，`tools/` 与 `tests/` 保存资源生成及独立验证工具。
`hardware/`、`tracks/`、`firmware/` 分别保存硬件事实、赛道来源与 F4 协议提案；`vendor_ws/` 隔离厂商驱动。
`data/generated/`、`build/`、`install/`、`log/` 是本地数据或构建产物，不纳入 Git。
`*.template.yaml` 是未填写完整的规格表，不能直接作为 ROS 运行参数。

每个主题保留一个技术入口及中英文对应版。历史验收保留原版本与日期；更新当前状态不表示重新跑过历史测试。
[变更记录](docs/CHANGELOG_cn.md) · [参考资料](docs/REFERENCES_cn.md) · [许可](LICENSE)
