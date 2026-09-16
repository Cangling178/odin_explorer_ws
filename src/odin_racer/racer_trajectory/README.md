# racer_trajectory

English | [Chinese](README_cn.md)

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

## Current implementation — 2026-09-16

The standalone planner is planned. Ordered progress and curvature-based speed limiting currently live inside `lap_controller` and `lap_route.hpp`; predictive braking remains future work.

Launch, parameters and acceptance: [competition lap](../../../simulation/COMPETITION_LAP.md).
