# 源码导航

本目录仅保留 `odin_explorer/` 下五个实际使用的 ROS 包。

- [explorer_description](odin_explorer/explorer_description/README.md)：机器人 Xacro、STL 和模型预览；安装几何仍需实测标定。
- [explorer_bringup](odin_explorer/explorer_bringup/README.md)：模型预览、人工建图、Jetson 导航和电脑 RViz 的统一启动入口。
- [explorer_localization](odin_explorer/explorer_localization/README.md)：ODIN 点云网关与 OctoMap 二维栅格建图接入。
- [explorer_odin](odin_explorer/explorer_odin/README.md)：C++ 位姿、TF 与实时点云适配；通过 PCL 过滤点云。
- [explorer_navigation](odin_explorer/explorer_navigation/README.md)：Nav2 实车参数与电脑 RViz 配置；导航算法直接使用官方组件。

[项目结构与接口](../docs/01_project.md) · [部署](../docs/02_deployment.md)
