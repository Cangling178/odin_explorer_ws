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

预览需要对应 ROS 安装中的 `robot_state_publisher`、`joint_state_publisher`、`xacro` 和 `rviz2`。
启动文件默认打开带模型与 TF 配置的 RViz；追加 `rviz:=false` 可关闭窗口。
有时钟源时，也支持 `use_sim_time:=true`。预览中的轮关节状态为静止示意。
独立传感器、落地接触与整车运动仿真的启动和验证命令见[仿真说明](../simulation/README_cn.md)。

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

结构检查器依赖 PyYAML，评测器及其测试仅使用 Python 标准库。接触模型测试还需 NumPy、PyYAML 和已加载的 ROS xacro 环境，见 `tools/requirements-dev.txt`。GitHub Actions 已配置为在 push/pull_request 时执行结构检查、离线测试和资源构建；它不运行需要渲染环境的 Gazebo 动态验证。

## 厂商底层工作空间

在 `vendor_ws/` 中使用经过独立审阅的厂商构建。`COLCON_IGNORE` 防止从根目录意外递归发现厂商包。构建自研叠加工作空间前先加载厂商安装环境，然后加载叠加层的 `install/local_setup.bash`。根目录构建明确使用 `--base-paths src`。不要在同一终端里混合加载 ROS 1 或另一 ROS 2 发行版。

## Git 工作流

保持 `main` 为经过检查的基础版本。开发时使用聚焦任务的分支，如 `codex/encoder-odometry`。需要时在提交中关联需求/任务编号。提交说明保持简洁，例如 `feat(hardware): add wheel feedback parser` 或 `docs(course): record crossing order`。合并前执行相关检查。记录真实里程碑依据后再打标签，不给未经测试的自主行驶能力打标签。

远程 `origin` 已配置为 [GitHub 仓库](https://github.com/Cangling178/odin_racer_ws)，许可见根目录 LICENSE。
提交时同步中英文文档、验证记录和 [项目计划](planning/README_cn.md)，检查通过后再推送。
构建产物、厂商源码、录包和 `data/generated/` 报告保持本地保存；复现命令和关键结果写入文档。

## C++ 循线检查

新增运行节点与参数见[低速视觉循线](../simulation/LINE_FOLLOWING_cn.md)。构建后执行：

```bash
source install/local_setup.bash
colcon test --base-paths src --packages-select racer_perception racer_control
colcon test-result --verbose
python3 tools/validate_line_controller.py
```

Gazebo 动态循线验证需渲染环境，不在 CI 中执行。纯 ROS 控制器故障验证使用隔离 domain 92，不连接硬件。
