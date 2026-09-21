# Source map

English | [Chinese](README_cn.md)

Eleven first-party ROS 2 packages live under `src/odin_racer/`. Build from the workspace root with `colcon build --base-paths src`; vendor code is isolated in `vendor_ws/`.

| Package | Current implementation |
| --- | --- |
| [racer_interfaces](odin_racer/racer_interfaces/README.md) | Atomic `LineObservation` message |
| [racer_description](odin_racer/racer_description/README.md) | Robot assets, physics/sensor/course generators and FishPoly plugin |
| [racer_perception](odin_racer/racer_perception/README.md) | C++ ground projection, black-line observations and offline image processing |
| [racer_control](odin_racer/racer_control/README.md) | Local tracking and ordered full-lap controllers, enable/stop logic, simulation drive settings |
| [racer_bringup](odin_racer/racer_bringup/README.md) | Preview, base simulation, local tracking and lap launches |
| [racer_hardware](odin_racer/racer_hardware/README.md) | Specification only; no F4 transport or real wheel feedback |
| [racer_odin](odin_racer/racer_odin/README.md) | Specification only; no real-device adapter |
| [racer_localization](odin_racer/racer_localization/README.md) | Specification only; current map alignment is inside lap control |
| [racer_trajectory](odin_racer/racer_trajectory/README.md) | Specification only; current route progress/curvature limiting is inside lap control |
| [racer_evaluation](odin_racer/racer_evaluation/README.md) | Specification only; runnable independent evaluators live in `tools/` |
| [racer_navigation](odin_racer/racer_navigation/README.md) | Optional future navigation |

Run [full laps](../simulation/COMPETITION_LAP.md) or [local tracking](../simulation/LINE_FOLLOWING.md). These are simulation entry points, not real-vehicle deployment.
[Architecture](../docs/02_architecture.md) records implemented data flow and future ownership; [development](../docs/07_development.md) defines configuration and testing conventions. Package READMEs remain because CMake installs them; status and commands are linked rather than duplicated.
