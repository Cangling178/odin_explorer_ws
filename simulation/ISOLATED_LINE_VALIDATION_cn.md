# 独立场景验证与复现

[English](ISOLATED_LINE_VALIDATION.md) | 简体中文

最终冻结验收：**42/42次跟踪和12/12次故障测试通过**。
各场景最差误差、车体扫掠上界、故障停车延迟和代表图见
[交付结果](../experiments/isolated_line/RESULTS_cn.md)。

运行实现和接口见 [C++ 视觉循线](LINE_FOLLOWING_cn.md)。这是仿真工程测试，不是正式比赛或实车认证。
参考路径、结束区域和 Gazebo 真值只进入独立评测器。感知与控制仅消费车载图像、CameraInfo、TF 和轮式里程计。

## 冻结的验收条件

[acceptance.json](../experiments/isolated_line/acceptance.json) 在算法改动前记录误差、速度、走廊和初始条件。
正式重复矩阵再冻结运行源码、参数及评测器 SHA-256，执行中若变化就中止矩阵，不能混合不同版本的结果。

| 项目 | 工程验收条件 |
| --- | --- |
| 正确通过 | 到达半径 60 mm 的结束区，出口航向误差 <0.25 rad，顺序经过全部参考检查区，无故障停车 |
| 全程误差 | 时间加权 RMS <60 mm，P95 <100 mm，最大 <140 mm；同时报告初始、跟踪、转角阶段 |
| 直线与圆弧回归 | 末段 30% 时间的时间加权 RMS <15 mm |
| 工程走廊 | 参考折线两侧各 230 mm；检查整个车体保守包络及采样间运动余量 |
| 指令 | v≤0.05 m/s，\|w\|≤0.5 rad/s，线/角加速度≤0.15 m/s² / 0.8 rad/s² |
| 观测 | 成功变换的图像原始采集年龄≤0.35 s；里程计期限0.15 s |
| 故障 | 零速请求延迟<0.6 s；再观察1.2 s确认速度<0.005 m/s、角速度<0.02 rad/s；恢复1 s后仍锁存停止 |
| 初始条件 | 居中、左右35 mm偏移、正负0.08 rad航向；居中重复两次 |

原始报告另外记录仿真实际速度与角速度，用10%的接触动态余量检查物理速度边界。故障和显式停止的
零速请求独立标记，不当作正常加速度整形失败；主动转角停车仍经过正常限幅。

直角附近，“到参考线最近点”的弧长坐标本来就可能不连续：车体只移动2 mm，最近点可能从入口切换
到出口、使该坐标跳变160 mm。因此报告保留最近点坐标最大跳变，但路线顺序用沿参考线每100 mm
的检查区独立验证，半径沿用固定最大误差140 mm；50 mm的瞬时跳跃门槛用于实际相邻车体位置。
检查器测试同时覆盖正常直角投影切换和真正跳过路径段，不能靠终点位置单独判定通过。

## 场景几何

默认黑线宽21 mm，地面接触模型保持一致。所有场景的打印线都会延伸到结束区域之后，以免把
“到达终点”误当作“线突然消失”。白底和黑线都是无碰撞的视觉几何；重复测试将相同条带表面
合并为一个网格，减少渲染调用，未改变参考中心线或走廊。

| 场景 | 几何与结束条件 |
| --- | --- |
| `line_straight` | y=0；结束中心(1.2,0) m |
| `line_left` / `line_right` | 半径0.8 m，圆心(0,±0.8) m；转过±1.5 rad后的点为结束中心 |
| `line_arc` | 保留0.8 m原左圆弧回归；转过2.5 rad后结束 |
| `line_s` | x从0到2 m；y=0.14·[1−cos(πx)] m，曲率正负变化；结束中心(2,0) m |
| `line_corner_left` / `line_corner_right` | 入口y=0，到x=0.8 m后单个±90°角；结束中心(0.8,±0.7) m |

场景参数由 `course_world.line_fixture` 明确定义，报告保存全部参数、初始位姿和参考折线。
单次开发默认初始位姿(0,−0.035,−0.08)，正式矩阵使用上表五类条件。

## 独立评测与扫掠范围

`isolated_line_metrics.py` 不被运行算法导入。它通过 Gazebo `LinkStates` 的车体真值计算最近线段
误差、路线检查区顺序和结束区条件。误差以实际采样间隔加权，分阶段统计不会跨越其他阶段的时间空档。
报告保存所有采样、指令、控制状态、观测年龄、停车位置、运行终止原因，以及源码和二进制散列。

扫掠由现有 URDF 导出的所有碰撞体计算，包括车轮、车板、立柱和传感器，不只检查车轴中心。
当前评测用全部碰撞体的保守XY矩形包络并填充10 mm网格，再增加网格覆盖半径和采样间平移/旋转余量。
它会填满真实车体空隙，属于保守上界。包络超出走廊会判本次工程测试失败；这不单独证明任何控制
策略下底盘都物理不可能通过。开发中18 mm停车后转向曾使此包络超界，报告保留；最终策略提前约80 mm
停车，参考线和230 mm走廊不变。正式比赛宽度尚未给出，不能据此宣称满足正式比赛规则。

## 复现命令

先构建并加载ROS和工作区，确认DISPLAY和端口可用。以下命令会主动驱动隔离仿真，不连接实车：

```bash
python3 -m unittest discover -s tests -v
colcon test --base-paths src --packages-select racer_perception racer_control
colcon test-result --verbose
python3 tools/validate_line_controller.py
python3 tools/validate_arming_clock.py

# 单次完整场景；已存在输出目录会被拒绝，所有尝试保留。
python3 tools/validate_isolated_line.py --course line_corner_left \
  --output data/generated/my_corner_run

# 静止检查角点，绝不使能。
python3 tools/validate_isolated_line.py --course line_corner_left --static \
  --spawn-x .35 --spawn-y 0 --spawn-yaw 0 --output data/generated/my_static_run
ros2 run racer_perception line_offline \
  data/generated/my_static_run/0001_static_gray.png data/generated/my_static_run/offline

# 固定参数矩阵：7场景×(居中2次+其他4类各1次)=42次。
python3 tools/run_isolated_matrix.py --output data/generated/my_fixed_matrix

# 3阶段×4故障；每个故障使用全新场景。
python3 tools/run_isolated_matrix.py --faults --output data/generated/my_fault_matrix

# 导出独立轨迹/误差图、带目标点的调试图、HTML索引和JSON汇总。
python3 tools/report_isolated_line.py data/generated/my_fixed_matrix
```

`--domain` 和 `--port` 允许隔离多组测试。故障矩阵使用单个左直角的 `RUNNING`、`APPROACH`、`TURN`
三个阶段，各注入停图、空白图像、停TF、停里程计。若无法到达指定阶段，报告标记未覆盖/失败，
不能算故障停车通过。`validate_line_controller.py` 另覆盖重复/乱序时序、延迟TF、无效路径、NaN、
错误帧、异常里程计、禁止自动重启和显式停止。

每次运行保存原图、实际输入图、灰度地面图、黑线掩膜、中心线/角点/出口图及采集时刻路径。
图像按仿真时间每秒和状态变化记录，故障/结束另存快照；控制指令按接收到的每条记录，真值约20 Hz。
`report_isolated_line.py` 在地面调试图上补画前视目标、控制状态、年龄和指令，并生成可导出的静态图。

## 本次交付的证据目录

原始基线、静止/离线图、逐次开发失败和正式矩阵位于本机 `data/generated/isolated/`。
其中 `baseline/source` 保存原算法快照，`baseline/binaries.sha256` 标记原运行二进制。
`baseline` 的七场景结果、`development_v*` 的所有成功和失败都保留，不能与正式矩阵混算成功率。
正式结果以 `validated/final_curves`、`validated/final_turns` 和 `validated/final_faults` 目录的
`manifest.json`、逐次 `report.json` 及 `validated/final_summary.json` 为准。
这些大体积原始产物按仓库策略不纳入Git；复现代码、标准、测试和本说明纳入源码。

## 开发失败与回归修复

原逐行算法的七场景基线为三次通过、四次失败：左右圆弧与原圆弧通过，两个直角因横向出口被判为宽黑区停止；
直线和S弯各出现一次TF失效停止。原代码、图像、失败位置和原因均保留在 `baseline/`。

开发记录还包含近视野起点遗漏、短支撑入口方向偏差、盲区碎片误判分支、18 mm停车后的车体扫掠超界、
评测TF中继延迟和两次重复验收发现的控制边界问题：

- 前视圆交点恰好落在相邻线段公共端点时，微小浮点误差可能使两条线段同时拒绝该交点。
  修复为数值容差内钳位到端点；10万组确定性微扰重放无遗漏，并新增1000组C++回归检查。
- 使能前的零速周期与使能后的第一条指令可能跨过仿真时钟量化边界，使起步加速度统计达到上限两倍。
  修复为使能时重置加速计时，并让周期零速与非零指令使用一致的周期时间戳；独立20次重复使能检查通过。

这些修复没有改变验收阈值。早期冻结轮次的记录不会被覆盖，也不与最后版本混合计算成功率。
无效图像无法形成新地面投影时，调试地面图可能仍是最近一次有效投影；故障证据以实际输入图、
观测有效性、控制状态、逐条指令和真值停车检查共同判断，不能将旧调试图当作新观测。
