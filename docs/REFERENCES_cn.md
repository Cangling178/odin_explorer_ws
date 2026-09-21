# 一手参考资料

[English](REFERENCES.md) | 简体中文

外部资料原核对日期为 2026-09-10，本次仅整理本地引用，不声明其在线内容已重新核验。已导入驱动的精确版本见[厂商记录](../vendor_ws/README_cn.md)；其余为设计参考，实际接入使用版本匹配文档。

| 来源 | 采用的信息 | 适用范围 |
| --- | --- | --- |
| [ODIN1 产品](https://www.manifoldtech.cn/products/odin1/) | 感知输出种类和宣称的位姿精度 | 产品能力；仍需验证实际设备 |
| [ODIN1 厂商驱动](https://github.com/manifoldsdk/odin_ros_driver) | Humble/Ubuntu 22.04 基线和固件匹配 | 已导入版本见厂商记录，目标平台待验收 |
| [ODIN1 厂商数据文档](https://github.com/ManifoldTechLtd/wiki/blob/master/docs/odin_series/odin1/5.%20Data%20output_.md) | 设备专属相机模型和坐标转换问题 | 适配 CameraInfo/TF 前审阅 |
| [Odin-Nav-Stack](https://github.com/ManifoldTechLtd/Odin-Nav-Stack) | 已有 ODIN1 导航集成 | ROS 1 / Go2 示例；未导入 |
| [JetPack 6.2.1 发布说明](https://docs.nvidia.com/jetson/jetpack/6.2.1/release-notes/index.html) | Orin 支持和 L4T 36.4.4 基线参考 | 6.x 版本示例，不代表最新版本 |
| [当前 Orin Nano 安装说明](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/quick_start.html) | 独立于驱动支持情况核查平台选项 | 新版 JetPack 不代表厂商用户态兼容 |
| [Humble diff_drive_controller](https://control.ros.org/humble/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html) | 已用于仿真的车轮控制器及指令／TF 约定 | 后轮差速布局已确认；参数待测 |
| [Nav2 Regulated Pure Pursuit](https://docs.nav2.org/rolling/configuration_and_development/configuration_guide/controller_plugins/configuring_regulated_pp/) | 基于曲率调节速度的概念 | Rolling 参考；实现前重查 Humble API |
| [Clearpath 机器人软件栈](https://github.com/clearpathrobotics/clearpath_robot) | 硬件、传感器、配置和测试的职责划分 | 组织方式参考；未复制源码 |

架构实现状态、实车关卡和内部指标分别以对应文档为准。给定赛道图片是用户提供的依据，不是完整官方规则。
