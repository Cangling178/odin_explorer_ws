# explorer_bringup

模型预览、人工建图、Jetson 导航和电脑 RViz 的统一启动入口。

Jetson 启动 `navigation_jetson.launch.py`，电脑本地启动 `navigation_rviz.launch.py`。本次跨机验证使用 `ROS_DOMAIN_ID=35`、`ROS_LOCALHOST_ONLY=0` 和 `rmw_fastrtps_cpp`；具体命令见部署文档。

[项目结构与接口](../../../docs/01_project.md) · [部署与构建](../../../docs/02_deployment.md) · [导航与巡航](../../../docs/04_navigation.md)
