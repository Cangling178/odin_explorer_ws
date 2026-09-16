# racer_control

English | [Chinese](README_cn.md)

Low-speed path tracking, explicit enabling and invalid-input stops.

C++17 node `line_controller` is implemented with algorithm logic separate from ROS plumbing.
Runtime parameters are in `config/line_controller.yaml`; `*.template.yaml` remain design specifications.

Implementation, topics, parameters, launch and tests: [visual line following](../../../simulation/LINE_FOLLOWING.md).
Ordered full-course routing and crossing selection are implemented in the simulation lap controller. Hardware calibration and F4 integration remain pending.

Existing `config/simulation_controllers.yaml` retains the ros2_control drive, joint-state broadcaster and underlying command timeout.

## Current implementation — 2026-09-16

`lap_controller` is the current continuous full-map controller: ordered route progress, full-map visual alignment, wheel odometry, explicit enable and latched fault stops. `line_controller` remains the independent local-vision/corner controller. Only one is launched at a time.

Launch, parameters and acceptance: [competition lap](../../../simulation/COMPETITION_LAP.md).
