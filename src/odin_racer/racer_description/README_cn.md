# racer_description

[English](README.md) | 简体中文

机器人 Xacro／CAD 资源、坐标几何、仿真世界生成器及 FishPoly Gazebo 相机插件。已有质量为 0.877 kg 小计，固定部件合并为三个动态刚体时保留 25 个基本碰撞体。

| 位置 | 职责 |
| --- | --- |
| `urdf/`、`meshes/` | 装配、估算惯性／碰撞和来源网格 |
| `racer_description/contact_world.py`、`drive_world.py` | 被动接触和 ros2_control 场景 |
| `racer_description/sensor_world.py`、`fishpoly.py` | 共用传感器生成及投影模型 |
| `racer_description/course_world.py`、`course_texture.py` | 图片比赛地图和独立黑线场景 |
| `plugins/odin_fishpoly_camera.cpp` | FishPoly 渲染及 ROS 图像／标定发布 |
| `config/` | 接触、执行器、传感器和赛道设置 |

[仿真命令](../../../simulation/README_cn.md) · [模型假设](../../../simulation/MODEL_cn.md) · [底盘来源](../../../hardware/mechanical/chassis_plate/README_cn.md) · [ODIN 来源](../../../hardware/mechanical/odin1/README_cn.md)。
模型预览使用 `racer_bringup preview.launch.py`，物理参数和安装尚未对照实车标定。
