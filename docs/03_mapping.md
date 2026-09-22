# 03 建图与地图


导航新增的小簇过滤只属于 `odin_nav_adapter`，不改变本页的建图网关或已保存的栅格地图。导航配置当前使用时间模式 `1`；建图若使用下述模式 `2`，应使用独立建图配置，不直接改动正在使用的导航配置。

当前实现适用于人工移动、平整地面的实验室建图。沿用 ODIN 自带定位，`octomap_server` 在线构建三维占据地图并投影为 `/map`。没有启动底盘、Nav2 或自主探索，也没有实现厂商回环后的历史地图重建。

## 安装与构建

```bash
cd /home/cangling/odin_explorer_ws
source /opt/ros/humble/setup.bash
sudo apt install ros-humble-octomap-server ros-humble-nav2-map-server
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install
source install/local_setup.bash
```

厂商驱动按[厂商说明](02_deployment.md)单独构建。`start_driver:=false` 默认接收已运行的驱动或录包，不需要安装 SDK。`start_driver:=true` 则需要先加载 `vendor_ws/install/local_setup.bash`，只启动厂商 `host_sdk_sample`，不启动深度补全、图像叠加及另一套 RViz。不要同时运行两个驱动实例。

检查厂商配置 `senddtof: 1`、`sendodom: 1`、`send_odom_baselink_tf: 1`；`custom_map_mode: 1` 为厂商 SLAM 模式。不要因本工程已有预览模型而添加虚假的 `base_link` 到雷达标定。适配沿用驱动实际发布的 `odom → imu → lidar` ；当前驱动仅在重定位模式（`custom_map_mode: 2`）发布 `odom → map`。建图模式默认使用 `odom` 固定坐标，本模块不伪造 `map` TF。`/map` 是输出话题名，其 `header.frame_id` 默认为 `odom`。

厂商默认 `use_host_ros_time: 0` 使用设备启动后的秒数，不能直接与主机 ROS 时间比较。当前网关要求统一时间轴：在实际使用的厂商配置 `register_keys` 下设置 `use_host_ros_time: 2`，重启驱动，等待时间对齐稳定，再开始建图。检查点云 header 时间是否接近主机当前时间；若仍有大偏差，先排查厂商 PTP 对齐，不要关闭过期检查或只改点云时间戳。仅有设备启动时间的旧录包不能直接套用这里的 `--clock` 回放流程，需要点云、TF 和回放时钟一致的时间转换。

## 确定地面高度后启动

`floor_z` 是 **建图固定坐标系中的地板 Z 值（默认 odom）**，不是设备安装高度，也不一定为 0。先启动驱动，在 RViz 以 `odom` 为 Fixed Frame 显示 `/odin1/cloud_raw`，用 Publish Point 工具选择地板并查看 `/clicked_point` 的 Z；在多处平整地板取值。若使用其他测量方式，仍须转换到同一个建图固定坐标系。此工具不会改变机器人位姿。

以下 `-0.35` 仅为测量结果的示例，必须换成实测值：

```bash
# 驱动已运行：
ros2 launch explorer_bringup mapping.launch.py floor_z:=-0.35

# 或在加载厂商环境后，一并启动厂商 SDK：
ros2 launch explorer_bringup mapping.launch.py floor_z:=-0.35 start_driver:=true

# 无图形界面：
ros2 launch explorer_bringup mapping.launch.py floor_z:=-0.35 rviz:=false
```

可传 `driver_config:=/absolute/path/control_command.yaml` 指定厂商配置；可用 `params_file:=/absolute/path/octomap.yaml` 覆盖地图参数文件。启动参数可用 `--show-args` 查看。仅在确有独立且持续有效的 map TF 时使用 `mapping_frame:=map`；RViz 会同步切换，`floor_z` 也必须改用该坐标系下的测量值。

默认配置为 5 cm 栅格、5 Hz 最大点云插入频率、5 m 射线最大范围、地板以上 0.08–1.0 m 的二维障碍投影区间。它们是实验起点，不是实车验收值：

- `obstacle_height` 应覆盖实际车体可能碰撞的最高位置。
- `ground_clearance` 是忽略的地板高度带，默认 8 cm 也会漏掉该带内的小障碍，必须按地面噪声和底盘通过能力调小验证。
- 高度范围相对固定建图坐标系的地板平面；不适用于坡道、多层楼或明显倾斜的地图。
- 保留地面附近点参与三维射线更新，但通过 `occupancy_min_z/max_z` 排除地板的二维占据投影；无需尚未标定的 `base_footprint` 地面分割。
- 调节分辨率、射线范围和 YAML 中的 `max_rate`，实测 Orin Nano 的处理延迟与地图更新频率。5 Hz 是上限，不是性能承诺。

## 数据与状态

```text
/odin1/cloud_raw + 厂商采集时刻 TF
  → odin_cloud_gate
  → /sensors/odin/points
  → octomap_server
  → /map (nav_msgs/OccupancyGrid)
```

网关只接受 `lidar` 坐标系下的当前帧点云，不改变原始坐标和时间戳。默认拒绝 `/odin1/cloud_slam` 的 `odom` 坐标系，也不接受把累计点云伪装成雷达帧。没有运动去畸变功能；快速手持旋转仍可能造成重影。

网关检查 XYZ FLOAT32 字段、消息布局、时间戳和采集时刻 TF，队列最多 10 帧，默认过期 0.5 秒。过期、乱序、超前超过 0.1 秒及缺失 TF 的点云不插入。点云采用 SensorData QoS，地图和状态可供晚加入订阅者获取。

```bash
ros2 topic echo /mapping/status --qos-durability transient_local
ros2 topic hz /sensors/odin/points
ros2 topic info /map --verbose
```

`mapping` 只表示网关正在转发，不代表 OctoMap 已完成处理或导航可用。`waiting_for_acquisition_tf` 表示缺少采集时刻的 TF，检查驱动 TF 开关、时钟与录包内容。`waiting_for_fresh_cloud` 表示数据中断。`rejected_*` 表示输入格式、坐标系或时间不合约。

## 回环、重定位和重置边界

**默认 odom 模式没有独立的 map/odom 修正信号，无法可靠检测厂商回环，仍可能出现重影；发现位姿跳变或重影后应结束本次建图并检查。**

仅在 `mapping_frame:=map` 等独立全局坐标模式下，网关比较当前 `map ← odom` 与首次接收点云时的变换。累计平移变化超过 0.15 m 或转动超过 0.10 rad 时，状态锁存为 `halted`，停止转发；所有模式下 ROS 时钟倒退也会锁存停止。阈值在 YAML 中配置，不会因变换恢复而自动继续。

这是一项错误累积保护，**不是回环修复**。阈值以内的修正仍可能造成误差；没有 `map/odom` 变化的设备复位或未暴露的历史轨迹调整无法可靠识别。暂停前已经发布的地图仍保留在 `/map`，不能作为继续探索或自动导航的有效性保证。状态仅用于检查建图过程，不发送底盘停车指令。建图与已保存地图导航分别运行。

出现 `halted` 后，停止整个 mapping launch，再重新启动以建立一张新地图；地面高度也需重新核对。**不要只调用 OctoMap reset 服务或只重启网关**：两侧必须同时开始新会话。默认不会删除已保存的地图文件，也不会静默清空正在积累的地图。要保留回环前后的完整一致地图，需要厂商提供修正后的历史位姿，并实现重放/重建或子图后端。

## 保存、录制和回放

```bash
mkdir -p data/maps data/bags
ros2 run nav2_map_server map_saver_cli -f data/maps/lab
ros2 bag record -o data/bags/lab /odin1/cloud_raw /tf /tf_static
```

地图保存生成 YAML + PGM，供后续地图服务器读取；不包含定位轨迹，不是厂商重定位地图。仅在 `/map` 有效且检查状态后保存。晚启动录包须核对 `/tf_static` 是否实际录入；厂商有些外参通过 `/tf` 动态发布。

回放使用两个终端，均加载 ROS 和本工程环境，不启动实机驱动：

```bash
ros2 launch explorer_bringup mapping.launch.py floor_z:=-0.35 use_sim_time:=true
ros2 bag play data/bags/lab --clock
```

不要在同一建图会话使用 `--loop` 或向后 seek；时间倒退会暂停网关。若原包未提供 map/odom/lidar 的完整 TF，不能仅靠点云恢复正确的空闲射线。

## 已有地图对齐记录

本地 `data/results/alignment/` 保留 `lab_02.bin` 与 `lab_01_edit.yaml` 的历史离线对齐报告、拟合结果和图片。这些文件与本项目地图有关，整理时保留；一次性的配准验证脚本、下载工具和中间缓存已清理。报告中的平面变换只是拟合候选，未验证设备实时重定位坐标，不应未经核对直接作为导航外参。

## 现场检查

检查静止墙体是否稳定、平移时端点与射线是否一致、桌腿和门框是否可见、地板是否被排除、盲区是否保持未知。绕行回到起点后检查重影；地图保存与重定位使用两类不同文件，不能互相替代。

本项目不再保留合成建图测试脚本；既往软件验证不能替代 ODIN 与 Jetson 的实际建图检查。传感器安装与地图坐标对齐见[导航说明](04_navigation.md)。

上游：[OctoMap ROS 2](https://github.com/OctoMap/octomap_mapping/tree/ros2)。本项目通过依赖使用上游，不复制其算法。

[返回项目首页](../README.md) · [下一步：导航与巡航](04_navigation.md)
