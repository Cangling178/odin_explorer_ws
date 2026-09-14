# 赛道资源

[English](README.md) | 简体中文

`reference/` 保存给定图片和标注来源。`competition/` 保存未填写的测量/路线规格，以及实测样本 CSV 表头。目前没有把任何推测的黑线坐标或分支顺序当作真值。

`competition/reference_reconstruction.yaml` 单独记录图片提取参数，用于生成
[Gazebo 比赛参考图赛道](../simulation/COMPETITION_COURSE_cn.md)。该复刻场景可供相机观察，
不替代实测路线或交叉点通行顺序。

每次运行都保留赛道版本和哈希。按顺序存储以米为单位的中心线样本，带分段 ID 和累计距离。自交点可能存在 x/y 相同、但属于不同路线访问的点。不能按 x 排序或全局最近邻来构造通行顺序。
