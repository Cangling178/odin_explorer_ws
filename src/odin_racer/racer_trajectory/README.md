# racer_trajectory

Ordered route progress and feasible speed profiles.

## Status

Planned: segment topology, crossing association, curvature and acceleration/braking limits. Course coordinates remain unmeasured.

## Responsibility and acceptance

Backlog: TRACK-001, ROUTE-001, SPEED-001. See the root architecture and interface documents.
This package currently installs assets/documentation through ament_cmake.
A successful build is not evidence that a planned subsystem runs.

## Configuration

Any `*.template.yaml` is a specification form, not a live ROS parameter file.
Add runtime dependencies, executables and tested parameters when implementing
the component. Keep vendor code and large recordings outside this package.
