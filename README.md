# Odin Explorer

English | [简体中文](README_cn.md)

ROS 2 laboratory exploration and mapping with Jetson Orin Nano, ODIN1 and an F4 differential-drive base.

**An independently cloned, reduced development foundation, not a completed autonomous robot.** Six packages build and model preview runs. Vendor sources are separate. F4 transport, continuous odometry, navigation grids, Nav2 and exploration goal selection remain unimplemented and unvalidated on hardware.

GitHub: <https://github.com/Cangling178/odin_explorer_ws> (public repository).

Milestones: manually moved mapping → teleoperated base and stopping → goal navigation while mapping → autonomous exploration → waypoint patrol.

## Project structure

```text
odin_explorer_ws/
├── src/odin_explorer/
│   ├── explorer_description/   # Model and RViz preview
│   ├── explorer_bringup/       # Launch composition
│   ├── explorer_hardware/      # Host-side base interface
│   ├── explorer_odin/          # ODIN data adaptation
│   ├── explorer_localization/  # Odometry and mapping integration
│   └── explorer_navigation/    # Navigation, exploration and patrol
├── vendor_ws/src/odin_ros_driver/  # Separate vendor sources and SDK
├── third_party/Odin-Nav-Stack/ # Official ROS1 navigation stack submodule
├── firmware/                   # MCU firmware; protocol notes only
├── hardware/                   # CAD, calibration, BOM and specifications
├── docs/                       # Architecture, interfaces and bringup
│   └── planning/               # Milestones and assignments
├── tools/check_workspace.py    # Minimal structure/model check
├── .github/workflows/          # Automated build and checks
└── build/ · install/ · log/     # Local build outputs, ignored by Git
```

```bash
cd /home/cangling/odin_explorer_ws
source /opt/ros/humble/setup.bash
colcon build --base-paths src --symlink-install
source install/local_setup.bash
python3 tools/check_workspace.py
ros2 launch explorer_bringup preview.launch.py
```

Preview connects to no actuators or sensor devices. See [development](docs/07_development.md) for dependencies.

[Packages](src/README.md) · [Architecture](docs/02_architecture.md) · [Interfaces](docs/06_interfaces.md) · [Assignments](docs/planning/TEAM_ASSIGNMENTS.md) · [Bringup](docs/09_bringup.md) · [Hardware](hardware/README.md) · [Firmware](firmware/README.md) · [Vendor](vendor_ws/README.md) · [Migration](docs/MIGRATION.md).

No tracks, world generators, Gazebo plugins, line following or lap tests. One structural/model check and a third-party setup script remain. Add transport and stopping tests when those functions are implemented. Null values require measurements; `*.template.yaml` files are not runtime parameters.

The official stack is integrated as an isolated submodule. See [navigation stack integration](third_party/README.md) for setup and ROS1/ROS2 differences. Run `bash tools/setup_odin_nav_stack.sh` to restore dependencies and the driver patch. F4 adaptation remains pending.
