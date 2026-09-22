# ODIN 厂商工作空间

`src/odin_ros_driver` 是独立的厂商仓库，包含 SDK 和原始许可证，不随主仓库提交。`COLCON_IGNORE` 防止主工作区意外把它当作普通源码一起构建。

源码版本、补丁应用及 Jetson 构建顺序见[部署与构建](../docs/02_deployment.md)。按编号依次应用 `patches/` 中的补丁：

- [0001-respect-config-file.patch](patches/0001-respect-config-file.patch)：读取 launch 传入的 `config_file`。
- [0002-isolate-sdk-symbols.patch](patches/0002-isolate-sdk-symbols.patch)：隔离静态 SDK 的导出符号，避免同名 MD5 实现干扰 FastDDS 的同机识别。
- [0003-report-rgb-config-failure.patch](patches/0003-report-rgb-config-failure.patch)：记录 RGB 配置调用耗时和错误类别，明确配置是否得到确认；此项是诊断改善，不代表已修复设备应答超时。

- [0004-save-navigation-config.patch](patches/0004-save-navigation-config.patch)：保存当前实验室导航配置，包括主机时间模式、重定位模式和地图路径；换机时按实际工作区路径调整。

补丁不修改定位算法。SDK 符号隔离保留 DWARF 调试信息和帧指针，但 SDK 内部函数通过 `dladdr` 获取名称的能力会减少。

先加载 ROS 环境与本厂商工作空间，再加载自有工作空间。不要把电脑编译产物直接复制到 Jetson。
