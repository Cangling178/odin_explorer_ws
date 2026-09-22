# ODIN 实验室导航

ODIN1 连接 Jetson，Jetson 运行重定位、实时点云处理和 Nav2，电脑通过 RViz 选择目标、设置顺序航点并显示导航状态。项目同时保留人工移动建图和机器人模型预览。

当前软件输出到 `/cmd_vel`，不包含下位机、底盘通信或定位失效停车节点。导航与避障软件链路已经在受控输入下验证；Jetson 实机、安装外参、实验室地图对齐和跨机网络仍需现场核对。

## 文档顺序

| 顺序 | 文档 | 内容 |
| --- | --- | --- |
| 01 | [项目结构与接口](docs/01_project.md) | 五个功能包、两端分工、话题和坐标树 |
| 02 | [部署与构建](docs/02_deployment.md) | 厂商补丁、Jetson 与电脑各自编译和启动 |
| 03 | [建图与地图](docs/03_mapping.md) | ODIN 点云生成二维地图、保存与坐标约定 |
| 04 | [导航与巡航](docs/04_navigation.md) | 地图对齐、安装标定、RViz 操作及操作建议 |
| 05 | [修改与验证](docs/05_changes_and_validation.md) | 文件作用、开源组件、验证结果和整理记录 |

## 目录

```text
src/odin_explorer/
├── explorer_description/    # 机器人模型与预览
├── explorer_odin/           # C++ 位姿、TF 和点云适配
├── explorer_localization/   # C++ 建图网关与 OctoMap 接入
├── explorer_navigation/     # Nav2 参数与 RViz 配置
└── explorer_bringup/        # 建图、导航和显示启动入口
vendor_ws/                  # 独立厂商驱动、SDK、配置补丁
hardware/                   # CAD、原始标定、模型说明与部件清单
data/                       # 地图、标定、设备记录和测量结果（本地数据）
docs/                       # 按使用顺序编号的中文文档
```

[源码导航](src/README.md) · [硬件与模型](hardware/README.md) · [厂商工作空间](vendor_ws/README.md)

## 运行入口

- 模型预览：`ros2 launch explorer_bringup preview.launch.py`
- 人工建图：`ros2 launch explorer_bringup mapping.launch.py floor_z:=实测地面Z`
- Jetson 导航：`ros2 launch explorer_bringup navigation_jetson.launch.py`，必须按部署文档提供地图和实测变换参数。
- 电脑交互显示：`ros2 launch explorer_bringup navigation_rviz.launch.py`

建图与已保存地图导航分别运行，不同时启动两套驱动或相互冲突的 TF 发布者。项目不保留纯模拟导航、合成测试脚本或未实现功能的空壳包。
