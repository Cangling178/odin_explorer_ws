# racer_odin

English | [Chinese](README_cn.md)

ODIN1 vendor adaptation and timestamp/frame contracts.

## Status

Planned: audited topic mapping, frame/model conversion, time handling and sensor health. Vendor SDK remains in a separate underlay.

## Responsibility and acceptance

Backlog: SENS-001, SENS-002. See the root architecture and interface documents.
This package currently installs assets/documentation through ament_cmake.
A successful build is not evidence that a planned subsystem runs.

## Configuration

Any `*.template.yaml` is a specification form, not a live ROS parameter file.
Add runtime dependencies, executables and tested parameters when implementing
the component. Keep vendor code and large recordings outside this package.
