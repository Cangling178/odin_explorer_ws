# racer_control

English | [Chinese](README_cn.md)

C++17 tracking, explicit enable and latched fault stops. Select one controller per drive output:

- `lap_controller`: ordered CSV route, whole-map visual alignment and wheel odometry; [full-lap operation](../../../simulation/COMPETITION_LAP.md).
- `line_controller`: observed local paths and bounded corner stop/turn/reacquire; [local tracking](../../../simulation/LINE_FOLLOWING.md).

`config/line_controller.yaml` configures local tracking; lap parameters are supplied by its launch and node defaults. `config/simulation_controllers.yaml` configures the simulated differential drive and wheel-state broadcaster. Route geometry is in `config/competition_lap.csv`, with source metadata alongside it. `test/` covers tracking geometry and ordered route behavior.
Hardware command arbitration, F4 integration and real calibration remain pending; `control_contract.template.yaml` is only a specification.
