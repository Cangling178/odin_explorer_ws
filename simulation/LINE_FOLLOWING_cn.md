# C++ 独立场景低速视觉循线

[English](LINE_FOLLOWING.md) | 简体中文

完整比赛地图的预录路线辅助连续整圈入口见[整圈循迹](COMPETITION_LAP_cn.md)。

当前比赛地图右侧直线到下方波浪段的开发与复现见[地图波浪循线](COMPETITION_WAVES_cn.md)。

原独立验收范围：现有仿真车辆，在直线、左右圆弧、S 弯和单个左右直角场景中使用车载 FishPoly 图像跟踪。
交叉点选路、完整比赛跑圈、实车及正式比赛走廊不在本次验收范围内。实现不等于场景验收通过；
所有尝试、失败原因及重复矩阵结果见 [独立验证说明](ISOLATED_LINE_VALIDATION_cn.md)。

## 构建与启动

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --symlink-install
source install/local_setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
ros2 launch racer_bringup line_following.launch.py course:=line_corner_left gui:=false
```

车载仿真相机需要有效的 `DISPLAY`。使用空闲的 ROS domain 和 Gazebo master 端口。
`course` 支持 `line_straight`、原回归 `line_arc`、`line_left`、`line_right`、`line_s`、
`line_corner_left`、`line_corner_right`；`competition` 仅保留原入口，不保证完整路线。

默认不使能。在另一个已加载相同环境的终端查看状态并明确启动：

```bash
ros2 topic echo /sim/racer/line/tracking_status
# 上面的持续查看命令可另开终端；READY 后使能会实际驱动车辆。
ros2 service call /sim/racer/line/line_controller/enable std_srvs/srv/SetBool '{data: true}'
ros2 service call /sim/racer/line/line_controller/enable std_srvs/srv/SetBool '{data: false}'
```

场景参数以 YAML/JSON 映射传给场景生成器，例如：

```bash
ros2 launch racer_bringup line_following.launch.py course:=line_right \
  course_parameters:='{radius: 0.8, line_width: 0.021, spawn_y: 0.035, spawn_yaw: 0.08}'
```

几何参数只用于渲染和独立评测，不传入感知、控制节点。结束区域也只用于评测脚本的到达检查及
外部停车；运行控制器没有预设终点或场景方向信息。

完整地图底部S弯的左侧第一个波谷附近，可用以下初始位姿朝右出发：

```bash
ros2 launch racer_bringup line_following.launch.py course:=competition gui:=true \
  course_parameters:='{scale: 2.0, spawn_x: -1.20, spawn_y: -1.16, spawn_yaw: 0.0}'
```

该位置按重建地图纹理选取，不是正式起点。先关闭旧仿真再启动；默认仍不使能。
比赛地图现在默认以原纹理的2倍线性尺寸显示：地图从2×1.5 m变为4×3 m。
黑线宽度现在独立于地图比例，默认约21.2 mm，不再随地图加粗。
上面的S弯示例显式指定2倍比例。
地图缩放本身不改变车辆和相机内参；当前循线算法参数见下表。`scale: 1.0`可恢复原比例；显式`spawn_x/y`使用缩放后的世界米制坐标，
不会再次乘比例，默认起点则随地图缩放。GUI观察视点及可选俯视相机位置同步调整，原地图资源文件不变。
完整地图的紧凑S弯不属于原独立S弯验收矩阵；当前分段开发结果见[地图波浪循线](COMPETITION_WAVES_cn.md)。

## 感知实现

1. 缓存最近三张图像，优先处理与CameraInfo采集时间戳精确匹配的最新帧，避免两个DDS流交错时覆盖未配对图像。
   校验 FishPoly 六项畸变参数、内参及相机帧。
   通过原有 FishPoly 正投影和相机 TF，将地面米制网格重采样为灰度图，保留 skew，未改成针孔模型。
2. 对有效相机覆盖区域阈值化为黑线掩膜，使用 Zhang–Suen 细化得到中心线骨架。
   连通图使用八邻域，去掉已有正交连接的多余对角边，并清除连接到分叉的短终端噪声支路。
3. 在近车区域寻找唯一可用的连通分量。上一帧起点和方向用带采集时间的 TF 补偿后参与起点选择；
   提示过期或不可变换时重新保守选择。搜索考虑实际相机近边界，不能从远处任意黑线开始追踪。
4. 沿连接关系输出有序米制点，允许横向延伸和局部前向坐标减小。用沿线弧长衡量长度；不跨遮挡
   插值，也不以平滑弦线替代直角。局部厚度拒绝宽黑块，多出口截断且禁止控制继续驶入。
5. 在角点两侧使用约 65 mm 支撑检测方向突变并输出观测出口方向。控制器还会检查角点确实在路径上，
   排除角点前 35 mm 和起点裁剪边缘，使用至少 120 mm 的直线支撑拟合入口方向；支撑不足时不刷新转角记忆。
6. 无线、长度不足和多出口均有明确原因。原始图像近乎均匀（包括注入空白图）或投影/TF 失败时，
   图像健康标志为假。图像健康与路径有效性是不同字段。

`line_geometry.hpp` 中的算法可脱离 ROS 测试。`line_offline` 可重放保存的米制地面灰度 PNG；当前网格在输出前缀后追加参数`0.10 0.50`，不加参数时读取旧版网格。
程序输出骨架、掩膜、角点/出口叠加图和有序路径 JSON。固定阈值只对应当前仿真光照；置信度是工程质量分，并非统计概率。

## 弯道控制与时间补偿

`LineObservation` 将图像健康、路径、角点、出口数量及原始采集时间作为同一观测传输。
控制器把路径从采集时刻的 `base_link` 变换到轮式 `odom`，每个周期再用最新有效里程计变回车体坐标。
图像和 TF 经独立 DDS 流到达：控制器用最多五帧的先进先出队列保留待变换观测，等待 TF 时不阻塞控制定时器；只有成功
变换的观测才续期，缺失 TF 仍会触发原始采集时间的截止期限。重复或乱序数据不能续期。

路径检查从严格 `x` 递增改为有限值、逐段距离及总弧长检查。Pure Pursuit 选第一个向前的前视圆交点，
根据速度、路径曲率和可见距离调节前视，保持 0.12–0.45 m 的硬边界；前视还必须位于当前保留的已观测路径起点
之后。路径不足就停车。上一周期目标保存在 `odom` 中，新目标在当前路径弧长坐标和空间距离上都受
跳跃限制，避免跳到 S 弯另一段。速度受角速度上限和剩余观测长度对应的停车距离约束。

控制器在`odom`中保留进入相机近盲区的已观测点，仅拼接重叠的新路径，并替换重叠边缘以避免骨架毛刺累积。
普通弯道路径缓存默认最多12 s，`observed_path_memory`可配置；图像健康与TF仍须按0.35 s期限更新，里程计期限不变。
路径变短时减速。短时只看到侧面出口时，可进入`CURVE_ALIGN`，停止平移并转向最后观测切线，
取得新的可用图像路径后恢复；5 s内未重捕获则停车。这个流程与下面的单直角流程分开。

## 单个直角流程

```text
RUNNING → APPROACH → CORNER_STOP → TURN → REACQUIRE → RUNNING
                              故障 → STOPPED（锁存）
```

角点位置、入口和出口方向必须在至少三次不同采集帧中一致。接近阶段沿可靠入口方向低速前进并
按剩余距离减速，目标停车位置为轮轴中心在观测角点前约 80 mm。`CORNER_STOP` 等待有效里程计
确认线速度低于 5 mm/s、角速度低于 0.02 rad/s，且至少保持 0.3 s；停车无法完成会触发故障。

差速底盘的 `TURN` 为零平移、受限低角速度转向，方向来自图像观测出口。角点进入近盲区后，仅可
短时使用最后可靠的 `odom` 角点和出口，不能使用场景答案。默认记忆上限为 18 s、累计位移 0.45 m、
累计转角 1.9 rad；超限锁存停车。期间健康图像、TF 和里程计仍必须持续更新。

航向接近出口只允许进入 `REACQUIRE`，不允许直接前进。必须在三个不同采集时间重新看到有足够长度、
横向位置和方向一致的出口路径，才恢复跟踪；2.5 s 无法重捕获即故障停车。单角流程完成后不再重复
触发同一角点。本功能不实现交叉点选路和连续多个直角的路线规划。

故障 `STOPPED` 与主动停车 `CORNER_STOP` 完全分离。故障后数据恢复不会自动使能；需再次显式调用
使能服务。故障零速请求不经加速度整形，物理减速仍由底层控制器和接触模型决定。

## 参数与调试接口

| 参数 | 默认值 |
| --- | --- |
| 米制地面网格 | x=0.10–0.75 m，y=±0.50 m，5 mm 网格 |
| 地面平面 | base_link 下方 33.25 mm；平地近似 |
| 黑色阈值 / 线厚度 | 灰度 65 / 8–50 mm |
| 最小路径长度 / 起点横向范围 | 0.10 m / ±0.45 m |
| 正常速度 / 前视范围 | ≤0.05 m/s / 0.12–0.45 m |
| 角速度 / 线加速度 / 角加速度 | ≤0.5 rad/s / 0.15 m/s² / 0.8 rad/s² |
| 角点接近速度 / 转向角速度 | ≤0.04 m/s / ≤0.30 rad/s |
| 图像观测 / 里程计期限 | 0.35 s / 0.15 s，未来容差 0.02 s |
| 墙钟看门狗 / 控制定时器 | 1 s / 20 ms；非硬实时保证 |

配置：[感知](../src/odin_racer/racer_perception/config/line_perception.yaml)、
[控制](../src/odin_racer/racer_control/config/line_controller.yaml)。通过 `perception_config:=...`、
`controller_config:=...` 替换后重启生效。运行时参数热修改未实现。

以下话题前缀均为 `/sim/racer/line/`：

| 话题 | 内容 |
| --- | --- |
| `observation` | `racer_interfaces/LineObservation`，控制使用的原子观测 |
| `local_path` | `nav_msgs/Path`，相同采集时间的有序米制路径，供调试 |
| `perception_status` | 检测原因、置信度、截断原因及处理耗时（ms） |
| `ground_gray` / `black_mask` / `ground_debug` | 米制灰度图、掩膜、中心线与角点/出口叠加图 |
| `tracking_status` | 控制状态和停车原因，Transient Local |
| `control_debug` | JSON：状态、观测年龄、目标、前视、角点/出口里程计坐标、记忆用量及指令 |

调试图只在有订阅时发布。最终速度指令为 `/sim/racer/diff_drive_controller/cmd_vel`。
测试用 `image_topic`、`odom_topic`、`tf_topic` 可重映射到故障注入中继；默认直接连接仿真车载数据。
控制器不订阅 Gazebo 真值、俯视相机、场景几何或参考路径。

## 放大地图并保持原线宽

在2倍地图上保持此前右上角的对应位置和朝向，可使用（原2.5倍地图坐标乘以2/2.5）：

```bash
ros2 launch racer_bringup line_following.launch.py course:=competition gui:=true \
  course_parameters:='{scale: 2.0, line_width: 0.02116, spawn_x: 1.614118, spawn_y: 1.284377, spawn_yaw: -1.570796}'
```

`line_width`单位是世界坐标米，与`scale`独立。生成器从原纹理提取连通骨架，在4倍纹理分辨率上
按指定米制线宽重新绘制，不平滑切弯，不改变交叉点连接。原始PNG/DAE资源保持不变，
新纹理及引用它的DAE保存在本次仿真的临时资源目录。骨架保留原图的像素误差和局部毛刺；
这是约21 mm的统一工程线宽，并非逐点还原原图不均匀的笔画宽度。2.5倍地图直线实测约22 mm，
存在栅格误差。此前地图修改未改变车辆和独立场景；本轮感知、控制参数调整见上文。
关闭旧仿真后重新启动以加载新纹理；此前地图修改仅验证纹理线宽、连通性和生成资源，当前循线改动及分段证据见[地图波浪循线](COMPETITION_WAVES_cn.md)。

循线启动默认启用 `lockstep:=true` 与64 MiB Fast DDS共享内存配置，图像使用SensorDataQoS接收，图像期限仍为0.35 s、墙钟看门狗1 s。配置及传输问题说明见[地图波浪循线](COMPETITION_WAVES_cn.md)。
