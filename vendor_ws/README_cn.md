# ODIN1 厂商底层工作空间

[English](README.md) | 简体中文

已将厂商仓库克隆到 `src/odin_ros_driver`。厂商源码、SDK 二进制和底层工作空间构建产物不纳入上层 Git 仓库。`COLCON_IGNORE` 防止根目录意外发现这些包。自研构建在根目录使用 `--base-paths src`，不是在此目录执行。

导入前：核对精确驱动/固件组合并审阅构建脚本。厂商文档对目录布局有要求，因此包直接放在本底层工作空间的 `src/` 下。在本目录按审阅后的厂商流程构建；自研基础工程不会调用它。

导入提交、许可证、SDK 来源及本机构建/点云初检已记录在下方；实物固件和目标平台验收仍待完成。
先加载此底层工作空间，再加载自研叠加层。验收要求见[ODIN1 接入](../docs/04_odin1_integration_cn.md)。
厂商驱动已单独构建到本地 `vendor_ws/install/`；根目录的自研构建不会自动下载、构建或安装它。

## 源码导入记录 — 2026-09-11

- 上游：https://github.com/manifoldsdk/odin_ros_driver.git
- 导入时分支：`main`；驱动版本：`v0.14.4`。
- 导入提交：`f51051f2d861f7643d4d33d2ade2952efe1a4672`。
- 仓库许可证：Apache-2.0，保留上游 `LICENSE`。
- SDK 来源：同一上游提交中的 `lib/liblydHostApi_amd.a` 和 `lib/liblydHostApi_arm.a`。
- 上游要求固件：`v0.14.0`；实物固件尚未核对。
- 导入时未修改源码。未执行厂商构建脚本；后续构建与测试见下方记录。
- 此处记录下载的版本，不表示平台与固件组合已验收锁定。

构建审阅记录：`script/build_ros2.sh` 引用了未定义的 `WS_DIR`，并执行
`rm -rf build install log`。执行前需要明确构建流程。

## 本机构建与初步测试 — 2026-09-11

开发笔记本使用 Ubuntu 22.04 / ROS 2 Humble。用户提供的日志显示编译成功
（`1 package finished`），并确认已在 RViz 中看到点云。USB 枚举为
`2207:0019`，连接速率为 `5000M`。目前仅完成初步点云显示检查，图像、IMU、
里程计质量和车体集成仍待验证；实物固件尚未确认，不代表 Jetson 平台验收通过。

在项目根目录构建：

```bash
cd /home/cangling/odin_racer_ws
source /opt/ros/humble/setup.bash
CMAKE_BUILD_PARALLEL_LEVEL=2 colcon --log-base vendor_ws/log build \
  --base-paths vendor_ws/src \
  --build-base vendor_ws/build \
  --install-base vendor_ws/install \
  --packages-select odin_ros_driver \
  --executor sequential \
  --cmake-args -DBUILD_SYSTEM=ROS2
```

之后日常使用只需加载环境并启动；源码或安装资源未改变时，无需重新编译：

```bash
source /opt/ros/humble/setup.bash
source /home/cangling/odin_racer_ws/vendor_ws/install/setup.bash
ros2 launch odin_ros_driver odin1_ros2.launch.py
```

本次构建未使用 `--symlink-install`。修改源码中的 YAML 或 launch 文件后，
需再次构建以更新安装副本。也可通过 launch 的 `config_file` 参数直接指定
主驱动 YAML，但辅助节点仍读取安装目录的默认配置。厂商源码和构建产物仍被
Git 忽略，克隆主仓库后需另行获取。
