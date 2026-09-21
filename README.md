# Odin Racer

English | [Chinese](README_cn.md)

ROS 2 line-following robot for Jetson Orin Nano, ODIN1 and an F4 controller, with two rear drive wheels and two passive front supports.

**The C++ perception and ordered-route controller have completed simulation laps. Hardware communication, Jetson deployment, calibration and real-vehicle integration remain unfinished.**
The Gazebo course defaults to 4×3 m with approximately 21.2 mm lines. Recorded results: 0.05 m/s passed 3/3 independent starts; 0.10 m/s passed once. The default remains 0.05 m/s. See [lap evidence](experiments/competition_lap/RESULTS.md) for metrics and scope.

## Start here

| Task | Guide |
| --- | --- |
| Build, check or contribute | [Development](docs/07_development.md) |
| Run a complete simulation lap | [Competition lap](simulation/COMPETITION_LAP.md) |
| Run component or local tracking simulations | [Simulation](simulation/README.md) |
| Understand code and data flow | [Package map](src/README.md), [architecture](docs/02_architecture.md), [interfaces](docs/06_interfaces.md) |
| Connect the real vehicle | [Bringup and calibration](docs/09_bringup.md), [hardware records](hardware/README.md) |
| Check remaining work | [Project plan](docs/planning/README.md), [requirements](docs/01_requirements.md) |
| Find test evidence | [Validation index](experiments/README.md) |

## Workspace

`src/odin_racer/` holds eleven first-party ROS packages; `tools/` and `tests/` hold generation and independent validation tools.
`hardware/`, `tracks/` and `firmware/` hold device facts, course sources and the F4 protocol proposal. `vendor_ws/` isolates the vendor driver.
`data/generated/`, `build/`, `install/` and `log/` are local data/build outputs, excluded from Git.
`*.template.yaml` files are incomplete specification forms, not runnable ROS parameters.

Documentation keeps one technical home per topic with English/Chinese counterparts. Historical evidence retains its original version and date; current status does not imply that old tests were rerun.
[Changes](docs/CHANGELOG.md) · [Sources](docs/REFERENCES.md) · [License](LICENSE)
