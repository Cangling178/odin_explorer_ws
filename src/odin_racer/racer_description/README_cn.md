# racer_description

[English](README.md) | 简体中文

机器人几何与坐标系定义。

## 状态

已提供：车板和 Odin1 CAD 网格、后驱动轮和前万向球、RViz 预览、已有 0.877 kg 质量
对应的估算惯性，以及独立 Odin 传感器场景。整车碰撞、接触与驱动仿真仍待完成。

## 职责与验收

任务编号：HW-001, CAL-001。参见根目录的架构与接口文档。
本包目前通过 ament_cmake 安装资源/文档。构建成功不代表规划中的子系统已经可以运行。

## 配置

所有 `*.template.yaml` 都是规格表，不是运行中的 ROS 参数文件。实现组件时再添加运行依赖、可执行程序和经过测试的参数。厂商代码和大型录制数据不放在本包中。

## CAD 预览

在工作空间根目录执行：

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-select racer_description racer_bringup
source install/local_setup.bash
ros2 launch racer_description preview.launch.py
```

不打开窗口时追加 `rviz:=false`。预览不需要 Odin 或 F4；不发布电机指令。

## Odin1

已加入官方 STEP 转换的 Odin1 外形与约 280 g 质量，安装与假设详见
[安装记录](../../../hardware/mechanical/odin1/README_cn.md)。
