# Primary references

English | [Chinese](REFERENCES_cn.md)

External sources were originally reviewed on 2026-09-10; this cleanup only updates local references and does not claim a new online review. The imported driver revision is in the [vendor record](../vendor_ws/README.md). Other entries are design references; use release-specific documentation when integrating.

| Source | What was used | Applicability |
| --- | --- | --- |
| [ODIN1 product](https://www.manifoldtech.cn/products/odin1/) | Available sensing modalities and advertised pose accuracy | Product capability; validate the actual unit |
| [ODIN1 vendor driver](https://github.com/manifoldsdk/odin_ros_driver) | Humble/Ubuntu 22.04 baseline and firmware matching | Imported revision recorded separately; target validation pending |
| [ODIN1 vendor data documentation](https://github.com/ManifoldTechLtd/wiki/blob/master/docs/odin_series/odin1/5.%20Data%20output_.md) | Device-specific camera model and coordinate conversion concerns | Audit before adapting CameraInfo/TF |
| [Odin-Nav-Stack](https://github.com/ManifoldTechLtd/Odin-Nav-Stack) | Existing ODIN1 navigation integration | ROS 1 / Go2 example; not imported |
| [JetPack 6.2.1 release notes](https://docs.nvidia.com/jetson/jetpack/6.2.1/release-notes/index.html) | Orin support and L4T 36.4.4 baseline reference | Example 6.x release, not a claim of latest version |
| [Current Orin Nano setup](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/quick_start.html) | Check current platform options independently of driver support | Newer JetPack does not imply compatible vendor userspace |
| [Humble diff_drive_controller](https://control.ros.org/humble/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html) | Wheel controller used in simulation and its command/TF contract | Confirmed rear differential drive; measured parameters pending |
| [Nav2 Regulated Pure Pursuit](https://docs.nav2.org/rolling/configuration_and_development/configuration_guide/controller_plugins/configuring_regulated_pp/) | Curvature-based speed regulation concept | Rolling reference; recheck Humble API before implementation |
| [Clearpath robot stack](https://github.com/clearpathrobotics/clearpath_robot) | Separation of hardware, sensors, configuration and tests | Organizational inspiration; no source copied |

Implementation status, hardware gates and internal metrics are specified in their respective project guides.
The supplied course photograph is user evidence, not an official full rulebook.
