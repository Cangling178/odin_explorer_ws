# racer_hardware

English | [Chinese](README_cn.md)

Motor transport, wheel feedback and drive integration.

## Status

Planned: Jetson-to-F4 transport, two rear encoder conversions, differential controller binding, command-age enforcement and diagnostics. No executable or motor connection exists.

## Responsibility and acceptance

Backlog: BASE-001, BASE-002. See the root architecture and interface documents.
This package currently installs assets/documentation through ament_cmake.
A successful build is not evidence that a planned subsystem runs.

## Configuration

Any `*.template.yaml` is a specification form, not a live ROS parameter file.
Add runtime dependencies, executables and tested parameters when implementing
the component. Keep vendor code and large recordings outside this package.
