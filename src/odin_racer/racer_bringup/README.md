# racer_bringup

English | [Chinese](README_cn.md)

Launch composition and robot operating profiles.

## Status

Available: model preview wrapper and ros2_control vehicle simulation.launch.py. Onboard simulated sensors are integrated. Pending: hardware sensor, base and race compositions with explicit readiness and arming.

## Responsibility and acceptance

Backlog: RACE-001. See the root architecture and interface documents.
This package currently installs assets/documentation through ament_cmake.
A successful build is not evidence that a planned subsystem runs.

## Configuration

Any `*.template.yaml` is a specification form, not a live ROS parameter file.
Add runtime dependencies, executables and tested parameters when implementing
the component. Keep vendor code and large recordings outside this package.

## Vehicle motion simulation

`ros2 launch racer_bringup simulation.launch.py` starts the physics model and
simulation controllers in /sim/racer. Append gui:=false for headless use.
Controller activation failure terminates the launch; success waits for commands
stamped in simulation time. No real motor interface starts.
See the [simulation guide](../../../simulation/README.md#ros2_control-vehicle-motion-simulation) for commands, settings and validation.

Onboard Odin output is enabled by default; append sensors:=false for base-only tests.
sensor_targets:=true adds known fixtures. The camera requires rendering even with gui:=false;
see [onboard sensors](../../../simulation/README.md#onboard-odin-sensors) for interfaces and validation.

Append `course:=competition` for the [competition drawing scene](../../../simulation/COMPETITION_COURSE.md);
the default `course:=empty` preserves the test floor. `course_overview:=true` adds an inspection camera.
Competition mode rejects sensor_targets.
