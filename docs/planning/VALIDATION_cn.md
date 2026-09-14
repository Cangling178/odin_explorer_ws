# 基础工程验证

[English](VALIDATION.md) | 简体中文

日期：2026-09-10。平台：现有 x86_64 工作站、Ubuntu 22.04 用户态、ROS 2 Humble、Python 3.10.12。这不是 Jetson 或实车验证。

| 检查 | 结果 | 范围 |
| --- | --- | --- |
| `python3 tools/check_workspace.py` | 通过 | 十个包清单、Python/YAML 语法、英文原创文本和本地 Markdown 链接 |
| `python3 -m unittest discover -s tests -v` | 七项测试通过 | 时间加权、无效数据、空洞、完赛规则和错误输入 |
| README 中的合成评测命令 | 通过 | 合成经过时间 0.4 s，有效时间覆盖率 75%，RMS 约 0.02160 m |
| `colcon list --base-paths src` | 发现十个包 | 仅自研资源 |
| `colcon build --symlink-install --base-paths src --executor sequential` | 十个包构建成功 | 资源安装，不代表自主行驶已实现 |
| `ros2 launch racer_bringup preview.launch.py --show-args` | 通过 | 已安装启动文件加载和参数解析 |
| 已安装 Xacro 展开和结构检查 | 通过 | 六个 link、五个 joint，恰好两个驱动关节和两个万向轮 link，无执行器插件 |
| `git diff --cached --check` | 基础提交时通过 | 空白格式一致性 |
| 生成文件/厂商代码/采集数据忽略检查 | 通过 | 构建、安装、日志、厂商源码和录包路径被排除 |

沙箱内的 colcon 在 CMake 配置完成后停滞；沙箱外的限时构建约 5.2 秒完成十个包。这属于执行环境限制，无需安装额外依赖。

没有测试实际运行的 ROS 预览节点、RViz 窗口、相机、电机控制器、Jetson 目标板、固件刷写、物理仿真或自主行驶。给定赛道图片原样保留，实测中心线坐标仍为空。初始本地 Git 仓库分支为 `main`，没有远程仓库。交付源码中不包含构建产物，应在最终位置按文档命令重新构建。

## 中文文档更新

日期：2026-09-11。新增 51 份 `_cn.md` 对应文档和双向语言链接。翻译覆盖、本地链接、章节/表格数量一致性、可执行命令原样保留，以及 Issue 模板前置元数据字段检查均通过。更新后的结构检查器仅允许 `_cn.md` 文档包含中文，并要求中英文成对且带语言导航。十个 ROS 包重新构建成功，已逐一比较安装后的中文 README 与源文件。未修改机器人运行逻辑。

## ros2_control 基础运动验证 — 2026-09-13

本机 Gazebo Classic 11.10.2 / ROS 2 Humble；不是 F4 或 Jetson 实车验收。
已有 0.877 kg 质量与 25 个碰撞体保留；两个轮速度接口由差速控制器驱动，轮式里程计
与 Gazebo 真值分开。构建通过，14 项单元测试通过；前后直行、左右原地转向、圆弧、
超限输入、零速停车、断流与过期指令测试通过。速度/加速度/力矩限制及轮状态、TF 检查通过。
参数、有效轮距 1.10 的仿真标定依据与可复现命令见[仿真说明](../../simulation/README_cn.md#ros2_control-整车运动仿真)。
`tools/validate_sim_drive.py` 输出完整指标。比赛模式仲裁、实车通信、随车感知仍未实现。
提交整理时已修正二进制/厂商目录扫描并补齐临时文档语言配对，全量仓库检查通过。

## 随车 Odin 传感器验证 — 2026-09-13

整车默认集成图像、CameraInfo、点云和 IMU，参数与独立台架共用，外参由 Xacro 固定关节链生成。
本机十个包构建成功，18 项单元测试通过；新增测试覆盖旋转安装与相机轴转换、台架/整车一致性、
关闭传感器时的物理模型保持，以及非法参数和活动关节挂载拒绝。

`tools/validate_sim_sensors.py` 在新启动的已知目标场景通过静止、前进、左右转向、加减速及
投影/点云/IMU/TF/时间戳/频率检查；结果位于本地 `data/generated/sim_sensors_validation.json`。
随后 `tools/validate_sim_drive.py` 六项运动及停车/限幅回归通过，结果为
`data/generated/sim_drive_with_sensors_validation.json`。独立台架入口复测收到全部四类消息，
1600×1296 图像、非空点云与静止 IMU Z=9.81 m/s²；本地记录为 `data/generated/odin_bench_regression.json`。
这些生成文件不纳入 Git，关键参数、指标和复现命令见[随车传感器说明](../../simulation/README_cn.md#随车-odin-传感器)。

实时因子约 0.62，仍需性能优化；完整黑线视野、自遮挡测试矩阵、算法闭环及实车一致性未验收。

## 比赛参考图赛道 — 2026-09-13，提交整理于 2026-09-14

2.00×1.50 m 图片复刻赛道已接入整车场景，保留原有车辆质量、碰撞和接触参数。
新增四项结构测试覆盖赛道物理隔离、资源比例与来源哈希、无随车传感器/可选俯视相机组合、
以及不兼容场景参数的拒绝；总计 22 项单元测试通过。

`tools/validate_competition_course.py` 实际运行通过：前进约 0.116 m 后停车，俯视黑线
IoU 约 0.853/0.851，随车投影 IoU 约 0.926/0.933；点云地面、静止 IMU、时间戳及频率检查通过。
本次图像/点云约 10 Hz、俯视图约 2 Hz，IMU 实收约 333 Hz（配置目标 400 Hz），实时因子约 0.84。
数据按仿真时间统计，仅对应本机与当次负载。

本地报告与截图为 `data/generated/competition_course_validation*`，不纳入 Git；
关键指标、检查阈值、限制和复现命令见[比赛赛道说明](../../simulation/COMPETITION_COURSE_cn.md)。
原图不变，实测路线模板仍为空，正式起点/方向/分支顺序尚未确认。此次不包含黑线检测或自主循线算法。

2026-09-14 提交前复核：仓库结构/语言配对/本地链接检查、22 项单元测试和
`colcon build --base-paths src` 的十个自研包构建全部通过；同步 README、架构、开发流程、计划和变更记录。
