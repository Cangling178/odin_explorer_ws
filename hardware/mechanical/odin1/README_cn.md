# Odin1 官方数模与安装

[English](README.md) | 简体中文

- [Product overview](https://manifoldtechltd.github.io/wiki/odin_series/odin1/1.%20Product%20Overview_.html)
- [Installation and CAD download](https://manifoldtechltd.github.io/wiki/odin_series/odin1/3.%20Installation%20Guide_.html)
- [Specifications](https://manifoldtechltd.github.io/wiki/odin_series/odin1/14.%20Technical%20Specifications_.html)
- [Original STEP](https://manifoldtechltd.github.io/wiki/odin_series/odin1/assets/stp/Odin1.stp)
- STEP SHA-256: `92a28478dfcfd8896e287ceecfa283515399f2cff61f0d86ff662433d29ac11f`.

本目录保留官方 STEP 原件；网格由 `tools/convert_odin_step.py` 生成，
需要 Gmsh 4.15.2 和 trimesh 5.1.0，单位由 mm 转为 m。
未自行声明厂商数模的再许可；权利归原权利人。

官方规格：主体宽 100、高 62、深 43 mm，重量约 280 g。
尺寸图含接头深度为 45.8 mm；实际下载数模包围盒为 100×62×46.4 mm，
保留原数模，不强行缩放到文档近似值。

`odin_link` 原点是底部四孔中心，X 向前、Y 向左、Z 向上。
数模转换 `(x,y,z)=(CAD_Z-20.4, -CAD_X, 31-CAD_Y)`，随后除以 1000。
这不是驱动的 imu/lidar/camera 坐标；尚未加入内部标定 TF 或模拟传感器。

按“车头四孔”解释为车头中央 84×30.3 mm 孔组（不是两侧万向球孔）：
CAD X=-41.742355/42.257645 mm，Z=-140.688953/-110.388953 mm。
孔旁表面高度已从网格核对为 Y=3.5 mm。直接贴板安装、正面朝前，
底部孔组中心位于 base_link 的 (205.538953, 0.257645, 32.25) mm。
官方底孔距为 84.3×30.7 mm，中心对齐后左右各差 0.15 mm、前后各差
0.20 mm；孔组并非精确一致，不据此断言螺钉能直接装配。
不新增未确认尺寸的支架，安装高度和俯仰尚需实车确认。

官方安装建议包括视野无遮挡、四周至少 10 mm 散热间隙，并强烈建议
设备底部离物体 0.2 m 以上。当前用户指定的贴板布局不满足该抬高建议，
视野、散热和与已有支撑结构的间隙仍需检查；这不是通过验收的硬件安装。

质量 0.280 kg 已加入；质心和惯性按均匀主体包围盒估算。
当前已赋质量小计 0.877 kg，不含车板、铜柱及其他电子设备，非整车总重。
