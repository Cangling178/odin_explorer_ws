# Risk register

English | [Chinese](RISKS_cn.md)

Ratings are initial engineering judgments, not measured probabilities.

| ID | Risk | Impact | Trigger / evidence | Mitigation / next decision |
| --- | --- | --- | --- | --- |
| R-01 | Existing chassis cannot fit tight turns | High | Radius or swept footprint violates corridor | Measure before algorithm selection |
| R-02 | ODIN1 ground view insufficient | High | Blind spot, blur or too few line pixels | Mount/projection trial; rule-compatible camera alternative |
| R-03 | Pose drift exceeds line tolerance | High | Independent error larger than internal error | Local visual feedback and calibration budget |
| R-04 | Wrong branch at intersection | High | Progress jumps to geometrically near segment | Ordered route, direction and crossing replay tests |
| R-05 | Wheel slip and caster alignment vary with speed and surface | High | Turn error varies across trials | Effective geometry calibration and bounded speed |
| R-06 | Sensor/compute latency causes overshoot | High | Stale observations or delayed actuation | Timestamp audit, profiling and braking-aware lookahead |
| R-07 | Driver/firmware/platform mismatch | High | Vendor build or USB data failure | Isolated underlay and exact tested revision |
| R-08 | Motor noise causes brownout or disconnect | High | Faults only under load | Measured power budget and wiring revision |
| R-09 | Judged point or corner penalties change acceptance | High | Remaining judging details | Sensing/prior-route allowances confirmed by owner; record remaining limits |
| R-10 | Evaluation rewards missing data or shortcuts | High | Fast run has gaps or wrong checkpoints | Coverage, ordered association and failure reporting |
| R-11 | Overinvestment in general navigation | Medium | Race milestones stall | Prioritize line/crossing/control baseline |

Assign an owner and update status when each risk has concrete evidence. Close a
risk only with a test or resolved rule, not with a proposed mitigation alone.
