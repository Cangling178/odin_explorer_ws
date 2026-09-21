# 仿真模型与实车差距

[English](MODEL.md) | 简体中文

2026-09-21 按当前模型与配置核对，合并原部件对照和临时不足清单。命令见[仿真入口](README_cn.md)，优先级见[项目计划](../docs/planning/README_cn.md)。

## 几何与动力学

| 部件 | 当前模型 | 尚存差异 |
| --- | --- | --- |
| 车板／ODIN | 原始 CAD 外观、保守基本几何碰撞 | 无弹性或精密干涉验收，安装未实测 |
| 后轮 | 直径 66.5 mm、宽 26 mm、名义轮距 257 mm | 刚性圆柱，无实测轮胎变形或滚阻 |
| 前支撑 | 固定 CY-15A 类球体／壳体 | 低摩擦滑动替代球体旋转和轴承行为 |
| 电机／支架 | MG513X 简化几何和估算惯性 | 无齿隙、内部转子惯性及连接弹性 |
| 铜柱 | 对边 4.5 mm、推导长 42 mm | 无螺纹，法兰省略；CAD 孔距 38.3 mm 与商品 40 mm 不符 |
| ODIN 安装 | 朝前、贴板假设 | 孔距不完全一致，视野与散热间隙待验证 |

[底盘尺寸](../hardware/mechanical/chassis_plate/README_cn.md)和[ODIN 来源／安装](../hardware/mechanical/odin1/README_cn.md)保留原始依据。源 URDF 的 16 个外观／实体 link 上有 25 个基本碰撞体；车板孔洞和空隙保守填充，允许装配内部重叠，关闭自碰撞。

已计入参考质量：电机 340 g、支架 94 g、轮胎轮毂 92 g、前支撑组件 71 g、ODIN 280 g，**小计 877 g，不是整车总质量**。车板、铜柱、电池、Jetson、F4 和驱动器质量暂缓。惯性按均匀盒体／圆柱估算，非实测。固定关节合并为 0.785 kg 车体和两个各 0.046 kg 轮子，包含旋转和平行轴项，不重复计重。

## 地面接触与执行器

[ground_contact.yaml](../src/odin_racer/racer_description/config/ground_contact.yaml) 保存未标定初值：后轮／前球／其他／地面摩擦 0.8／0.02／0.5／1.0，kp=100000 N/m，kd=100 N·s/m，min_depth=0.1 mm，修正 max_vel=0.1 m/s，ODE 步长 1 ms、80 次迭代。接触修正速度不是车速上限，摩擦设置也不表示无打滑。

[sim_actuation.yaml](../src/odin_racer/racer_description/config/sim_actuation.yaml) 使用轮速 PI 力矩反馈：Kp=0.02、Ki=0.05，积分力矩 ±0.03 N·m、总力矩 ±0.1 N·m、轮速 ±12 rad/s；没有电压、电流、PWM、死区、温升或编码器量化模型。

[simulation_controllers.yaml](../src/odin_racer/racer_control/config/simulation_controllers.yaml)：控制 100 Hz、里程计 50 Hz；车体上限 ±0.2 m/s、±1 rad/s，加速度 ±0.3 m/s²、±1.5 rad/s²；轮半径 0.03325 m。有效轮距系数 1.10 对应当前接触模型（有效轮距 0.2827 m），不是实车几何。里程计读取仿真轮位置，不使用指令速度或世界真值。

0.25 s 指令超时只表示开始制动，不是瞬时物理静止，且随仿真时间暂停。模型没有 F4 看门狗、上位机传输延迟、供电或电气停止行为，实车必须单独验证。

## 传感器与赛道

| 部件 | 当前实现 | 省略／未验证 |
| --- | --- | --- |
| RGB | 设备 O1-P040100136 FishPoly 几何，1600×1296、10 Hz | 曝光、模糊、噪声、压缩和实机时序 |
| 点云 | 240×180 射线，120°×90°，0.2–30 m、10 Hz | DTOF 材料／光照响应、噪声、confidence 和 offset_time |
| IMU | 理想加速度／角速度，配置 400 Hz | 偏置、噪声、温漂；真实硬件输出频率 |
| 外参 | Xacro 固定关节链、设备相机标定转换 | 机壳到雷达采用 CAD 镜头中心近似，车体安装未标定 |
| 厂商定位 | 未模拟 | SLAM、cloud_slam、重定位和地图服务 |
| 赛道 | 默认 4×3 m 图片复刻、约 21.2 mm 线宽 | 实测尺寸、正式顺序、光照和污渍变化 |

共用配置见 [odin_sensors.yaml](../src/odin_racer/racer_description/config/odin_sensors.yaml)，投影及自定义 CameraInfo 见 [FishPoly](FISHPOLY_CAMERA_cn.md)。点云 `resolution_m=0.001` 是设置，不是实机 1 mm 精度。相机渲染外观，射线点云求交碰撞体，因此平面黑线不会形成线状雷达回波。模拟坐标使用 `odin_sim_*`，不能直接当实车标定。

物理、传感器和有序路线已有[仿真验证依据](../experiments/README_cn.md)。频率和实时因子取决于记录中的负载，400 Hz IMU 是目标而非保证。已有结果不能证明实车精度、停车距离、紧弯走廊或 Jetson 吞吐；应先用真实图像和运动标定主要误差，再细化外观。
