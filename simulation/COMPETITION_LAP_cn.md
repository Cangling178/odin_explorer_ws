# 比赛地图连续整圈循迹

[English](COMPETITION_LAP.md) | 简体中文

目标：在现有 Gazebo 比赛地图上沿线完成一圈，起步后至终点前不停驶。
采用已确认的“预录有序路线 + 车载视觉校正 + 轮式里程计”方案。
运行控制和视觉处理使用 C++；Python 只负责资源准备、启动和独立验收。

## 路线与输入

地图保持默认4×3 m、约21.2 mm线宽，未修改纹理、车辆或相机模型。
从右侧直线中部朝下出发，依次经过底部波浪、左侧回弯、左上矩形、中央小环，
再通过中央交叉点向右上行驶，返回起点。中央交叉点按路线顺序经过两次。
原图左侧受损笔画按地图连通关系通过，运行期间仍须收到健康图像。
这是一条明确选定的仿真路线，不声明它是正式比赛规定的通行顺序。

`tools/generate_competition_lap.py` 从原纹理骨架按有序锚点提取路线，生成
`racer_control/config/competition_lap.csv` 和来源摘要。运行节点加载该文件，
不订阅 Gazebo 真值、俯视相机或评测器输出。

`lap_controller.cpp` 用局部路线进度窗口约束位置投影，防止在交叉点跳到另一次通行。
利用图像采集时刻的TF，把地面黑线掩膜的窄线骨架与完整地图做点到线匹配，校正地图与轮式里程计的对齐。
交叉点处单分支感知不确定时，可短距离使用已知路线和轮式里程计；未成功视觉校正的累计路线距离限制为0.65 m。
Pure Pursuit在紧弯降低前进速度，保持非零平移；不进入旧控制器的停车转角状态。

图像期限0.35 s、里程计期限0.15 s、墙钟看门狗1 s；故障停车锁存。
这些期限不因使用预录路线而放宽。启动仍需显式使能；完成一圈后自动停车。

## 构建与启动

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --symlink-install
source install/local_setup.bash
export ROS_DOMAIN_ID=96
export GAZEBO_MASTER_URI=http://127.0.0.1:11396
ros2 launch racer_bringup competition_lap.launch.py gui:=true
```

相机渲染需要有效DISPLAY。READY后，在相同环境的另一终端启动：

```bash
ros2 service call /sim/racer/line/lap_controller/enable std_srvs/srv/SetBool '{data: true}'
```

主动停止将`data`改为`false`。重新进行完整一圈应重新启动仿真，重置出生位姿和路线进度。
`control_debug`输出路线进度、估计位姿、观测年龄、视觉匹配残差和指令。
原有`line_following.launch.py`继续用于单分支场景。

## 独立验收

以下命令主动启动隔离仿真并使能车辆，输出目录必须是新的：

```bash
python3 tools/validate_competition_lap.py --output data/generated/competition_lap/my_run
python3 tools/report_competition_lap.py data/generated/competition_lap/my_run
```

验收条件在运行前固定：

- 按顺序通过每100 mm一个的路线检查点，半径100 mm；返回起点并由控制器报告FINISHED。
- 全程轮轴到地图中心线的最大误差≤100 mm，时间加权RMS≤50 mm。
- 排除起步1 s与终点停车后，中途指令线速度始终为正，实测平移速度始终大于3 mm/s。
- 检查图像时效、真值采样时效、指令上限、唯一指令发布者和终点物理停车。

误差门限是本次仿真工程验收约定，并非车轴始终压在21 mm黑线内部或正式比赛评分承诺。
报告包括`report.json`、`trajectory.png`、`launch.log`以及源文件、二进制摘要。
进度与停止检查用Gazebo独立位姿，评测结果不回传控制器。

## 验证状态

已完成一次整圈动态验收：367.29 s，185/185检查点，中途不停；轮轴偏线RMS5.32 mm、最大22.25 mm，最低行驶速度19.13 mm/s。

[验收结果和范围](../experiments/competition_lap/RESULTS_cn.md)。原始HTML报告为`data/generated/competition_lap/attempt07/index.html`。

最终检查：11个包构建通过；colcon统计32项C++测试记录通过（含测试套件结果）；41项Python测试通过；12项ROS控制器检查通过。
历史54次独立场景验收不覆盖新整圈控制器，本次未重跑该历史动态矩阵。

## 重复运行验证

使用同一份程序、地图、参数和验收标准，按顺序独立启动3次仿真。每次重新生成仿真世界并从名义起点出发。输出目录必须是新的：

```bash
python3 tools/repeat_competition_lap.py --output data/generated/competition_lap/my_repeats
```

汇总为输出目录中的`index.html`与`summary.json`，每次运行保留独立报告和日志。程序运行中会检查输入文件及二进制摘要，防止不同版本的结果被合并为重复验收。此检查只验证名义起点下的重复性，不代表任意起点、扰动或实车稳定性。

## 最新结果

0.05 m/s 三次独立启动均通过，圈时 367.26–367.36 s；0.10 m/s 单次通过，圈时 197.43 s。默认仍为 0.05 m/s，速度参数上限 0.10 m/s。完整指标及适用范围见[results](../experiments/competition_lap/RESULTS_cn.md).
