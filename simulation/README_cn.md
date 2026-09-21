# 仿真运行入口

[English](README.md) | 简体中文

当前后端为开发机上的 Gazebo Classic 11／ROS 2 Humble，比赛地图默认 4×3 m。[模型假设](MODEL_cn.md)和[历史验证](../experiments/README_cn.md)与运行命令分开维护。

## 选择入口

| 目的 | 入口／说明 |
| --- | --- |
| 连续完整跑圈 | [competition_lap.launch.py](COMPETITION_LAP_cn.md) |
| 局部视觉循线和角点实验 | [line_following.launch.py](LINE_FOLLOWING_cn.md) |
| 比赛纹理、比例与投影检查 | [赛道世界](COMPETITION_COURSE_cn.md) |
| FishPoly 投影及相机验证 | [相机模型](FISHPOLY_CAMERA_cn.md) |
| 底盘运动、传感器目标或落地检查 | 下文命令 |

先按[开发流程](../docs/07_development_cn.md)构建。在每个测试终端加载：

```bash
source /opt/ros/humble/setup.bash
source install/local_setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
```

使用空闲 ROS domain／master 组合，同一时间只运行一个世界。`gui:=false` 只隐藏窗口，相机仍需可用 DISPLAY。传感器使用者设置 `use_sim_time=true`，两套循线控制器不可争用指令出口。

## 底盘运动

```bash
ros2 launch racer_bringup simulation.launch.py
```

启动轮状态广播器和差速控制器，不自动发送运动指令。在相同环境的另一终端执行下列测试，会主动驱动仿真车辆：

```bash
ros2 control list_controllers -c /sim/racer/controller_manager
python3 tools/validate_sim_drive.py --output data/generated/sim_drive_validation.json
```

验证器用轮反馈与独立真值检查前后行驶、双向转向、圆弧、饱和、零指令、旧指令及断流；结束发送零速，运行时不要有其他指令发布者。不需要相机的底盘检查可用 `sensors:=false`。

## 随车传感器目标

每次传感器验证使用新启动的世界：

```bash
ros2 launch racer_bringup simulation.launch.py gui:=false sensor_targets:=true
```

在匹配环境的第二终端执行：

```bash
python3 tools/validate_sim_sensors.py --output data/generated/sim_sensors_validation.json
```

验证器会主动移动车辆。检查停车后的 FishPoly 目标边界（8 px）、点云目标／地面 P95 距离（20／10 mm）、IMU 响应、TF 和消息时效／频率。LinkStates 没有采集时间戳，运动对照仅为基础响应检查，不是精密时序标定。此目标验证使用空场，不用于 `course:=competition`。

## 地面接触

```bash
ros2 launch racer_description ground_contact.launch.py gui:=false
```

随后仅在该隔离落地世界执行：

```bash
python3 tools/validate_ground_contact.py --reset --output data/generated/ground_contact_validation.json
```

`--reset` 会复位整个测试世界。此场景有重力和被动车轮，没有驱动指令、车辆 TF 或 Odin 输出；采用已有 0.877 kg 质量小计和 25 个碰撞体。验证器观察 10 仿真秒，后 5 秒要求高度误差 <1 mm、垂直波动 <0.5 mm、水平漂移 <1 mm、速度 <0.005 m/s、角速度 <0.02 rad/s、姿态偏转 <0.5°。`contact_config:=/absolute/path/config.yaml` 可替换接触设置。

## 独立 Odin 台架

```bash
ros2 launch racer_description odin_sensors.launch.py gui:=false
```

固定台架设备高 0.5 m、目标在前方 2 m，不代表实车安装。关闭竞争发布 TF 的预览／台架节点。话题前缀为 `/sim/odin1/`，而非 `/sim/racer/odin1/`。world 文件是场景生成模板，不能当成完整传感器世界直接运行。

## 整车接口与选项

| 接口 | 含义 |
| --- | --- |
| `/sim/racer/diff_drive_controller/cmd_vel` | `TwistStamped` 输入，使用 `/clock` 时间戳 |
| `/sim/racer/diff_drive_controller/cmd_vel_out` | 限幅指令 |
| `/sim/racer/diff_drive_controller/odom` | 轮位置反馈里程计 |
| `/sim/racer/joint_states` | 实际仿真关节状态 |
| `/sim/racer/tf`、`/sim/racer/tf_static` | 局部里程计及机器人变换 |
| `/sim/racer/odin1/image`、`camera_info` | FishPoly 图像及同帧标定 |
| `/sim/racer/odin1/cloud_raw`、`imu` | 射线点云及理想 IMU |
| `/contact_test/link_states`、`get_entity_state` | 仅供评测的 Gazebo 真值 |

使用者将 `/tf`、`/tf_static` 重映射至整车命名空间。RViz 图像显示用 Reliable／Volatile、depth 5；点云和 IMU 用 sensor-data QoS。循线启动配置 lockstep 和扩大的 DDS 共享内存，详见[局部循线](LINE_FOLLOWING_cn.md)。

`controllers:=...`、`sensor_config:=...`、`contact_config:=...` 选择配置文件，修改后重启。`sensor_targets` 默认 false，不能与比赛场景混用。比赛场景 `course_overview:=true` 添加仅供评测的俯视相机。配置与物理限制集中在[模型范围](MODEL_cn.md)。
