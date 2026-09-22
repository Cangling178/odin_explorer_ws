# explorer_navigation

Nav2 实车参数与电脑 RViz 配置；导航算法直接使用官方组件。

2026-09-23 已在 Jetson 实机输入下验证明显障碍绕行、近距离直行规划、速度输出和取消归零。局部与全局代价地图接收过滤后的障碍点云；低矮小簇参数属于 `explorer_odin`。实际行驶及实车巡航待底盘执行接口接入后联调。

[项目结构与接口](../../../docs/01_project.md) · [部署与构建](../../../docs/02_deployment.md) · [导航与巡航](../../../docs/04_navigation.md)
