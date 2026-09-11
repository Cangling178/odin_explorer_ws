# racer_perception

English | [Chinese](README_cn.md)

Local visual line observations and branch candidates.

## Status

Planned: ground projection, line candidates, confidence and invalid-data semantics. No trained model or detector is included.

## Responsibility and acceptance

Backlog: VIS-001. See the root architecture and interface documents.
This package currently installs assets/documentation through ament_cmake.
A successful build is not evidence that a planned subsystem runs.

## Configuration

Any `*.template.yaml` is a specification form, not a live ROS parameter file.
Add runtime dependencies, executables and tested parameters when implementing
the component. Keep vendor code and large recordings outside this package.
