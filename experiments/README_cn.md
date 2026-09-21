# 验证依据与数据

[English](README.md) | 简体中文

此索引用于区分历史仿真证据与当前检查。**尚无实车循迹验收记录。** 更新文档不表示重跑动态测试，也不改写其原始源码哈希。

| 依据 | 版本／日期与范围 |
| --- | --- |
| [比赛整圈](competition_lap/RESULTS_cn.md) | 2026-09-16 选定路线：初始通过、0.05 m/s 独立启动 3/3 次及 0.10 m/s 单次通过；保留原门限和 JSON |
| [独立循线](isolated_line/RESULTS_cn.md) | 历史冻结版本 42 次跟踪＋12 次故障；后续波浪段证据在同页独立记录 |
| [FishPoly 相机](../simulation/FISHPOLY_CAMERA_cn.md) | 2026-09-14 几何、目标和赛道投影；保留原设备／模型约束 |
| 基础工程／接触／运动 | 2026-09-10–13 历史检查，下文概述 |
| 文档整理 | 2026-09-21 核对时仓库检查和 45 项 Python 测试通过；没有新增 Gazebo 或实车试验 |

## 保留的基础验证

初期包／预览检查对应早期骨架，不代表当前算法。2026-09-13 落地检查观察 10.036 仿真秒，稳定轴高约 33.1267 mm、名义 33.25 mm，只有两后轮和两前支撑触地。运动测试通过前后行驶、双向转向、圆弧、限幅及停车；0.1 m/s 指令断流后，约 0.30 s 观测到减速、0.60 s 达到停车阈值、额外行驶约 44.9 mm。这些是历史模型结果，不是实车制动限值。

本地报告为 `data/generated/ground_contact_validation.json`、`sim_drive_validation.json`、`sim_drive_with_sensors_validation.json` 和 `sim_sensors_validation.json`。旧针孔相机指标已由上方 FishPoly 记录取代。[部件复现命令](../simulation/README_cn.md)保留；早期逐次增加的测试总数不再作为当前回归数量。

## 数据与评测

[评测语义](../docs/08_evaluation_cn.md)定义时间加权、无效区间和有序关联。独立演示使用合成数据：

```bash
python3 tools/evaluate_run.py experiments/examples/synthetic_samples.csv   --metadata experiments/examples/synthetic_run.json
```

`run.template.yaml` 和 `results.csv` 是实验记录骨架，不是实车成绩。Git 保留来源／标定引用、小图、机器可读摘要和合成示例；大图、录包、日志、冻结二进制／源码快照保留在被忽略的 `data/generated/`。引用时保留路径、哈希、版本及条件，不将失败／开发运行混入冻结验收，也不因说明合并而删除底层证据。
