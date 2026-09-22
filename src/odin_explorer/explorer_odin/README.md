# explorer_odin

C++ 位姿、TF 与实时点云适配；通过 PCL 过滤点云。

障碍标记前增加低矮小簇过滤：在车体坐标系中，以 4 cm 邻接距离聚类，
丢弃最长边不超过 25 cm、最高点不超过 `base_link` 上方 4 cm 的点簇。
高于该高度的细杆和更大的点簇保留；清除点云不经过此过滤。
这些阈值按当前近处低矮回波设置，也会忽略符合范围的真实小物体。
参数位于 `config/nav_adapter.yaml`，`small_cluster_max_extent: 0.0` 可关闭过滤。
修改后重启适配器生效；已进入代价地图的旧占据仍需射线观测清除。

`/odin1/cloud_raw` 输入使用 Reliable，与当前厂商驱动发布端一致，避免大帧点云经 UDP 传输时无法恢复丢包。障碍物和清除点云输出保持 SensorDataQoS，供 Nav2 订阅。更换驱动时应确认其原始点云发布端仍支持 Reliable。

[项目结构与接口](../../../docs/01_project.md) · [部署与构建](../../../docs/02_deployment.md) · [导航与巡航](../../../docs/04_navigation.md)

构建测试：`BUILD_TESTING=ON` 后执行 `ctest --test-dir build/explorer_odin --output-on-failure`。实机效果与测试边界见[2026-09-23 验证记录](../../../docs/diagnostics/2026-09-23-navigation-validation.md)。
