# First-party ROS 2 packages

English | [Chinese](README_cn.md)

The full-map continuous entry is [competition_lap.launch.py](odin_racer/racer_bringup/launch/competition_lap.launch.py), with C++ `lap_controller` and onboard visual alignment. See [lap guide](../simulation/COMPETITION_LAP.md).

C++ runtime entry: [line_following.launch.py](odin_racer/racer_bringup/launch/line_following.launch.py); [implementation and tests](../simulation/LINE_FOLLOWING.md).
Main functions belong in packages under `src/odin_racer/`. The complete-map simulation entry point is `competition_lap.launch.py`; there is no hardware race launch yet. Packages marked as planned contain documentation and configuration specifications, not algorithm nodes.

| Package | Responsibility | State |
| --- | --- | --- |
| [racer_interfaces](odin_racer/racer_interfaces/README.md) | Atomic image-health, centerline and corner/exit messages | LineObservation v0.1.0 |
| [racer_description](odin_racer/racer_description/README.md) | Robot geometry and frame definitions | Preview, physics model, onboard sensors and simulation generation |
| [racer_hardware](odin_racer/racer_hardware/README.md) | Motor transport, wheel feedback and drive integration | Planned subsystem |
| [racer_odin](odin_racer/racer_odin/README.md) | ODIN1 vendor adaptation and timestamp/frame contracts | Planned subsystem |
| [racer_localization](odin_racer/racer_localization/README.md) | Continuous body state and global alignment | Planned subsystem |
| [racer_perception](odin_racer/racer_perception/README.md) | Local visual line observations and branch candidates | C++ black-line detection, FishPoly ground projection and invalid observations |
| [racer_trajectory](odin_racer/racer_trajectory/README.md) | Ordered route progress and feasible speed profiles | Planned subsystem |
| [racer_control](odin_racer/racer_control/README.md) | Path tracking, operating state and command gating | C++ adaptive Pure Pursuit, bounded single-corner states and latched fault stops; continuous lap states implemented; hardware race integration pending |
| [racer_navigation](odin_racer/racer_navigation/README.md) | Optional Nav2 integration | Planned subsystem |
| [racer_bringup](odin_racer/racer_bringup/README.md) | Launch composition and robot operating profiles | Preview and vehicle motion simulation |
| [racer_evaluation](odin_racer/racer_evaluation/README.md) | Race recording and metric export integration | Planned subsystem |

All eleven are discoverable ament_cmake packages; racer_interfaces generates ROS messages. Description/bringup provide
preview, standalone sensors, contact and vehicle-motion launch implementations. Use `colcon build --base-paths src` from
the workspace root. Vendor code is isolated under `vendor_ws/`. The maintainer
address is an intentional non-deliverable placeholder until the owner chooses
a project contact; it is not used as the Git commit identity.

## Existing program entry points

| File | Function |
| --- | --- |
| [simulation.launch.py](odin_racer/racer_bringup/launch/simulation.launch.py) | ros2_control vehicle motion simulation |
| [course_world.py](odin_racer/racer_description/racer_description/course_world.py) | Competition drawing scene and optional overhead camera, selected with course:=competition |
| [validate_competition_course.py](../tools/validate_competition_course.py) | Course image projection, sensors and short-motion validation |
| [preview.launch.py](odin_racer/racer_bringup/launch/preview.launch.py) | User launch entry; composes model preview |
| [Model preview implementation](odin_racer/racer_description/launch/preview.launch.py) | Publishes model and stationary joint states |
| [robot.urdf.xacro](odin_racer/racer_description/urdf/robot.urdf.xacro) | CAD and simplified assemblies, approximate inertias, collisions and optional simulation control interfaces |
| [evaluate_run.py](../tools/evaluate_run.py) | Offline evaluation of associated error samples |
| [check_workspace.py](../tools/check_workspace.py) | Syntax, documentation links and package checks |

Race state, mode selection and final command arbitration belong in `racer_control`; `racer_navigation` only integrates optional Nav2, and `racer_bringup` composes launches. Perception supplies line observations, `racer_trajectory` maintains ordered route progress and plans speed, and `racer_control` turns references into motion commands. See [Architecture](../docs/02_architecture.md).
