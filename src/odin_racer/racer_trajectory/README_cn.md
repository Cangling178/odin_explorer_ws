# racer_trajectory

[English](README.md) | 简体中文

有序路线进度与可行速度曲线。

## 状态

计划：分段拓扑、交叉点关联、曲率和加速/制动限制。赛道坐标尚未测量。

## 职责与验收

任务编号：TRACK-001, ROUTE-001, SPEED-001。参见根目录的架构与接口文档。
本包目前通过 ament_cmake 安装资源/文档。构建成功不代表规划中的子系统已经可以运行。

## 配置

所有 `*.template.yaml` 都是规格表，不是运行中的 ROS 参数文件。实现组件时再添加运行依赖、可执行程序和经过测试的参数。厂商代码和大型录制数据不放在本包中。

## 当前实现 — 2026-09-16

独立规划节点仍在规划中。有序进度和按曲率限制速度现已实现在 `lap_controller` 与 `lap_route.hpp` 中；预测制动仍待实现。

入口、参数与验收见[competition lap](../../../simulation/COMPETITION_LAP_cn.md).
