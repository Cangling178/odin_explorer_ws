# 独立克隆与精简记录

2026-09-21；新项目 **Odin Explorer**，工作空间 `/home/cangling/odin_explorer_ws`，包前缀 `explorer_`。

来源：`/home/cangling/odin_racer_ws`，提交 `4c90a5bb555000edf11772b69beb729c93b187bd`。使用 `git clone --no-hardlinks` 保留历史并独立存储；新分支 `explorer-foundation`。移除克隆生成的 origin，避免误推回原项目。原目录不参与修改。

保留：车体/电机/ODIN 外壳 Xacro 与网格、原始 CAD/设备标定、BOM 与未测规格、F4 协议、ODIN 接入资料、模型预览，以及硬件/定位/导航等必要接口规格。差速配置保留轮关节与物理接口约定，丢弃仿真参数。

删除：五个比赛相关包（control、perception、interfaces、trajectory、evaluation）、LineObservation、黑线算法与路线、赛道图片与世界生成、Gazebo/相机插件、模拟传感器 TF、比赛实验结果、原 tools/tests 与旧 CI。

六个保留包更名为 explorer_description、explorer_bringup、explorer_hardware、explorer_odin、explorer_localization、explorer_navigation。仅保留一个工作空间/模型检查工具和对应轻量 CI；不添加占位算法测试。

未复制旧 build/install/log 或生成数据。独立复制被忽略的 `vendor_ws/src/odin_ros_driver`，保留其自身 Git 历史与 SDK，提交 `f51051f2d861f7643d4d33d2ade2952efe1a4672`，不修改第三方命名。厂商构建产物需在新目录重新生成。

原实现和历史测试仍可在来源工程及本克隆历史追溯；新工程当前目录不保留。此次精简没有实现 F4、SLAM 栅格适配或自主导航，不继承旧仿真验收结论。

## 本次验证

六个包 colcon 构建通过；最小检查通过（依赖、40 份文档链接、Python 语法、16 个模型 link、网格资源）。无界面预览成功发布左右轮关节状态并正常退出。自研当前文件从 224 个减至 82 个，不含 Git 历史、构建产物及独立厂商源码。原工程 224 个受版本管理文件与 Git 索引的 SHA-256 核对未变化。没有进行实车、设备连接或导航测试。
