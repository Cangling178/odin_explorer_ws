# explorer_odin

C++ 位姿、TF 与实时点云适配；通过 PCL 过滤点云。

`/odin1/cloud_raw` 输入使用 Reliable，与当前厂商驱动发布端一致，避免大帧点云经 UDP 传输时无法恢复丢包。障碍物和清除点云输出保持 SensorDataQoS，供 Nav2 订阅。更换驱动时应确认其原始点云发布端仍支持 Reliable。

[项目结构与接口](../../../docs/01_project.md) · [部署与构建](../../../docs/02_deployment.md) · [导航与巡航](../../../docs/04_navigation.md)
