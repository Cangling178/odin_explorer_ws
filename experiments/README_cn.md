# 实验

[English](README.md) | 简体中文

每次真实运行复制 `run.template.yaml` 并填写全部来源字段。简要结果保存在 `results.csv`；大型依据文件放在不纳入 Git 的 `data/` 或外部存储，并记录哈希和路径。未完成的尝试也要记录。

`examples/` 是用于运行离线工具的合成数据目录，不能计入机器人实测结果。后续 bag 到 CSV 的适配器必须保留无效样本，并关联正确赛道分段。

`run.template.yaml` 是完整实验档案模板；评测器的 `--metadata` 只接受 JSON，不能直接传入这个 YAML 文件。参考 [synthetic_run.json](examples/synthetic_run.json) 填写对应运行的 JSON 元数据；必填字段和指标定义见[评测说明](../docs/08_evaluation_cn.md)。
