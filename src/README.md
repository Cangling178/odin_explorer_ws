# First-party ROS 2 packages

English | [Chinese](README_cn.md)

Main functions belong in packages under `src/odin_racer/`. There is no single `main.py` or race launch yet. Packages marked as planned contain documentation and configuration specifications, not algorithm nodes.

| Package | Responsibility | State |
| --- | --- | --- |
| [racer_description](odin_racer/racer_description/README.md) | Robot geometry and frame definitions | Asset preview |
| [racer_hardware](odin_racer/racer_hardware/README.md) | Motor transport, wheel feedback and drive integration | Planned subsystem |
| [racer_odin](odin_racer/racer_odin/README.md) | ODIN1 vendor adaptation and timestamp/frame contracts | Planned subsystem |
| [racer_localization](odin_racer/racer_localization/README.md) | Continuous body state and global alignment | Planned subsystem |
| [racer_perception](odin_racer/racer_perception/README.md) | Local visual line observations and branch candidates | Planned subsystem |
| [racer_trajectory](odin_racer/racer_trajectory/README.md) | Ordered route progress and feasible speed profiles | Planned subsystem |
| [racer_control](odin_racer/racer_control/README.md) | Path tracking, operating state and command gating | Planned subsystem |
| [racer_navigation](odin_racer/racer_navigation/README.md) | Optional Nav2 integration | Planned subsystem |
| [racer_bringup](odin_racer/racer_bringup/README.md) | Launch composition and robot operating profiles | Asset preview |
| [racer_evaluation](odin_racer/racer_evaluation/README.md) | Race recording and metric export integration | Planned subsystem |

All ten are discoverable ament_cmake asset packages. Only the description/bringup
preview has a launch implementation. Use `colcon build --base-paths src` from
the workspace root. Vendor code is isolated under `vendor_ws/`. The maintainer
address is an intentional non-deliverable placeholder until the owner chooses
a project contact; it is not used as the Git commit identity.

## Existing program entry points

| File | Function |
| --- | --- |
| [preview.launch.py](odin_racer/racer_bringup/launch/preview.launch.py) | User launch entry; composes model preview |
| [Model preview implementation](odin_racer/racer_description/launch/preview.launch.py) | Publishes model and stationary joint states |
| [robot.urdf.xacro](odin_racer/racer_description/urdf/robot.urdf.xacro) | Illustrative geometry |
| [evaluate_run.py](../tools/evaluate_run.py) | Offline evaluation of associated error samples |
| [check_workspace.py](../tools/check_workspace.py) | Syntax, documentation links and package checks |

Race state, mode selection and final command arbitration belong in `racer_control`; `racer_navigation` only integrates optional Nav2, and `racer_bringup` composes launches. Perception supplies line observations, `racer_trajectory` maintains ordered route progress and plans speed, and `racer_control` turns references into motion commands. See [Architecture](../docs/02_architecture.md).
