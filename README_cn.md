# Odin Explorer

[English](README.md) | 简体中文

基于 ROS 2 的实验室自主探索与建图工程：Jetson Orin Nano + ODIN1 + F4，后轮差速驱动、前被动支撑。

**这是从原工程独立克隆并精简后的开发基础，不是已完成的自主导航系统。** 当前可构建六个包并运行模型预览；厂商驱动源码另存。F4 通信、连续里程计、导航栅格、Nav2 和探索目标选择仍待实现和实车验证。

GitHub：<https://github.com/Cangling178/odin_explorer_ws>（公开仓库）。

近期顺序：人工移动建图验证 → 低速遥控底盘与停车 → 指定目标导航并建图 → 自主探索 → 已建地图内定点巡航。

## 工程结构

```text
odin_explorer_ws/
├── src/odin_explorer/
│   ├── explorer_description/   # 车体模型和 RViz 预览
│   ├── explorer_bringup/       # 统一启动入口
│   ├── explorer_hardware/      # 上位机底盘接口
│   ├── explorer_odin/          # ODIN 数据适配
│   ├── explorer_localization/  # 连续里程计与建图接入
│   └── explorer_navigation/    # 避障导航、自主探索和巡航
├── vendor_ws/src/odin_ros_driver/  # 独立厂商源码与 SDK
├── third_party/Odin-Nav-Stack/ # 官方 ROS 1 导航栈，独立子模块
├── firmware/                   # 下位机固件；目前只有协议说明
├── hardware/                   # CAD、标定、BOM 和待测规格
├── docs/                       # 架构、接口、开发与联调
│   └── planning/               # 阶段安排和人员分工
├── tools/check_workspace.py    # 最小结构与模型检查
├── .github/workflows/          # 自动构建和检查
└── build/ · install/ · log/     # 本地构建产物，不纳入 Git
```

## 使用

```bash
cd /home/cangling/odin_explorer_ws
source /opt/ros/humble/setup.bash
colcon build --base-paths src --symlink-install
source install/local_setup.bash
python3 tools/check_workspace.py
ros2 launch explorer_bringup preview.launch.py
```

模型预览不连接电机，不启动厂商设备。构建依赖与环境说明见[开发流程](docs/07_development_cn.md)。

| 入口 | 内容 |
| --- | --- |
| [源码](src/README_cn.md) | 六个保留包及实现状态 |
| [架构](docs/02_architecture_cn.md) / [接口](docs/06_interfaces_cn.md) | 建图、定位、导航和控制边界 |
| [任务分工](docs/planning/TEAM_ASSIGNMENTS_cn.md) | 三人职责、总负责人及验收阶段 |
| [实车联调](docs/09_bringup_cn.md) | 建图、底盘和导航验证 |
| [硬件](hardware/README_cn.md) / [固件](firmware/README_cn.md) | CAD、标定原件、F4 协议 |
| [厂商驱动](vendor_ws/README_cn.md) | 独立版本与构建入口 |
| [迁移记录](docs/MIGRATION_cn.md) | 保留、删除和原工程追溯 |

不包含赛道、世界生成、Gazebo 插件、黑线循迹或整圈测试。保留一个结构与模型检查工具及一个第三方源码准备脚本；实车通信及停车功能实现时再补对应测试。规格中的 `null` 尚待实测，`*.template.yaml` 不能作为运行参数。

官方导航栈已按上游目录独立接入，准备方法与 ROS 1/ROS 2 差异见[导航栈接入](third_party/README_cn.md)。运行 `bash tools/setup_odin_nav_stack.sh` 可恢复其子模块和驱动补丁；它尚未完成 F4 底盘适配。
