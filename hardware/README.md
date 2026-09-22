# 机器人模型与硬件资料

保留本项目所用底盘、ODIN 数模、设备标定和部件清单。模型几何不等于实测传感器安装外参；导航使用的 `base_to_imu` 需要独立测量。

- [底盘与电机模型说明](mechanical/chassis_plate/README.md)
- [ODIN 数模与安装说明](mechanical/odin1/README.md)
- [部件清单](bom.csv)
- [设备标定原件](mechanical/odin1/calib_device.yaml)
- [导航标定与地图对齐](../docs/04_navigation.md)

未填实测数值的通用模板已移除。实测包络、点云高度和车体外参直接按导航文档填写运行参数；本阶段不包含下位机程序或底盘通信。
