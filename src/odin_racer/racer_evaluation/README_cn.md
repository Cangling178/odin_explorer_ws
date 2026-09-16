# racer_evaluation

[English](README.md) | 简体中文

比赛记录与指标导出集成。

## 状态

计划中的 ROS 集成：运行事件同步、录包导出和有序路线关联。`tools/` 中已有可用的独立 CSV 评测器。

## 职责与验收

任务编号：EVAL-001, EVAL-002。参见根目录的架构与接口文档。
本包目前通过 ament_cmake 安装资源/文档。构建成功不代表规划中的子系统已经可以运行。

## 配置

所有 `*.template.yaml` 都是规格表，不是运行中的 ROS 参数文件。实现组件时再添加运行依赖、可执行程序和经过测试的参数。厂商代码和大型录制数据不放在本包中。

## 当前实现 — 2026-09-16

本 ROS 包仍为骨架；可运行验收由 Python 工具 `validate_competition_lap.py`、`validate_lap_controller.py` 和 `repeat_competition_lap.py` 提供。

入口、参数与验收见[competition lap](../../../simulation/COMPETITION_LAP_cn.md).
