# 仿真计划

[English](README.md) | 简体中文

已添加 Gazebo Classic 11 独立 Odin1 传感器测试场景，以及采用现有质量的整车落地接触测试；整车驱动尚未接入。确定 ROS/JetPack 和驱动模型后再选择仿真器；条件允许时，在工作站运行计算量大的仿真。

先进行确定性的平面测试：直线、等半径圆弧、S 曲线、坐标重复的交叉点、尖角以及受控数据丢失。之后加入实测车轮几何、执行延迟、饱和、打滑和相机视野，验证底盘能否通过实测走廊。

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

- RGB：1600×1296、10 Hz、水平 FOV 129°；**针孔近似**，垂直 FOV
  由宽高比推导，不能同时匹配官方 104°；没有实现 FishPoly 或真实全局快门误差。
  CameraInfo 为仿真针孔内参，绝不直接填设备鱼眼标定。
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
未验证带驱动的牵引、转向和制动，也未验证真实地面、真实球滚动或缺省质量的实车一致性。
