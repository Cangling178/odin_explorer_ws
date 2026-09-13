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
