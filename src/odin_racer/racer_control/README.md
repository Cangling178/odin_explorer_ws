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
