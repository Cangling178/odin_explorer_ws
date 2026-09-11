# 开发流程

[English](07_development.md) | 简体中文

## 平台基线

在干净的终端环境中使用目标 ROS 发行版。基础工程面向 Humble，本地工作站无需 Jetson 或 ODIN1 即可构建资源。目标设备投入使用时，在 `hardware/platform_lock.template.yaml` 记录实际软件版本。初始化脚本不会自动刷写设备、安装软件包、修改 udev 规则或启动电机。

## 构建和检查

```bash
cd ~/odin_racer_ws
source /opt/ros/humble/setup.bash
colcon list --base-paths src
colcon build --symlink-install --base-paths src
source install/local_setup.bash
ros2 launch racer_bringup preview.launch.py --show-args
ros2 launch racer_bringup preview.launch.py
```

预览需要对应 ROS 安装中的 `robot_state_publisher`、`joint_state_publisher` 和 `xacro`。如需可视化，在另一个已加载环境的终端中运行 `rviz2`，将 Fixed Frame 设为 `base_link`，添加 RobotModel 和 TF。有时钟源时，也支持 `use_sim_time:=true`。静止关节只是示意，不是物理仿真。

安装并初始化 ROS 和 rosdep 后，可按需执行标准依赖安装步骤：

```bash
rosdep install --from-paths src --ignore-src --rosdistro humble -r -y
```

此命令可能安装系统软件包，基础工程创建时没有执行它。规划中的包仅声明现有代码真正使用的依赖。实现实际节点时再添加运行依赖，避免给仅含文档的包强加完整导航/GPU 软件栈。

## 离线检查

```bash
python3 tools/check_workspace.py
python3 -m unittest discover -s tests -v
python3 tools/evaluate_run.py experiments/examples/synthetic_samples.csv \
  --metadata experiments/examples/synthetic_run.json
git diff --check
```

结构检查器依赖 PyYAML，评测器及其测试仅使用 Python 标准库，见 `tools/requirements-dev.txt`。可选 GitHub 工作流执行结构检查、离线测试和资源构建；只有后续将仓库托管到 GitHub 时才会运行。

## 厂商底层工作空间

在 `vendor_ws/` 中使用经过独立审阅的厂商构建。`COLCON_IGNORE` 防止从根目录意外递归发现厂商包。构建自研叠加工作空间前先加载厂商安装环境，然后加载叠加层的 `install/local_setup.bash`。根目录构建明确使用 `--base-paths src`。不要在同一终端里混合加载 ROS 1 或另一 ROS 2 发行版。

## Git 工作流

保持 `main` 为经过检查的基础版本。开发时使用聚焦任务的分支，如 `codex/encoder-odometry`。需要时在提交中关联需求/任务编号。提交说明保持简洁，例如 `feat(hardware): add wheel feedback parser` 或 `docs(course): record crossing order`。合并前执行相关检查。记录真实里程碑依据后再打标签，不给未经测试的自主行驶能力打标签。

当前没有远程仓库。选择开源许可证和发布是后续独立决定。即使不用 GitHub，也可以将任务条目复制到 [项目计划](planning/README_cn.md)，并在旁边记录验证依据。
