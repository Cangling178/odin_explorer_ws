# 仿真使用与验证

[English](README.md) | 简体中文

2026-09-14 更新：[C++ 单分支视觉循线](LINE_FOLLOWING_cn.md)已实现，含显式使能与锁存停车；完整比赛路线和实车验收仍待完成。

逐部件的模拟内容、参数近似与实车差异见[各部件仿真范围与实车差异](COMPONENT_SIMULATION_cn.md)；
后续工作优先级见[模型不足清单](MODEL_GAPS_TEMP_cn.md)。

比赛参考图赛道已搭建：追加 `course:=competition` 启动完整黑线场景，
详见[赛道启动、比例与验证](COMPETITION_COURSE_cn.md)。这是图片复刻版，已有单分支低速循线原型，完整路线仍待实现。

当前使用 Gazebo Classic 11 / ROS 2 Humble，已验证独立 Odin1 传感器输出、采用已有质量的整车落地接触，
以及 ros2_control 基础运动。长期仿真器选型仍待目标 ROS/JetPack 与实车驱动方案明确；
条件允许时，在工作站运行计算量大的仿真。

已完成直行、原地转向、圆弧、指令限幅及断流停车测试，并接入随车图像、点云和 IMU，
通过已知目标投影与运动响应检查。已新增直线和圆弧循线闭环入口；下一步验证实际安装下的黑线视野，
再扩展 S 曲线、坐标重复的交叉点、尖角及受控观测丢失测试。
当前接触、执行器和投影采用注明来源的近似；后续用实测几何、执行延迟、打滑与传感器数据校准，
验证底盘能否通过实测走廊。

验收要求：正确的有序进度、有界控制输出、观测缺失时明确标记无效、不切弯抄近路，以及可复现的误差/时间报告。仿真结果不能替代独立实车试验。

## Odin1 传感器测试

使用本机已安装的 Gazebo Classic 11 和 ROS2 Humble gazebo_plugins。
该后端只用于现有环境的测试入口，不代表长期仿真器选型。

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-select racer_description
source install/local_setup.bash
ros2 launch racer_description odin_sensors.launch.py
```

可追加 `gui:=false` 关闭 Gazebo 窗口；相机仍需要可用的图形渲染环境。
请先关闭 URDF 预览：独立场景与整车预览不能同时发布同名模拟传感器 TF。
ROS 话题：`/sim/odin1/image`、`/sim/odin1/camera_info`、
`/sim/odin1/cloud_raw`、`/sim/odin1/imu`，以及 `/clock`。
所有模拟数据使用仿真时间；消费者需设置 `use_sim_time=true`。
静止 Odin 安装基准在地面上 0.5 m，前方 2 m 有测试目标；不是当前车头安装高度，
也不是可驾驶整车。没有新增虚构整车质量或控制器。

### 参数与边界

- RGB：采用设备 O1-P040100136 标定的 **FishPoly** 几何投影，1600×1296、10 Hz。
  标定推算水平/垂直视场约 128.85°/103.30°；CameraInfo 使用项目自定义 `fishpoly` 约定。
  广角 cubemap 渲染后按标定逆映射采样；无曝光响应、运动模糊或图像噪声。详见 [FishPoly 实现](FISHPOLY_CAMERA_cn.md)。
- 深度/点云：240×180 角度采样、120°×90°、10 Hz、0.2–30 m。
  30 m 是选择的量程上限；未模拟官方反射率/光照条件下的 70 m 能力。
  Gazebo 射线不是实际 DTOF 成像，点云会过滤无效点，数量不固定；
  不包含厂商 confidence/offset_time 字段，也未模拟反射率、时间偏移、±3 cm 噪声。
- IMU：400 Hz 为参考 SDK 平滑发送默认值设定的仿真频率，非核实后的硬件采样率；
  理想无噪声、无偏置漂移。静止场景主要用于接口检查。
- 官方 IMU←LiDAR 平移 (-0.02663,0.03447,0.02174) m 已使用。
- 相机外参来自本机设备 O1-P040100136 的 calib.yaml，副本存于
  `hardware/mechanical/odin1/calib_device.yaml`。对其旋转做 SVD 正交化后取逆。
- 机壳→LiDAR 为从官方 CAD RX 镜头中心推定的近似 (15.55,5.5,31) mm，
  不是光学中心标定，整组外参不能直接作为实车安装标定。
- 模拟 TF 使用 odin_sim_* 前缀；未替代真实驱动的 imu/lidar/camera TF。
- 不模拟厂商内部 SLAM、cloud_slam、重定位、地图保存或曝光服务。

依据：[官方技术参数](https://manifoldtechltd.github.io/wiki/odin_series/odin1/14.%20Technical%20Specifications_.html)、
[官方数据输出与外参](https://manifoldtechltd.github.io/wiki/odin_series/odin1/5.%20Data%20output_.html)。

验证记录：本机实际收到 1600×1296 图像和 CameraInfo、XYZ/intensity 点云、IMU；静止加速度 Z=9.81 m/s²。尚未验证运动响应与实物误差。

## 整车地面接触测试

使用当前 Xacro 生成独立动态场景，不添加未知部件质量。生成器按固定关节合并
质量、质心和惯性（包含坐标旋转与平行轴项），同时搬移所有外观和碰撞体。
物理模型含 3 个刚体：0.785 kg 车体及两个各 0.046 kg 的车轮，总质量仍为
0.877 kg；25 个碰撞体与两个自由轮关节保留。前球作为车体上的低摩擦滑动支撑，
不模拟球体旋转。源 URDF 的 TF 树和零件级惯性不变，生成的 SDF 不重复计重。

参数集中在 [ground_contact.yaml](../src/odin_racer/racer_description/config/ground_contact.yaml)，
由场景生成器读取，不是 ROS 节点参数文件。以下全部为初始工程值，未实测标定：

| 参数 | 初始值 | 用途 |
| --- | --- | --- |
| 后轮 mu / mu2 | 0.8 / 0.8 | 轮胎接地摩擦 |
| 前球 mu / mu2 | 0.02 / 0.02 | 低摩擦支撑近似；不代表实测滚动阻力 |
| 其他部件 / 地面摩擦 | 0.5 / 1.0 | 地面不限制较小的物体摩擦系数 |
| 接触 kp / kd | 100000 N/m / 100 N·s/m | 接触刚度与阻尼 |
| min_depth | 0.0001 m | 接触修正容差，不是穿透量的硬上限 |
| max_vel | 0.1 m/s | 穿透修正速度上限，不是车速上限 |
| 恢复系数 | 0 | 不额外施加恢复弹性 |
| 最大接触点数 | 10 / 碰撞体 | 轮胎接触求解 |
| ODE 步长 / 迭代数 / SOR | 1 ms / 80 / 1.3 | quick 求解器，pyramid 摩擦模型 |
| 轮关节阻尼 | 0.0001 N·m·s/rad | 小阻尼，自由轮；不是电机刹车 |
| 初始离地间隙 | 20 mm | 从几何最低点推导释放高度 |

kp、kd 同时写入地面和物体表面；最终接触响应由 ODE 双方表面参数共同决定。
参数含义参考 [Gazebo 物理参数](https://classic.gazebosim.org/tutorials?tut=physics_params)
和 [SDFormat 接触规范](https://sdformat.org/spec/1.7/collision/)，具体取值是本工程初值。

在工作空间根目录启动：

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-select racer_description
source install/local_setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
ros2 launch racer_description ground_contact.launch.py
```

无窗口测试追加 `gui:=false`。可用 `contact_config:=/absolute/path/config.yaml` 替换参数。
专用 ROS domain 和 Gazebo master 将测试与已有预览/设备会话隔离；另一测试终端需使用相同
环境变量。该入口提供 Gazebo 可视化、/clock、/contact_test/model_states、
/contact_test/link_states 和 /contact_test/get_entity_state，不发布车辆 TF、轮速指令或
模拟 Odin 数据；状态服务是仿真真值，不能当作定位算法输出。

复现本次落地检查（仅对上述专用测试世界使用 --reset，它会重置整个仿真世界）：

```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
python3 tools/validate_ground_contact.py --reset \
  --output data/generated/ground_contact_validation.json
python3 -m unittest discover -s tests -v
```

检查程序观察 10 秒仿真时间，取后 5 秒检查高度误差 <1 mm、垂直波动 <0.5 mm、
水平漂移 <1 mm、线速度 <0.005 m/s、角速度 <0.02 rad/s、姿态偏转 <0.5°。
这些是本场景的工程检查阈值，不是实车性能指标；修改几何或释放高度后需同步审查检查条件。

2026-09-13 本机 Gazebo 11.10.2 / ROS 2 Humble 验证：SDF 校验、包构建、11 项单元测试通过；
从 base_link 高 53.25 mm 释放，观察 10.036 s，稳定高度约 33.1267 mm（名义值 33.25 mm），
静置阶段最大线速度约 0.0000323 m/s、角速度约 0.0000541 rad/s、姿态偏转约 0.00460°。
独立采集约 1 秒 Gazebo contacts，四个支撑各出现 987 条接触记录，没有其他部件触地。
该落地检查不覆盖带驱动的牵引、转向和制动；后续基础运动验证见下节。
真实地面、真实球滚动及未计入质量对实车一致性的影响仍未验证。

提交整理时已修正仓库检查器的 CAD 二进制扫描和厂商目录边界，并补齐临时不足清单英文版；
全量仓库检查、包构建和单元测试通过。动态验证结果保持上面的适用范围。

## ros2_control 整车运动仿真

启动入口为 racer_bringup 的 simulation.launch.py，复用已有碰撞、接触和惯性合并。
仿真 URDF 通过 sim_control:=true 声明两个轮关节的 velocity 命令接口及
position/velocity/effort 状态接口；GazeboSystem 在仿真中使用 PI 轮速反馈施加力矩。
仅激活 joint_state_broadcaster 与 diff_drive_controller；未启动真实 F4 接口或循线算法。
不再运行预览用 joint_state_publisher，避免覆盖实际轮状态。

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-select racer_description racer_control racer_bringup
source install/local_setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
ros2 launch racer_bringup simulation.launch.py
```

无窗口追加 gui:=false。与独立落地场景二选一运行；相同 Gazebo master 只能运行一个 server。
另一终端设置相同环境，确认两个控制器 active：

```bash
source /opt/ros/humble/setup.bash
source install/local_setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
ros2 control list_controllers -c /sim/racer/controller_manager
ros2 topic pub --use-sim-time -r 20 -t 60 \
  /sim/racer/diff_drive_controller/cmd_vel geometry_msgs/msg/TwistStamped \
  '{header: {stamp: now, frame_id: base_link}, twist: {linear: {x: 0.1}, angular: {z: 0.0}}}'
```

命令时间戳必须来自 /clock；命令停止后由控制器超时制动。0.25 秒是开始超时处理的期限，
不是物理车速归零时间；制动还受加速度限制与轮速闭环响应影响。仿真暂停时该时限也暂停，
不等同于实车 F4 的独立看门狗。启动只激活仿真控制器，不自动发送非零速度。

| 设置 | 值 / 说明 |
| --- | --- |
| 控制 / 里程计发布频率 | 100 Hz / 50 Hz，使用仿真时间 |
| 轮半径 / 名义轮距 | 从 Xacro 读取 0.03325 m / 0.257 m，不重复维护 |
| 有效轮距修正 | 1.10，仅当前仿真接触模型；有效轮距 0.2827 m |
| 线速度 / 角速度上限 | ±0.2 m/s / ±1.0 rad/s |
| 线加速度 / 角加速度上限 | ±0.3 m/s² / ±1.5 rad/s² |
| 指令时效 | TwistStamped，cmd_vel_timeout=0.25 s |
| 轮速度 / 力矩上限 | ±12 rad/s / ±0.1 N·m，初始仿真值 |
| 轮速 PI | Kp=0.02、Ki=0.05、Kd=0；积分力矩限幅 ±0.03 N·m，抗积分饱和 |
| 里程计 | position_feedback=true、open_loop=false，使用轮位置反馈 |

控制参数在 [simulation_controllers.yaml](../src/odin_racer/racer_control/config/simulation_controllers.yaml)，
执行器初值在 [sim_actuation.yaml](../src/odin_racer/racer_description/config/sim_actuation.yaml)。
生成器将几何填入临时运行 YAML，并检查组合线/角速度不超过轮速度上限。轮关节力矩、速度限值
同时写入仿真 URDF 与 SDF。控制器配置可用 controllers:=/absolute/path/file.yaml 替换；
修改模型、接触或配置后应重新启动场景。

有效轮距的依据：最初采用名义轮距和 PI 轮速反馈时，左右原地转向及圆弧的
“按名义轮距计算的轮式角速度 / Gazebo 实际角速度”约为 1.101。
这反映当前宽圆柱轮胎的接触/滑动行为，采用 1.10 后再独立运行测试；CAD 轮距没有修改。
修正只属于这套仿真参数，不能作为实车轮距标定；更换轮胎、接触参数或地面后需重新验证。

| 接口 | 发布者 / 含义 |
| --- | --- |
| /sim/racer/diff_drive_controller/cmd_vel | 外部测试输入，TwistStamped |
| /sim/racer/diff_drive_controller/cmd_vel_out | 控制器输出的限幅指令 |
| /sim/racer/diff_drive_controller/odom | 控制器计算的轮式里程计 |
| /sim/racer/joint_states | joint_state_broadcaster，实际仿真轮状态 |
| /sim/racer/tf、/sim/racer/tf_static | 控制器负责 odom→base_link；robot_state_publisher 负责车内变换 |
| /contact_test/get_entity_state、/contact_test/link_states | 独立 Gazebo 真值，用于对照，不参与轮式里程计 |

odom 是以启动时车体位姿为基准的局部平面参考系，Gazebo world 是物理世界；没有伪造 world→odom
变换。里程计中的 z=0 不等于 Gazebo 地面高度。Odin 默认产生随车图像、点云和 IMU，接口与验证见下节。

```bash
# Same isolated ROS domain as the simulation; this actively moves the robot.
python3 tools/validate_sim_drive.py --output data/generated/sim_drive_validation.json
```

验证脚本运行前进、后退、左右原地转向、圆弧和超限指令，比较轮反馈、轮式里程计与世界真值，
检查零速停车、发布中断、过期指令、限幅、力矩和 TF 发布者；结束时发送零速。
脚本使用默认配置的测试速度和验收阈值，不重置世界；不要同时运行其他指令发布者。
接口依据：[gazebo_ros2_control](https://control.ros.org/humble/doc/gazebo_ros2_control/doc/index.html)、
[diff_drive_controller](https://control.ros.org/humble/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html)。

运动验证记录（2026-09-13，Gazebo 11.10.2 / ROS 2 Humble）：首次配置检查以及随后复测均通过。
最终复测的前/后直行约 +0.1000/-0.1000 m/s，左右转向约 +0.4998/-0.5057 rad/s，
圆弧约 0.1002 m/s、0.4983 rad/s；超限指令被限制为 0.2 m/s 和 1 rad/s。
断流测试观测约 0.30 s 开始减速、0.60 s 达到停车阈值，额外距离约 44.9 mm。
零速停车各场景约 0.4–0.9 s；停车阈值为 |v|<0.005 m/s、|w|<0.02 rad/s 且限幅指令接近零。
六项测试中，分段里程计位移增量误差最大约 11.3 mm、航向增量误差最大约 0.0079 rad。
分段位移比较使用 world 与 odom 的各自坐标轴，长期累积方向漂移也会贡献该误差。
速度、加速度、力矩、过期命令、静止高度和 TF 完整性检查全部通过；14 项单元测试通过。
本记录仅证明基础平面运动可用，不代表比赛循线或真实电机性能。完整指标由上面的脚本生成。

## 随车 Odin 传感器

整车运动入口默认 `sensors:=true`。传感器直接挂在固定部件合并后的 `base_link` 物理刚体上，
安装位姿沿展开后的 Xacro 固定关节链计算，包含 Odin 安装与传感器相对外参。
相机生成器将 ROS 光学坐标轴换算为 Gazebo 渲染坐标轴；消息仍使用光学坐标系。
不新增刚体或质量，整车仍为三个刚体、0.877 kg、25 个碰撞体。

[odin_sensors.yaml](../src/odin_racer/racer_description/config/odin_sensors.yaml) 为独立台架与整车共用的
传感器参数，包含分辨率、频率、FOV 和量程；外参仍以 Xacro 为来源。
[sensor_world.py](../src/odin_racer/racer_description/racer_description/sensor_world.py) 负责生成两种场景的传感器。
`worlds/odin_sensors.world` 现在是独立台架模板，通过原有 launch 生成可运行世界，不能直接作为完整传感器世界启动。
设备原始 `calib_device.yaml` 未修改；相机已采用 FishPoly 几何投影；点云仍为射线、IMU 仍为理想模型，不模拟厂商 SLAM。

| 话题 | 类型 / 坐标系 | 订阅建议 |
| --- | --- | --- |
| `/sim/racer/odin1/image` | Image / `odin_sim_camera_optical` | Reliable、Volatile、depth=5 |
| `/sim/racer/odin1/camera_info` | CameraInfo / `odin_sim_camera_optical` | Reliable、Volatile、depth=5 |
| `/sim/racer/odin1/cloud_raw` | PointCloud2 / `odin_sim_lidar` | sensor_data QoS |
| `/sim/racer/odin1/imu` | Imu / `odin_sim_imu` | sensor_data QoS |

消费者设置 `use_sim_time=true`，并将 `/tf`、`/tf_static` 重映射到 `/sim/racer/tf`、`/sim/racer/tf_static`。
整车只由 robot_state_publisher 发布车内 TF，差速控制器发布 odom→base_link；没有独立台架 TF 发布节点。
本机用尽力传输订阅大图像时出现明显丢帧，Reliable 订阅恢复约 10 帧/仿真秒。
跨机器或换 DDS 实现时需重新测量传输和时延。

| 启动参数 | 默认值 / 用途 |
| --- | --- |
| `sensors` | true；false 时只运行底盘，适用于没有渲染环境的运动测试 |
| `sensor_config` | 共用 odin_sensors.yaml；可替换整车传感器配置，需重新启动 |
| `sensor_targets` | false；true 添加前方红色方块和蓝色地面标记，用于验证 |
| `course` | empty；competition 为比赛参考图赛道，不能同时添加 sensor_targets |
| `course_overview` | false；true 启用比赛场景的固定俯视检查相机 |
| `gui` | true；false 只关闭窗口，相机仍需要可用的 DISPLAY/渲染环境 |

使用新启动的专用世界，不与其他命令发布者共用。测试会主动移动车辆，不重置世界；
重复传感器验证前重新启动场景。以下使用默认模型及传感器参数：

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-select racer_description racer_control racer_bringup
source install/local_setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
ros2 launch racer_bringup simulation.launch.py gui:=false sensor_targets:=true
```

另一终端加载相同 ROS 环境和 domain 后运行：

```bash
python3 tools/validate_sim_sensors.py --output data/generated/sim_sensors_validation.json
python3 tools/validate_sim_drive.py --output data/generated/sim_drive_with_sensors_validation.json
```

传感器验证覆盖静止、0.1 m/s 前进、左右 0.25 rad/s 转向及加减速。
停车后的图像与点云对照已知目标：红色方块中心 (2,0,0.2) m、尺寸 (0.1,0.3,0.4) m；
蓝色标记中心 (0.8,0,0.001) m、尺寸 (0.3,0.12,0.001) m，仅有外观，不影响地面接触。
图像按 FishPoly CameraInfo 投影比较采样后的曲线边界（包括标记移出画面的裁剪），阈值 8 px；
点云目标表面 P95 误差阈值 20 mm、地平面 10 mm。IMU 检查左右角速度、加速/制动符号、
匀速与静止响应；同时检查 TF、发布者、时间戳、消息新鲜度和实收频率。
Gazebo link_states 没有采集时间戳：几何比较仅在停车后进行，运动 IMU 对照使用最近真值，
属于基础响应验证，不能作为精密时延或实车标定报告。

历史记录（2026-09-13，旧针孔版本；FishPoly 验收见上述专页）：图像/CameraInfo 约 10 Hz、点云约 10 Hz、IMU 约 399.9 Hz，
均按仿真时间计。四个停车位姿的红色目标边界最大误差约 3.13 px，地面标记约 3.63 px；
左右转向 IMU 与真值的稳态角速度平均绝对误差均低于 0.0002 rad/s。
测得实时因子约 0.62，未达到实时运行；这是当前电脑、渲染和订阅负载下的结果。
该标记可见性不代表全部近地视野或真实黑线可见性验收。已另建[比赛参考图场景](COMPETITION_COURSE_cn.md)
并检查初始直段黑线投影；全赛道视野、遮挡/丢帧测试和算法闭环仍待完成。
