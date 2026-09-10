# racer_navigation

Optional Nav2 integration.

## Status

Planned extension: navigation mode, environment representation and controller adapter after race requirements are satisfied. No fake Nav2 parameter file is installed.

## Responsibility and acceptance

Backlog: NAV-001. See the root architecture and interface documents.
This package currently installs assets/documentation through ament_cmake.
A successful build is not evidence that a planned subsystem runs.

## Configuration

Any `*.template.yaml` is a specification form, not a live ROS parameter file.
Add runtime dependencies, executables and tested parameters when implementing
the component. Keep vendor code and large recordings outside this package.
