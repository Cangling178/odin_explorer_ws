# racer_control

English | [Chinese](README_cn.md)

Path tracking, operating state and command gating.

## Status

Planned: low-speed baseline, error feedback, bounded commands and mode arbitration. No autonomous velocity publisher exists.

## Responsibility and acceptance

Backlog: CTRL-001, RACE-001. See the root architecture and interface documents.
This package currently installs assets/documentation through ament_cmake.
A successful build is not evidence that a planned subsystem runs.

## Configuration

Any `*.template.yaml` is a specification form, not a live ROS parameter file.
Add runtime dependencies, executables and tested parameters when implementing
the component. Keep vendor code and large recordings outside this package.

## Simulated differential drive

config/simulation_controllers.yaml supplies a 100 Hz ros2_control manager,
joint-state broadcaster, differential-drive controller and 0.25 s command timeout.
Wheel geometry is injected from the model at launch; the effective separation
correction is simulation-only. This is working simulation base-velocity control;
path tracking, race state and hardware communication remain unimplemented.
See the [simulation guide](../../../simulation/README.md#ros2_control-vehicle-motion-simulation) for launch and validation.
