# 硬件资料

[English](README.md) | 简体中文

这里保存硬件事实和建模假设，上位机／固件接入及标定步骤统一见[实车联调](../docs/09_bringup_cn.md)。

| 资料 | 范围 |
| --- | --- |
| [bom.csv](bom.csv) | 清单及待核对的电气／设备信息 |
| [robot_spec.template.yaml](robot_spec.template.yaml) | 未填写完整的实测机器人规格，不是运行参数 |
| [platform_lock.template.yaml](platform_lock.template.yaml) | 目标系统／JetPack、驱动和固件锁定表，尚未验收 |
| [底盘记录](mechanical/chassis_plate/README_cn.md) | CAD 来源、已确认／参考尺寸、假设及转换 |
| [ODIN 记录](mechanical/odin1/README_cn.md) | CAD 来源、安装假设与设备标定 |

后双驱动电机、前被动支撑和 F4 已确认。机械参考资料记录 MG513X GMR 500 线、1:28 电机；实际额定值、输出轴每转计数、驱动器、F4 板和通信待核实。开发机已有设备点云显示记录，不能据此认定 Jetson 就绪。

有接线／供电资料后再建立 `electrical/`，有实测数据和残差后建立 `calibration/<revision>/`，空目录占位说明已移除。未知规格保持未填；原始 CAD、设备标定和参考值不等于完整实测整车模型。
