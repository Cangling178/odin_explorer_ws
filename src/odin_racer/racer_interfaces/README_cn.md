# LineObservation 消息约定

[English](README.md) | 简体中文

接口版本 0.1.0。[LineObservation.msg](msg/LineObservation.msg) 通过 `path.header` 原子关联采集时间／坐标系、图像健康、路径有效性／置信度、角点和出口证据。几何量使用该坐标系；`image_valid` 只证明图像／投影健康，不表示一定看到线。

局部 `line_controller` 正常循线需要可用路径，拒绝多出口；角点／曲线机动只能有界复用已观测几何。`lap_controller` 使用图像健康与另行发布的地面 `black_mask` 对齐预录路线，局部 `path_valid=false` 本身不意味着整圈必须停车，图像／里程计时效和无视觉校正行驶距离限制仍生效。

消息没有仿真真值、场景身份或终点区域。[当前及拟定接口](../../../docs/06_interfaces_cn.md)区分已实现话题与实车计划。
