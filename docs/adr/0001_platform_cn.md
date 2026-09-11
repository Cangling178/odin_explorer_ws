# ADR-0001：平台基线

[English](0001_platform.md) | 简体中文

状态：提案，2026-09-10。

背景：目标平台为 Jetson Orin Nano，ODIN1 驱动对版本敏感。查阅时厂商 README 倾向使用 Humble/Ubuntu 22.04。开发主机已安装 Humble，但这不能证明目标 Jetson 的系统镜像版本。

决定：以 Humble 作为基础构建目标，评估兼容的 JetPack 6.x/Ubuntu 22.04 目标平台。目前不刷写 Jetson，也不宣称已锁定驱动。

影响：需要共同验证厂商 ARM64 资源、固件和 CUDA/OpenCV 兼容性。新版 ROS/JetPack 只有通过厂商驱动测试后才可考虑。长期部署前评估发行版支持周期和升级工作量。在硬件冒烟测试后锁定精确版本，不根据搜索摘要锁定。

验证：目标平台清单、厂商底层工作空间构建，以及带时间戳的传感器采集。
