# 自研 ROS 2 包

[English](README.md) | 简体中文

C++ 运行入口：[line_following.launch.py](odin_racer/racer_bringup/launch/line_following.launch.py)；[实现与验证](../simulation/LINE_FOLLOWING_cn.md)。
主要功能在 `src/odin_racer/` 内按包实现，目前没有统一的 `main.py` 或比赛启动程序。下表中的“规划中的子系统”只有文档和配置规格，没有算法节点。

| 包 | 职责 | 状态 |
| --- | --- | --- |
| [racer_interfaces](odin_racer/racer_interfaces/README_cn.md) | 图像健康、中心线和角点/出口的原子消息 | LineObservation v0.1.0 |
| [racer_description](odin_racer/racer_description/README_cn.md) | 机器人几何与坐标系定义 | 预览、物理模型、随车传感器与仿真生成 |
| [racer_hardware](odin_racer/racer_hardware/README_cn.md) | 电机通信、车轮反馈与驱动集成 | 规划中的子系统 |
| [racer_odin](odin_racer/racer_odin/README_cn.md) | ODIN1 厂商适配与时间戳/坐标约定 | 规划中的子系统 |
| [racer_localization](odin_racer/racer_localization/README_cn.md) | 连续车体状态与全局对齐 | 规划中的子系统 |
| [racer_perception](odin_racer/racer_perception/README_cn.md) | 局部视觉黑线观测与候选分支 | C++ 黑线检测、FishPoly 地面投影与无效观测输出 |
| [racer_trajectory](odin_racer/racer_trajectory/README_cn.md) | 有序路线进度与可行速度曲线 | 规划中的子系统 |
| [racer_control](odin_racer/racer_control/README_cn.md) | 路径跟踪、运行状态与指令控制 | C++ 自适应 Pure Pursuit、有界单角转向状态与锁存停车；完整比赛状态待实现 |
| [racer_navigation](odin_racer/racer_navigation/README_cn.md) | 可选 Nav2 集成 | 规划中的子系统 |
| [racer_bringup](odin_racer/racer_bringup/README_cn.md) | 启动组合与机器人运行配置 | 预览及整车运动仿真 |
| [racer_evaluation](odin_racer/racer_evaluation/README_cn.md) | 比赛记录与指标导出集成 | 规划中的子系统 |

十一个包都可由 ament_cmake 发现并构建；racer_interfaces 生成 ROS 消息。description/bringup 已有预览、独立传感器、落地接触和整车运动仿真启动实现。在工作空间根目录运行 `colcon build --base-paths src`。厂商代码隔离在 `vendor_ws/`。

项目维护者地址在负责人指定联系地址前，故意使用不可投递的占位符；它不用于 Git 提交身份。

## 已有程序入口

| 文件 | 功能 |
| --- | --- |
| [simulation.launch.py](odin_racer/racer_bringup/launch/simulation.launch.py) | ros2_control 整车运动仿真 |
| [course_world.py](odin_racer/racer_description/racer_description/course_world.py) | 比赛参考图赛道与可选俯视相机，通过 course:=competition 加载 |
| [validate_competition_course.py](../tools/validate_competition_course.py) | 赛道图像投影、传感器与短距离运动验证 |
| [preview.launch.py](odin_racer/racer_bringup/launch/preview.launch.py) | 用户启动入口，组合模型预览 |
| [模型预览实现](odin_racer/racer_description/launch/preview.launch.py) | 发布模型与静止关节状态 |
| [robot.urdf.xacro](odin_racer/racer_description/urdf/robot.urdf.xacro) | CAD 与简化装配、估算惯性、碰撞及可选仿真控制接口 |
| [evaluate_run.py](../tools/evaluate_run.py) | 已关联误差样本的离线评测 |
| [check_workspace.py](../tools/check_workspace.py) | 语法、文档链接和包结构检查 |

比赛状态、模式选择和最终指令仲裁属于 `racer_control`；`racer_navigation` 只负责可选 Nav2 集成，`racer_bringup` 负责启动组合。感知输出黑线观测，`racer_trajectory` 维护有序路线进度并规划速度，`racer_control` 将参考轨迹转成运动指令。详见[系统架构](../docs/02_architecture_cn.md)。
