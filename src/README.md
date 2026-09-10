# First-party ROS 2 packages

| Package | Responsibility | State |
| --- | --- | --- |
| `racer_description` | Robot geometry and frame definitions | Asset preview |
| `racer_hardware` | Motor transport, wheel feedback and drive integration | Planned subsystem |
| `racer_odin` | ODIN1 vendor adaptation and timestamp/frame contracts | Planned subsystem |
| `racer_localization` | Continuous body state and global alignment | Planned subsystem |
| `racer_perception` | Local visual line observations and branch candidates | Planned subsystem |
| `racer_trajectory` | Ordered route progress and feasible speed profiles | Planned subsystem |
| `racer_control` | Path tracking, operating state and command gating | Planned subsystem |
| `racer_navigation` | Optional Nav2 integration | Planned subsystem |
| `racer_bringup` | Launch composition and robot operating profiles | Asset preview |
| `racer_evaluation` | Race recording and metric export integration | Planned subsystem |

All ten are discoverable ament_cmake asset packages. Only the description/bringup
preview has a launch implementation. Use `colcon build --base-paths src` from
the workspace root. Vendor code is isolated under `vendor_ws/`. The maintainer
address is an intentional non-deliverable placeholder until the owner chooses
a project contact; it is not used as the Git commit identity.
