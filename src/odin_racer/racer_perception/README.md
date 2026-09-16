# racer_perception

English | [Chinese](README_cn.md)

Local visual black-line detection and metric ground centerlines.

C++17 node `line_perception` is implemented with algorithm logic separate from ROS plumbing.
Runtime parameters are in `config/line_perception.yaml`; `*.template.yaml` remain design specifications.

Implementation, topics, parameters, launch and tests: [visual line following](../../../simulation/LINE_FOLLOWING.md).
Ordered full-course routing and crossing selection are implemented in the simulation lap controller. Hardware calibration and F4 integration remain pending.

## Current implementation — 2026-09-16

The same C++ perception node supplies both controllers. The lap controller uses the ground black mask for map alignment and LineObservation for image health.

Launch, parameters and acceptance: [competition lap](../../../simulation/COMPETITION_LAP.md).
