# 赛道来源与路线数据

[English](README.md) | 简体中文

[course_reference.jpg](reference/course_reference.jpg) 是负责人 2026-09-10 提供的原始附件，所有权不变。图中外部场地标注 200×150 cm，红色参考范围 161×120 cm；未确定正式起点／方向、交叉点顺序、线宽和评分容差。

| 数据 | 含义 |
| --- | --- |
| [reference_reconstruction.yaml](competition/reference_reconstruction.yaml) | 图片裁剪／提取及原始资源比例 |
| [course.template.yaml](competition/course.template.yaml)、[centerline.template.csv](competition/centerline.template.csv) | 未填写的实测赛道与有序路线记录 |
| [仿真路线](../src/odin_racer/racer_control/config/competition_lap.csv)、[元数据](../src/odin_racer/racer_control/config/competition_lap.json) | 按图片提取、用于所选 4×3 m 仿真的有序整圈 |

原始 PNG／DAE 提取资源对应 2×1.5 m；运行默认放大 2 倍为 4×3 m，线宽独立控制为约 21.2 mm。整圈生成器采用明确图片锚点和固定 4×3 m 换算；修改通用场景比例不会自动重建整圈路线。

[赛道生成与验证](../simulation/COMPETITION_COURSE_cn.md)记录纹理坐标及资源来源，[整圈运行](../simulation/COMPETITION_LAP_cn.md)记录选定通行顺序。这些是仿真输入，不是实测真值或正式比赛路线。实测样本使用米制有序分段和进度，保留交叉点不同访问，每次实验记录路线版本／哈希。
