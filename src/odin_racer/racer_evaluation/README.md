# racer_evaluation

English | [Chinese](README_cn.md)

Race recording and metric export integration.

## Status

Planned ROS integration: synchronized run events, bag export and ordered route association. A working standalone CSV evaluator lives in tools/.

## Responsibility and acceptance

Backlog: EVAL-001, EVAL-002. See the root architecture and interface documents.
This package currently installs assets/documentation through ament_cmake.
A successful build is not evidence that a planned subsystem runs.

## Configuration

Any `*.template.yaml` is a specification form, not a live ROS parameter file.
Add runtime dependencies, executables and tested parameters when implementing
the component. Keep vendor code and large recordings outside this package.

## Current implementation — 2026-09-16

The ROS package remains a skeleton; executable validation is provided by the Python tools `validate_competition_lap.py`, `validate_lap_controller.py` and `repeat_competition_lap.py`.

Launch, parameters and acceptance: [competition lap](../../../simulation/COMPETITION_LAP.md).
