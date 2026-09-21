# 源码导航

[English](README.md) | 简体中文

自研代码集中在 `src/odin_explorer/`。当前有六个 ROS 2 包；仅模型及预览有可运行实现，其余包保留开发所需的接口规格。

| 包 | 职责 | 当前实现 |
| --- | --- | --- |
| `explorer_description` | 车体、车轮、电机和 ODIN 外壳模型，部件坐标关系 | Xacro、STL、RViz 配置和预览启动 |
| `explorer_bringup` | 组合模块、配置运行模式和启动顺序 | 仅 `preview.launch.py`；无电机或设备连接 |
| `explorer_hardware` | 上位机与 F4 通信、轮反馈及差速底盘接口 | 规格模板；无通信实现或硬件插件 |
| `explorer_odin` | 厂商点云/位姿的数据、时钟与 TF 适配 | 规格模板；实际驱动在独立厂商空间 |
| `explorer_localization` | 连续里程计、全局定位和导航栅格接入 | 规格模板；无估计器或栅格生成实现 |
| `explorer_navigation` | Nav2 避障导航、探索目标选择和定点巡航 | 规格模板；无导航启动入口 |

每个包的 `package.xml` 声明 ROS 依赖，`CMakeLists.txt` 安装资源，`config/` 保存配置或设计规格；已实现的启动入口位于 `launch/`。只有 description 包包含 `urdf/` 与 `meshes/`。`*.template.yaml` 不是 ROS 运行参数。

`explorer_hardware` 运行在上位机；根目录 `firmware/` 用于将来运行在 F4 上的代码，目前只有协议说明。差速运动学由上位机完成，F4 负责轮速闭环与独立指令看门狗，相关实现仍待补全。

`vendor_ws/src/odin_ros_driver/` 是独立厂商仓库，不属于自研 `colcon build --base-paths src` 的范围，也不随主仓库 Git 推送。重新克隆后按[厂商说明](../vendor_ws/README_cn.md)获取锁定源码并单独构建。

模型尺寸和惯性含建模假设；真实设备安装外参仍需测量。预览发布虚拟轮关节状态，不能作为真实底盘反馈。

[工程结构](../README_cn.md#工程结构) · [架构与数据流](../docs/02_architecture_cn.md) · [开发流程](../docs/07_development_cn.md)
