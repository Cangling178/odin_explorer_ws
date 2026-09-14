# racer_description

[English](README.md) | 简体中文

机器人几何与坐标系定义。

## 状态

已提供：车板和 Odin1 CAD 网格、后驱动轮及前万向球、RViz 预览、已有 0.877 kg
质量小计对应的估算惯性，以及基本几何碰撞体。水平车板离地 62 mm 是用户指定值。
整车落地接触与 ros2_control 基础运动测试已通过；实测标定仍待完成。

已提供随车 Odin 传感器和[比赛参考图赛道](../../../simulation/COMPETITION_COURSE_cn.md)，
包含带比例与来源记录的纹理/网格和场景生成器；比赛尺寸沿用图注，尚未实测标定。

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

## 碰撞几何

展开模型后，16 个实体/外观 link 上共有 25 个基本几何碰撞体：

- 车板：247.416×220×3.5 mm 底板盒体，以及单独包围 CAD 上部凸起的盒体。
  边界从已有 STL 提取；保守填充孔洞及凸起之间的空隙，狭小间隙和自碰撞检查需要更细的形状。
- 轮胎：与外观半径、宽度相同的圆柱，轴向为 Y。
- 电机、编码器盖、支架、输出轴：与已有简化外观相同的盒体/圆柱；支架保留两块板的 L 形。
- 铜柱：六角柱的外接圆柱，半径为对边宽度除以 sqrt(3)，从安装面向下延伸。
- 万向球：每套分别有球体和壳体圆柱；安装法兰因尺寸不完整继续省略。
- Odin1：46.4×100×62 mm 包络盒，在 odin_link 中心为 (-3.6, 0, 31) mm，
  包含 CAD 主体和接头；与仅用于惯性估算的主体盒不同。

本次添加未改变质量、惯性、外观几何或关节拓扑。输出轴/轮毂、球/壳的内部重叠属于
装配近似，未启用自碰撞。源 URDF 保留零件级结构；专用接触场景生成器将固定部件合并，
保留无质量部件的碰撞体，并按 ground_contact.yaml 配置接触。前球采用低摩擦滑动近似，
并非真实滚动支撑。

检查记录（2026-09-13）：源码 Xacro 展开及包构建通过。碰撞体尺寸均为正，所有外观
link 均有碰撞体；两个轮胎和两个球的最低点均为 base_link 下 Z=-0.03325 m，
没有碰撞体低于该平面。9 个惯性 link 质量小计仍为 0.877 kg。这些是几何检查，
不是 Gazebo 落地、滚动或运动试验。

## 动态接触场景

构建后使用 `ros2 launch racer_description ground_contact.launch.py`；无窗口时追加
`gui:=false`。生成器从当前 Xacro 创建三个刚体，总质量仍为 0.877 kg，保留全部碰撞体。
该场景只验证重力、支撑和静置，不接收驱动指令，不发布车辆 TF 或 Odin 传感器数据。
参数、隔离环境启动命令和已通过的落地测试见[仿真说明](../../../simulation/README_cn.md#整车地面接触测试)。

运动场景由 `racer_bringup simulation.launch.py` 启动，通过可选 sim_control Xacro 参数声明控制接口；使用已有接触生成器并加入 Gazebo 控制插件。详见[运动仿真](../../../simulation/README_cn.md#ros2_control-整车运动仿真)。

随车图像、点云和 IMU 已集成，台架与整车共用 config/odin_sensors.yaml，安装位姿来自 Xacro。见[随车传感器](../../../simulation/README_cn.md#随车-odin-传感器)。
