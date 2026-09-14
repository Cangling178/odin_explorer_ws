# Odin FishPoly 相机仿真

[English](FISHPOLY_CAMERA.md) | 简体中文

2026-09-14：台架与整车的 Odin 相机均采用设备 O1-P040100136 的 FishPoly 几何投影。
原始 [calib_device.yaml](../hardware/mechanical/odin1/calib_device.yaml) 未修改，构建时原样安装到
`share/racer_description/config/calib_device.yaml`。内参、畸变和输出尺寸来自该文件；相机相对外参沿用原有 Xacro。
比赛场景的固定俯视相机仍为针孔，属于检查仪器。

## 模型依据与参数

- [厂商数据输出说明 §5.3](https://github.com/ManifoldTechLtd/wiki/blob/master/docs/odin_series/odin1/5.%20Data%20output_.md)
- [厂商 PolynomialCamera 源码](https://github.com/manifoldsdk/odin_ros_driver/blob/main/include/polynomial_camera.hpp)，本机参考版本 `f51051f2d861f7643d4d33d2ade2952efe1a4672`
- [Gazebo Classic 广角相机](https://classic.gazebosim.org/tutorials?tut=wide_angle_camera)
- [ROS Humble CameraInfo 定义](https://github.com/ros2/common_interfaces/blob/humble/sensor_msgs/msg/CameraInfo.msg)

光学坐标为 X 向右、Y 向下、Z 向前。对点 `(X,Y,Z)`，令 `r=hypot(X,Y)`、`theta=atan2(r,Z)`：

```text
theta_d = theta + k2*theta^2 + k3*theta^3 + ... + k7*theta^7
xd = theta_d * X/r
yd = theta_d * Y/r
u = A11*xd + A12*yd + u0
v = A22*yd + v0
```

光轴处显式返回主点，避免除零。逆投影在前半球内采用 48 次有界二分；加载时检查多项式导数极值，拒绝非单调标定。
`p1=p2=0` 是当前支持条件，非零值会报错。`isFast/numDiff/maxIncidentAngle` 原样保留在标定档案中，
不作为本实现的求解设置；这里自行构建逐像素查找表，`maxIncidentAngle: 120` 不被当作图像视场。
FishPoly 包含连续二至七次项，不能将这六个系数直接传给 OpenCV fisheye 或 ROS equidistant 模型。

本机内参推算视场为水平 128.8504°、垂直 103.2996°、一条对角线 171.1627°，按边缘像素中心计算。
四角最大入射角约 86.18°；这些是模型计算值，不是实测视场，不强制拟合产品标称 129°×104°×173°。

## 渲染与接口

生成路径：Gazebo 场景 → 六面 cubemap → 2048×2048 等距中间图 → FishPoly 逆映射 → 1600×1296 RGB。
单个 cubemap 面默认 1024×1024；插件预计算 OpenCV 固定点采样表，每帧做双线性重采样。
中间图覆盖前半球，避免旧针孔图像缺少鱼眼四角射线。为避开广角着色器的边缘渐隐，插件拒绝过于接近 90° 的标定像素；本机标定完全覆盖且无黑边。
有限纹理分辨率、双线性插值和场景抗锯齿会影响细线与边界精度，不能当成真实镜头的成像分辨率。

实现入口：

- [数学模型](../src/odin_racer/racer_description/racer_description/fishpoly.py)：投影、逆投影、标定及 CameraInfo 读取。
- [Gazebo 插件](../src/odin_racer/racer_description/plugins/odin_fishpoly_camera.cpp)：等距渲染重映射与 ROS 发布。
- [共享配置](../src/odin_racer/racer_description/config/odin_sensors.yaml)：标定路径、渲染分辨率、10 Hz 更新频率和近远裁剪。
- [场景生成器](../src/odin_racer/racer_description/racer_description/sensor_world.py)：台架与整车共用，同步注入标定参数与消息尺寸。

配置 `calibration_file` 相对传感器配置目录解析，也可使用绝对路径。默认文件在源码运行时取自 hardware，安装后取自包内副本。
修改设备标定后需要重新构建并重启仿真。自定义标定只替换内参；若更换实体设备，还需单独核对相机外参。

原有 `/sim/odin1` 和 `/sim/racer/odin1` 命名空间保持不变：

| 话题 | 约定 |
| --- | --- |
| `image` | `sensor_msgs/Image`，rgb8，1600×1296，10 Hz |
| `camera_info` | 同帧采集时间戳与 `odin_sim_camera_optical`；Reliable、Volatile、depth=5 |

`camera_info` 使用项目自定义协议：`distortion_model="fishpoly"`，`D=[k2,k3,k4,k5,k6,k7]`，
`K=[[A11,A12,u0],[0,A22,v0],[0,0,1]]`，`R=I`，`P=0`，binning/ROI 默认值。
这里 K 保留非零 skew；P 为零表示本插件没有提供校正后的针孔投影，不能用它投影原始图像。
标准 ROS 图像管线不自动支持该协议；消费者应使用 `FishPoly.from_info(info)` 的 `project/unproject`。
若将来提供去畸变图像，需要另行发布对应的标准针孔 CameraInfo。

## 构建与验证

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-select racer_description racer_control racer_bringup
source install/setup.bash
python3 tools/check_workspace.py
python3 -m unittest discover -s tests -v
python3 tools/validate_fishpoly_render.py
```

新增构建依赖为 gazebo_dev、gazebo_ros、rclcpp、sensor_msgs 和 libopencv-dev。
角度靶标脚本需要 DISPLAY，自动启动并关闭独立 gzserver，默认 ROS domain 90、Gazebo 端口 11389，
可用 `--domain`、`--port` 指定空闲值。它使用同一场景生成器，移除地面和外壳遮挡，仅验证镜头几何。
输出在 `data/generated/fishpoly_render_validation.{json,png,log}`。

整车传感器检查按 [随车传感器说明](README_cn.md#随车-odin-传感器) 启动空场和 sensor_targets；
比赛场景按 [赛道验证说明](COMPETITION_COURSE_cn.md) 启动。两个验收脚本已适配 FishPoly；
彩色目标采用边缘密集采样，地面黑线通过 FishPoly 反投影射线与地面求交。

2026-09-14 本机验证结果：

| 检查 | 结果 |
| --- | --- |
| 构建与单元测试 | 三个包构建通过；27 项测试通过，含官方正投影对照、全画幅往返、光轴、FOV、非法模型拒绝 |
| 四角、边缘、中心、cubemap 接缝 | 13 个靶标全部检出，最大中心偏差 0.230 px；均匀背景无未渲染黑像素，图像/参数时间戳严格相等 |
| 随车静止、前进、左右转向、加减速 | 全部通过；目标边界最大误差 2.09 px，地面标记 2.99 px（阈值 8 px） |
| 独立台架 | 1600×1296 FishPoly 图像与参数匹配；图像/CameraInfo 10 Hz，点云约 9.35 Hz、IMU 约 332.2 Hz；静止重力检查通过 |
| 随车频率 | 图像/CameraInfo 10 Hz，点云约 10 Hz，IMU 约 399.1 Hz，按仿真时间计 |
| 比赛场景 | 前后两次随车黑线 IoU 0.9787/0.9777；俯视 IoU 0.8534/0.8518；短距离运动与地平面检查通过 |
| 比赛频率 | 图像/CameraInfo/点云约 10 Hz，俯视 2 Hz，IMU 约 332.3 Hz；未达到 IMU 配置的 400 Hz |
| 实时因子 | 随车约 0.57，比赛约 0.85；当前电脑与本次负载下的结果，不代表 Jetson 性能 |

台架结果保存在 `data/generated/fishpoly_bench_validation.json`。整车原始结果保存在 `data/generated/fishpoly_sim_sensors_validation.json` 和
`data/generated/fishpoly_competition_course_validation.json`，比赛前后图像同前缀。
这些结果验证几何投影和基础响应，不能替代实机图像对照或全赛道可见性验收。
仍未模拟曝光、运动模糊、噪声、暗角、JPEG 压缩与设备处理时延，也未实现厂商 SLAM。
