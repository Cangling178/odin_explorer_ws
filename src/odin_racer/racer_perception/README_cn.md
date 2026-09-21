# racer_perception

[English](README.md) | 简体中文

C++17 `line_perception` 使用同帧 FishPoly 图像／CameraInfo 和采集时刻 TF 投影平地网格，发布 `LineObservation`、地面掩膜及调试图。`line_offline` 支持图像回放，几何实现位于 `include/racer_perception/line_geometry.hpp`。

两套控制器共用本节点：局部循线使用路径／角点证据，整圈使用图像健康与 `black_mask` 对齐地图。配置为 `config/line_perception.yaml`。[算法与接口](../../../simulation/LINE_FOLLOWING_cn.md) · [相机约定](../../../simulation/FISHPOLY_CAMERA_cn.md)。
真实图像标定、安装和时序仍需[实车验证](../../../docs/09_bringup_cn.md)。
