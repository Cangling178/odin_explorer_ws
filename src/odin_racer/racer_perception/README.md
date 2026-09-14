# racer_perception

English | [Chinese](README_cn.md)

Local visual black-line detection and metric ground centerlines.

C++17 node `line_perception` is implemented with algorithm logic separate from ROS plumbing.
Runtime parameters are in `config/line_perception.yaml`; `*.template.yaml` remain design specifications.

Implementation, topics, parameters, launch and tests: [visual line following](../../../simulation/LINE_FOLLOWING.md).
Full-course routing, crossing selection, hardware calibration and F4 integration remain pending.
