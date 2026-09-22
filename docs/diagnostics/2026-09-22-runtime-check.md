# ODIN 导航运行排查（2026-09-22）

本文保留当日排查证据。后续 Jetson 部署和导航测试见[2026-09-23 实机验证](2026-09-23-navigation-validation.md)，不以本文历史进程状态描述当前运行。

以下记录修复前的排查，检查对象为 21:53 启动的导航进程：驱动 PID 11785、适配器 PID 11787、RViz PID 12003。运行配置已使用 `use_host_ros_time: 1`。排查阶段未重启设备、未发送运动命令，也未更改导航代码或运行配置。后续用户授权的正式代码修改与构建结果见文末“修复落实”。

## 结论与处理顺序

1. 点云低频确实影响导航适配器，但设备和驱动本身仍约 10.26 Hz。丢帧发生在驱动至适配器的 DDS/UDP 接收链路。
2. 已发现 SDK 与 FastDDS 的同名 MD5 符号冲突，影响主机标识计算；运行中的驱动和其他 ROS 节点因而没有正常使用彼此的共享内存。实际 UDP 接收缓冲区为 212992 字节，适配器接收丢包持续增长。
3. 将适配器点云输入改为 Reliable 已在隔离副本中验证，输出恢复约 10.25 Hz。永久修复还应隔离 SDK 的动态导出符号，消除冲突源头。
4. RGB 参数失败是控制应答接收失败/超时，当前数据流正常；不是已证实的分辨率或帧率组合错误。
5. RViz 着色器日志高度符合已知的首次初始化验证告警，优先级低于前两项。

## 点云：设备正常，传输丢帧

### 设备端与驱动回调

设备状态文件：

`src/odin_ros_driver/log/Driver_20260922_215339/Conn_20260922_215340/dev_status.csv`

检查期间最近 100 条记录：

| 指标 | 最小值 | 均值 | 最大值 |
| --- | ---: | ---: | ---: |
| DTOF TX Hz | 10.16 | 10.266 | 10.36 |
| DTOF RX Hz | 10.06 | 10.258 | 10.48 |
| RGB TX Hz | 10.19 | 10.259 | 10.34 |
| RGB RX Hz | 10.18 | 10.258 | 10.33 |
| 设备 CPU 温度 °C | 48 | 48.84 | 50 |

驱动 `lidar_data_callback()` 在执行 `publishIntensityCloud()` 后更新 DTOF RX 统计。这不仅是设备声称在发数据，也说明主机驱动回调与发布路径持续运行。

USB 当前为 5000M 链路；主机可用内存约 20 GiB、未使用交换空间。没有证据支持将当前低频归因于 USB 降至 2.0、设备停流或内存耗尽。

### 同一话题、相同时间窗口的 QoS 对照

使用 ROS 原始序列化消息订阅，避免 Python 对点云逐点解析。采样 25 秒：

| 接收方式 | 帧数 | 实收频率 Hz | 最长相邻收帧间隔 s |
| --- | ---: | ---: | ---: |
| `/odin1/cloud_raw` Best Effort | 46 | 1.869 | 2.348 |
| `/odin1/cloud_raw` Reliable | 256 | 10.267 | 0.135 |
| `/navigation/obstacle_points` Best Effort | 62 | 2.555 | 2.045 |
| `/odin1/image/compressed` Best Effort | 36 | 1.603 | 2.536 |
| `/odin1/odometry` Best Effort | 256 | 10.260 | 0.154 |

这里 Hz 按首末收到的消息计算，不等于帧数直接除以 25。原始点云单帧约 934085 字节，压缩图像约 0.77 MB，里程计只有 716 字节。大消息明显更易受影响。

当前驱动发布端是 Reliable，适配器的点云输入在 `src/odin_explorer/explorer_odin/src/odin_nav_adapter.cpp:56` 使用 `SensorDataQoS()`，即 Best Effort。这是合法的 QoS 匹配，但该订阅不能依靠可靠重传恢复缺失数据。此前 `ros2 topic hz` 测到的是订阅接收速率，不能直接当成设备发布速率。

### UDP 丢包与共享内存

- 驱动和适配器均使用 `/opt/ros/humble/lib/libfastrtps.so.2.6.11`，相关 ROS/DDS 环境一致。
- 适配器用户数据 UDP socket 为端口 7411。一次 5 秒采样中，socket 丢包计数从 35735 增至 36145，即增加 410。
- `ss -u -a -n -m -p` 显示实际接收缓冲区 `rb212992`；后续同一 socket 累计丢包已到 72814。
- `net.core.rmem_default` 和 `net.core.rmem_max` 均为 212992。
- 主机 UDP `RcvbufErrors` 与 `InErrors` 在采样时均为 570988。它们是主机累计值，不能全部归因于 ODIN；适配器 socket 的增量才是当前链路的直接证据。
- 驱动只映射自身 FastDDS 共享内存；适配器映射多个其他导航节点共享内存，却没有映射驱动对应段。

### 更深一层：SDK / FastDDS 的 MD5 符号冲突

`vendor_ws/src/odin_ros_driver/CMakeLists.txt:102` 起默认开启回溯符号支持，`CMAKE_ENABLE_EXPORTS ON` 使链接命令带有 `--export-dynamic -rdynamic`。静态 SDK `liblydHostApi_amd.a` 中的全局 `MD5` 类因此进入可执行文件动态符号表。

FastDDS 也包含同名全局 `MD5` 类，两个实现的布局/API 不同。运行时符号解析可把构造函数与 `finalize()` 绑定到 SDK，而 `update(unsigned int)` 仍来自 FastDDS，造成两种实现混用。

FastDDS 通过接口地址计算主机标识，并利用 GUID 中的主机部分判断共享内存是否可用。当前驱动 GUID 主机字节为 `c1.f2`，适配器为 `c7.cd`；基于当前 IPv4 地址按 FastDDS 算法计算的正确值为 `c7.cd`。进程网络命名空间一致，没有找到支持“虚拟网卡变化”的证据。

不启动 ROS、不连接设备的最小离线复现结果：

| 链接方式 | MD5 摘要 | 主机字节 |
| --- | --- | --- |
| 仅 FastDDS | `deda20bc56c56761df39d8cc4eee4b1e` | `c7.cd` |
| 导出 SDK 同名符号 | `d41d8cd98f00b204e9800998ecf8427e` | `5e.2b` |
| 隐藏 SDK 动态导出符号 | `deda20bc56c56761df39d8cc4eee4b1e` | `c7.cd` |

SDK 自己正确配套调用时仍得到正常摘要。离线异常值与当前进程异常值不必相同：复现使用清零的独立存储，而原进程对象布局混用后的内容不同。证据支持符号冲突会破坏 FastDDS 主机标识，不能把某个异常字节值当成稳定标识。

算法依据为 FastDDS 2.6.11 的 [Host 实现](https://raw.githubusercontent.com/eProsima/Fast-DDS/v2.6.11/src/cpp/utils/Host.hpp) 与 [GUID 生成](https://github.com/eProsima/Fast-DDS/blob/v2.6.11/src/cpp/rtps/common/GuidUtils.hpp)，本地 `Guid.h` 的同机判断比较 GUID 前四字节。

另外复制实际驱动的链接参数，仅替换输出路径并添加 `-Wl,--exclude-libs,liblydHostApi_amd.a`，成功生成 `/tmp/odin_md5_diagnosis/host_sdk_sample_hidden`。SDK MD5 动态导出符号从 6 个降至 0，内部实现仍保留；22 个 DT_NEEDED 项完全一致，`ldd` 没有缺失依赖。新驱动没有执行。最终“新驱动 GUID 恢复一致 → 共享内存生效 → Best Effort 帧率恢复”的运行验证仍需要重启驱动，不能用离线链接验证替代。

### 隔离副本验证最小订阅修改

复制当前适配器源码到 `/tmp/odin_reliable_check`，仅将点云输入改为：

```cpp
rclcpp::SensorDataQoS().reliable()
```

独立编译后运行 32 秒，节点名称独立，所有输出 `/odom`、`/tf`、`/tf_static`、障碍点云和清除点云均重映射至 `/odin_diagnostic/*`。原运行节点保持不变。副本已自动退出。

25 秒对照结果：

| 话题 | 帧数 | Hz | 最长收帧间隔 s |
| --- | ---: | ---: | ---: |
| 原始点云 Reliable | 257 | 10.257 | 0.196 |
| 原适配器障碍点云 | 80 | 3.508 | 1.362 |
| 隔离副本障碍点云 | 256 | 10.254 | 0.135 |
| 压缩图像 Reliable | 256 | 10.260 | 0.129 |

这验证了 Reliable 输入能够恢复实际 PCL 处理后的障碍点云输出，不只是让统计工具显示正常。

建议的永久处理：

1. 针对静态 SDK archive 添加链接符号隔离，例如 x86 使用 `-Wl,--exclude-libs,liblydHostApi_amd.a`，ARM 使用对应库名；以最终实际链接文件为准。避免 SDK 污染其他动态库符号。
2. 将导航适配器原始点云输入改成 Reliable，与现有驱动发布端一致，作为已验证的丢帧缓解措施。此项只用于当前已确认 Reliable 的上游。
3. 重启生效后重新确认驱动 GUID 主机部分、共享内存映射及真实点云频率。若未来跨机走 UDP，再单独配置和验证网络接收缓冲区。

隐藏 SDK 动态符号可能减少 SDK 内部 `backtrace_symbols()` 的即时符号名称；DWARF、帧指针及离线 `addr2line` 信息可保留。没有必要为了修复丢帧先改设备帧率或关闭 RGB。

## RGB：控制命令应答超时，数据流正常

当前启动日志：`/home/cangling/.ros/log/host_sdk_sample_11785_1790085219875.log`。

- DTOF 成功时间 `1790085220.353473`，RGB `rc=-1` 时间 `1790085225.353617`，相隔 5.000143 秒。
- 已有日志共找到 44 次同类失败、0 次成功；对应等待时间 5.000143～5.000649 秒。包含完整初始化和恢复流两种路径，因此不是仅恢复启动才出现。
- `rgb_fps: 100` 表示约 10 fps，不是 100 fps。`RGB=100 / DTOF=100` 符合 `include/lidar_api.h:546` 的配对表。
- `src/host_sdk_sample.cpp:1685` 起的调用顺序为设置 DTOF、设置 RGB、再启动流，符合接口要求。
- 当前驱动 0.14.4、SoC 0.14.1、SLAM 0.13.0。仅凭版本数字不足以认定固件不兼容。

对实际 SDK 静态库/驱动二进制检查发现：`lidar_set_rgb_parameter()` 发送子命令 `0x2b` 后等待 `sender::recv_cmd(..., 5000)`；接收失败/超时分支返回 `-1`。因此现在已定位到控制应答接收层。

`include/lidar_api_type.h:489` 的协议错误码将不支持格式、分辨率、帧率、无效组合和未设置 DTOF 区分为 501～505。现有 `-1` 不能解释为已确认的参数组合错误。

RGB TX/RX 和可靠订阅均约 10.26 Hz，说明相机没有停止工作。但是，帧率正常不证明这次配置命令已成功生效：可能沿用旧/default 配置，也可能执行后应答丢失。状态表所有 `configured_odr` 字段为 0，同样不能用来证明 RGB 未配置。

尚未区分：设备没有返回应答，还是 SDK 没有正确接收/识别应答。当前 SDK 相关底层仅提供静态库，现有 ROS 日志不足以闭环这一差别。

后续应在一次受控启动中完整保留 SDK 标准输出，并抓取该 `0x2b` 控制交互及回复，再决定修固件协议还是 SDK 接收逻辑。本次没有为抓取启动交互而中断用户正在运行的设备。不要盲改分辨率、提高帧率，或仅屏蔽告警来声称修复。

## RViz：单次初始化验证告警

本次日志仅一次 `active samplers with a different type refer to the same texture image unit`，发生于首张 214×279 地图创建后；随后继续创建局部 80×80 和全局地图，没有持续出现同类错误。

RViz 官方 [issue #463](https://github.com/ros2/rviz/issues/463) 描述完全相同的首次绘图日志，报告者说明地图仍可显示。本地 Ogre 1.12.1 的上游实现是在链接成功后调用日志检查，而检查内部过早调用 `glValidateProgram()`；两个 sampler 尚未赋予不同纹理单元。见 [链接实现](https://raw.githubusercontent.com/OGRECave/ogre/v1.12.1/RenderSystems/GL/src/GLSL/src/OgreGLSLLinkProgram.cpp) 和 [验证实现](https://raw.githubusercontent.com/OGRECave/ogre/v1.12.1/RenderSystems/GL/src/GLSL/src/OgreGLSLExtSupport.cpp)。

本地材质文件已将两个 sampler 正确配置为单元 0 和 1，渲染包完整性检查正常。当前 RViz 实际使用 Mesa/Intel iris，而非机器上同时安装的 NVIDIA 驱动。

判断：高度符合初始化验证告警，不应据此认定地图渲染失败或关联点云低频。本次没有视觉检查屏幕，若地图实际空白，应另查显示状态、地图数据和 TF。无需仅为这一条日志重装显卡驱动。

## 验证边界

- 已完成实时只读采样、设备日志与源码/二进制检查、临时适配器隔离验证、离线 MD5 冲突复现。
- 临时诊断文件位于 `/tmp/odin_stream_probe.py`、`/tmp/odin_isolated_probe.py`、`/tmp/odin_isolated_probe_result.json`、`/tmp/odin_reliable_check/`、`/tmp/odin_md5_diagnosis/`。
- 本报告不代表已部署修复；正在运行的原适配器仍使用 Best Effort。
- 未发送导航目标或运动命令，未做实车避障和路径跟踪测试。

## 修复落实（同日后续，用户已授权修改代码）

正式修改已完成并安装到本工作区：

- `src/odin_explorer/explorer_odin/src/odin_nav_adapter.cpp`：原始点云输入改为 `SensorDataQoS().reliable()`，输出保持原有 QoS。
- `vendor_ws/src/odin_ros_driver/CMakeLists.txt`：只对实际链接的静态 SDK archive 追加 `--exclude-libs`，按实际库名兼容 x86/ARM，追加在 ARM 链接选项之后，保留现有调试信息。
- `vendor_ws/src/odin_ros_driver/src/host_sdk_sample.cpp`：增加 RGB 配置耗时、错误类别及真实帧率诊断，明确失败时配置未确认。没有跳过命令、增加重试或声称设备超时已根治。
- 厂商修改已保存为主仓库补丁 `vendor_ws/patches/0002-isolate-sdk-symbols.patch` 和 `0003-report-rgb-config-failure.patch`；从固定厂商 HEAD 按 `0001 → 0002 → 0003` 回放成功，结果与修改后的源码一致。部署说明同步更新。

构建与验证：

- `odin_ros_driver` 和 `explorer_odin` 完成编译，分别直接执行 `cmake --build ... --target host_sdk_sample` / `odin_nav_adapter` 返回 0，`cmake --install` 成功。沙箱中 colcon 在子进程构建结束后停在事件循环，因此终止了这两个构建管理进程并使用 CMake 完成安装和确认；未终止导航进程。
- 已安装驱动中 SDK MD5 动态导出符号为 0；加载 ROS 与 vendor 工作区环境后，`ldd` 没有缺失依赖；安装产物包含新 RGB 诊断文本。
- 正式安装的适配器再次以所有输出隔离的方式运行。25 秒采样中，完成发现后障碍物输出 10.258 Hz、最大相邻收帧间隔 0.136 秒；同期原运行适配器约 4.837 Hz、最大间隔 0.787 秒。前者采到 247 帧，开始阶段有发现/TF 外参等待，因此频率按首末收到的消息计算。
- 诊断副本已退出。当前原导航/驱动进程没有重启，新代码在下次启动后生效。完整共享内存恢复及 RGB 实际命令结果仍需届时确认。
