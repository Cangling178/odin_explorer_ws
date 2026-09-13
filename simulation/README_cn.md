# 仿真计划

[English](README.md) | 简体中文

已添加 Gazebo Classic 11 独立 Odin1 传感器测试场景；整车接触与驱动尚未接入。确定 ROS/JetPack 和驱动模型后再选择仿真器；条件允许时，在工作站运行计算量大的仿真。

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
