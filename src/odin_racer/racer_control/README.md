# racer_control

English | [Chinese](README_cn.md)

Low-speed path tracking, explicit enabling and invalid-input stops.

C++17 node `line_controller` is implemented with algorithm logic separate from ROS plumbing.
Runtime parameters are in `config/line_controller.yaml`; `*.template.yaml` remain design specifications.

Implementation, topics, parameters, launch and tests: [visual line following](../../../simulation/LINE_FOLLOWING.md).
Full-course routing, crossing selection, hardware calibration and F4 integration remain pending.

Existing `config/simulation_controllers.yaml` retains the ros2_control drive, joint-state broadcaster and underlying command timeout.
