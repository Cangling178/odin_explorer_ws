# Primary references

English | [Chinese](REFERENCES_cn.md)

Reviewed on 2026-09-10. These are design references, not downloaded dependencies.
Use release-specific documentation and pin actual integration revisions later.

| Source | What was used | Applicability |
| --- | --- | --- |
| [ODIN1 product](https://www.manifoldtech.cn/products/odin1/) | Available sensing modalities and advertised pose accuracy | Product capability; validate the actual unit |
| [ODIN1 vendor driver](https://github.com/manifoldsdk/odin_ros_driver) | Humble/Ubuntu 22.04 baseline and firmware matching | Candidate hardware dependency |
| [ODIN1 vendor data documentation](https://github.com/ManifoldTechLtd/wiki/blob/master/docs/odin_series/odin1/5.%20Data%20output_.md) | Device-specific camera model and coordinate conversion concerns | Audit before adapting CameraInfo/TF |
| [Odin-Nav-Stack](https://github.com/ManifoldTechLtd/Odin-Nav-Stack) | Existing ODIN1 navigation integration | ROS 1 / Go2 example; not imported |
| [JetPack 6.2.1 release notes](https://docs.nvidia.com/jetson/jetpack/6.2.1/release-notes/index.html) | Orin support and L4T 36.4.4 baseline reference | Example 6.x release, not a claim of latest version |
| [Current Orin Nano setup](https://docs.nvidia.com/jetson/orin-nano-devkit/user-guide/quick_start.html) | Check current platform options independently of driver support | Newer JetPack does not imply compatible vendor userspace |
| [Humble diff_drive_controller](https://control.ros.org/humble/doc/ros2_controllers/diff_drive_controller/doc/userdoc.html) | Standard wheel controller candidate and command/TF contract | Confirmed rear differential drive; measured parameters pending |
| [Nav2 Regulated Pure Pursuit](https://docs.nav2.org/rolling/configuration_and_development/configuration_guide/controller_plugins/configuring_regulated_pp/) | Curvature-based speed regulation concept | Rolling reference; recheck Humble API before implementation |
| [Clearpath robot stack](https://github.com/clearpathrobotics/clearpath_robot) | Separation of hardware, sensors, configuration and tests | Organizational inspiration; no source copied |

The architecture, milestone gates and internal metrics are project proposals.
The supplied course photograph is user evidence, not an official full rulebook.
