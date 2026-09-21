# 开发与最小检查

## 获取工程

仓库为公开仓库，可通过 HTTPS 直接克隆。主分支为 `main`。

```bash
git clone https://github.com/Cangling178/odin_explorer_ws.git
cd odin_explorer_ws
```

目录职责见[工程结构](../README_cn.md#工程结构)与[源码导航](../src/README_cn.md)。以下本机命令假定工作空间在 `/home/cangling/odin_explorer_ws`，其他机器请使用自己的克隆路径。

## 构建与检查

开发基线为 Ubuntu 22.04 / ROS 2 Humble。Jetson 镜像仍待验证。新终端只加载本工程及所需厂商空间，避免原工程 install 环境污染。

自研构建依赖：`ament_cmake`、`colcon`、`xacro`、`launch`、`launch_ros`、`ament_index_python`、`robot_state_publisher`、`joint_state_publisher`、`rviz2`；无需 Gazebo、OpenCV 或自定义消息生成器。

```bash
cd /home/cangling/odin_explorer_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install
source install/local_setup.bash
python3 tools/check_workspace.py
ros2 launch explorer_bringup preview.launch.py rviz:=false
```

`rosdep` 需事先初始化。预览退出按 Ctrl+C。该检查只验证包依赖、文档链接、Python 语法和展开模型中的网格、坐标树，不代表实车行为测试。

不保留旧比赛测试、世界生成和重复整圈脚本。后续只在新增实际功能时加入对应的协议错误输入、超时停车、时序/TF 和导航行为测试，不测试空占位包。

厂商构建见[厂商说明](../vendor_ws/README_cn.md)。本地 build/install/log、地图和录包不纳入版本管理。

## 修改放在哪里

- 上位机功能放在对应 `explorer_*` 包，统一启动放在 `explorer_bringup/launch/`。
- F4 固件放 `firmware/`，接线、实测参数和安装标定放 `hardware/`。
- 原始录包和地图分别放 `data/bags/`、`data/maps/`，按需创建；文档只提交可审查摘要。
- 厂商源码保留独立版本，不在主工程提交 SDK 或厂商构建产物。
- 中英文说明同步更新；新运动功能实现后再添加有针对性的验证。

当前唯一可运行入口是模型预览；构建成功不能代替底盘、定位或导航验收。
