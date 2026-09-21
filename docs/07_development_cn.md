# 开发与仓库规范

[English](07_development.md) | 简体中文

本机开发基线为 Ubuntu 22.04／ROS 2 Humble，目标 Jetson 组合尚未验收。在干净的 ROS 2 终端、工作空间根目录执行命令。

## 构建与预览

```bash
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src --rosdistro humble -r -y
colcon build --symlink-install --base-paths src
source install/local_setup.bash
ros2 launch racer_bringup preview.launch.py
```

`rosdep` 会安装依赖，需已完成 rosdep 初始化。预览使用 RViz、robot_state_publisher、joint_state_publisher 和 xacro；`rviz:=false` 关闭窗口。预览不发布电机指令。仿真运行入口见[仿真说明](../simulation/README_cn.md)。

接入厂商硬件时，先构建并加载[厂商底层工作空间](../vendor_ws/README_cn.md)，再构建、加载自研叠加层。不要混用 ROS 发行版。`vendor_ws/COLCON_IGNORE` 与 `--base-paths src` 隔离厂商包。

## 检查

```bash
python3 tools/check_workspace.py
python3 -m unittest discover -s tests -v
colcon test --base-paths src --packages-select racer_perception racer_control
colcon test-result --verbose
git diff --check
```

Python 依赖见 `tools/requirements-dev.txt`，图像测试还使用 OpenCV，几何测试使用 xacro；独立 CSV 评测器使用标准库。CI 执行仓库检查、Python 测试、构建及 C++ 测试，不运行需要渲染的 Gazebo 场景或实车。

构建并加载工作空间后，可执行合成 ROS 控制器检查：

```bash
python3 tools/validate_line_controller.py
python3 tools/validate_arming_clock.py
python3 tools/validate_lap_controller.py
```

这些检查使用隔离 domain 和合成输入。动态验证需要渲染环境，命令见[整圈](../simulation/COMPETITION_LAP_cn.md)及[局部循线](../simulation/LINE_FOLLOWING_cn.md)。验证范围和证据集中在[实验索引](../experiments/README_cn.md)，各使用文档不重复维护测试总数。

## 文件归属与协作

- 代码与运行配置放在 `src/odin_racer/` 所属包；硬件事实放在 `hardware/`，赛道事实放在 `tracks/`，实验摘要放在 `experiments/`。
- `*.template.yaml` 是规格表。未知事实保持未填，实现组件时再建立经过验证的运行参数；分别记录几何、路线和调参版本。
- 厂商源码、SDK 二进制、录包、凭据和生成报告不纳入 Git；记录上游版本／许可、数据路径／哈希。本地原始证据位于 `data/generated/`，不作为源码说明文件混管。
- 保留英文和对应 `_cn.md`，双向链接，同步技术含义。标识符、程序面向用户的字符串和提交说明使用英文；代码及配置注释可用中文。
- 每个主题保留一个权威页面，引用验收结果，不在多处复制成绩。不新增空目录说明或重复路线图；待办统一在[项目计划](planning/README_cn.md)。
- 使用聚焦分支和提交，说明行为、相关验证与限制，区分仿真、合成数据和实测。按变更运行必要检查，行为变化按需补回归；包构建通过不代表实车就绪。

远程仓库：[Cangling178/odin_racer_ws](https://github.com/Cangling178/odin_racer_ws)。遵循 [LICENSE](../LICENSE)，保留上游权利说明。`.github/` 中的 PR／Issue 模板用于简洁记录问题和验证依据。
