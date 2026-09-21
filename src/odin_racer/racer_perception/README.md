# racer_perception

English | [Chinese](README_cn.md)

C++17 `line_perception` projects same-frame FishPoly images/CameraInfo onto a flat ground grid using acquisition-time TF. It publishes `LineObservation`, ground masks and debug views. `line_offline` supports image replay; geometry is in `include/racer_perception/line_geometry.hpp`.

Both controllers share this node: local tracking uses path/corner evidence, while lap tracking uses image health and `black_mask` for map alignment. Configuration: `config/line_perception.yaml`. [Algorithm and interfaces](../../../simulation/LINE_FOLLOWING.md) · [Camera convention](../../../simulation/FISHPOLY_CAMERA.md).
Real-image calibration, installation and timing still need [hardware validation](../../../docs/09_bringup.md).
