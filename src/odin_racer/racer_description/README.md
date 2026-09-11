# racer_description

English | [Chinese](README_cn.md)

Robot geometry and frame definitions.

## Status

Available: illustrative two-rear-drive/two-front-caster Xacro and non-actuating model preview. Pending: measured geometry, collision/inertial model and actual sensor optical transforms.

## Responsibility and acceptance

Backlog: HW-001, CAL-001. See the root architecture and interface documents.
This package currently installs assets/documentation through ament_cmake.
A successful build is not evidence that a planned subsystem runs.

## Configuration

Any `*.template.yaml` is a specification form, not a live ROS parameter file.
Add runtime dependencies, executables and tested parameters when implementing
the component. Keep vendor code and large recordings outside this package.
