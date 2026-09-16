# racer_localization

English | [Chinese](README_cn.md)

Continuous body state and global alignment.

## Status

Planned: selected wheel/ODIN1 inputs, covariance policy, single TF authority and reset handling. No EKF configuration is presented as validated.

## Responsibility and acceptance

Backlog: LOC-001, CAL-001. See the root architecture and interface documents.
This package currently installs assets/documentation through ament_cmake.
A successful build is not evidence that a planned subsystem runs.

## Configuration

Any `*.template.yaml` is a specification form, not a live ROS parameter file.
Add runtime dependencies, executables and tested parameters when implementing
the component. Keep vendor code and large recordings outside this package.

## Current implementation — 2026-09-16

The standalone estimator is planned. Current simulation map alignment lives inside `lap_controller`; wheel odometry comes from the simulated diff-drive controller.

Launch, parameters and acceptance: [competition lap](../../../simulation/COMPETITION_LAP.md).
