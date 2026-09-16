# racer_bringup

[English](README.md) | 简体中文

2026-09-16 更新：[C++ 单分支视觉循线](../../../simulation/LINE_FOLLOWING_cn.md)已实现，含显式使能与锁存停车；完整地图连续循线现已通过仿真验证；实车验收仍待完成。

启动组合与机器人运行配置。

## 状态

已提供：模型预览封装及 ros2_control 整车运动仿真 simulation.launch.py。已集成随车模拟传感器。待完成：实车传感器、底盘和比赛启动组合，以及实车就绪检查和使能；仿真循线入口已有独立使能服务。

## 职责与验收

任务编号：RACE-001。参见根目录的架构与接口文档。
本包目前通过 ament_cmake 安装资源/文档。构建成功不代表规划中的子系统已经可以运行。

## 配置

所有 `*.template.yaml` 都是规格表，不是运行中的 ROS 参数文件。实现组件时再添加运行依赖、可执行程序和经过测试的参数。厂商代码和大型录制数据不放在本包中。

## 整车运动仿真

`ros2 launch racer_bringup simulation.launch.py` 启动已有物理模型与仿真控制器，
使用 /sim/racer 命名空间。可追加 gui:=false。控制器激活失败时终止启动，
成功后等待带仿真时间戳的速度指令；不启动任何真实电机接口。
完整命令、参数和验证见[仿真说明](../../../simulation/README_cn.md#ros2_control-整车运动仿真)。

默认启用随车 Odin 数据；追加 sensors:=false 可仅测试底盘。sensor_targets:=true 添加已知测试目标。
相机需要渲染环境，即使 gui:=false；接口和验证见[随车传感器](../../../simulation/README_cn.md#随车-odin-传感器)。

追加 `course:=competition` 使用[比赛参考图赛道](../../../simulation/COMPETITION_COURSE_cn.md)，
默认 `course:=empty` 保留空场。`course_overview:=true` 添加俯视检查相机；比赛场景不能使用 sensor_targets。

## 当前实现 — 2026-09-16

完整地图使用 `competition_lap.launch.py`，局部循线实验使用 `line_following.launch.py`。两者均为仿真入口，实车启动集成仍待完成。

入口、参数与验收见[competition lap](../../../simulation/COMPETITION_LAP_cn.md).
