# Project plan

English | [Chinese](README_cn.md)

2026-09-16 update: [C++ single-branch visual tracking](../../simulation/LINE_FOLLOWING.md) is implemented with explicit enabling and latched fault stops. Continuous full-map tracking is now validated in simulation; hardware acceptance remains pending.

Maintain milestones, tasks, risks and decisions here. Build evidence is in [validation](VALIDATION.md). Technical details remain in the [documentation](../README.md).

Isolated simulation acceptance passed 42/42 tracking and 12/12 fault trials; see [delivered results](../../experiments/isolated_line/RESULTS.md).
The competition map defaults to scale 2 (4 by 3 m) with about 21.2 mm stroke width; selected-route full laps and crossing selection pass in simulation; hardware dependencies remain pending.

## Milestones

Use evidence gates instead of fixed dates before the hardware and rules are known.
Only M0 has passed its acceptance gate; M1-M8 remain incomplete. Mechanical modeling,
the local vendor-driver build and initial point cloud check, and basic motion simulation
have documented progress. These partial results do not establish hardware bench or
autonomous line-following acceptance. SIM-001 remains in progress: onboard sensors and the competition
drawing scene and full-course closure are validated; sensor replay and hardware integration remain. Physical survey and official route order remain unconfirmed.

| Milestone | Deliverable | Exit evidence | Depends on |
| --- | --- | --- | --- |
| M0 Foundation | English workspace, buildable assets, local Git and offline metrics | Build/check report | None |
| M1 Requirements and inventory | Remaining rule answers, F4 model, ratings and dimensions | REQ/Q matrix and completed hardware forms | M0 |
| M2 Motor and sensor bench | Feedback control, watchdog, ODIN1 capture and calibration | Bench logs, measured timing and ground visibility | M1 |
| M3 Low-speed tracking | Simple-line control and valid metric pipeline | Independent error on straight/arcs | M2 |
| M4 Correct full course | Ordered route, correct crossing, feasible bends | Ten repeat attempts with failure log | M3, surveyed course |
| M5 Accuracy baseline | Repeatable accepted error limits | Calibration revision and acceptance report | M4 |
| M6 Speed optimization | Bounded speed profile and fair controller comparison | Reduced valid time at retained accuracy | M5 |
| M7 Competition release | Frozen parameters and reproducible startup | Full rehearsal and tagged evidence | M6 |
| M8 Optional navigation | Nav2/local environment integration | Separate navigation tests | M7 or explicit scope change |

The critical early decision is whether the existing chassis can negotiate this
course within the judged corridor and whether ODIN1's camera sees the line well
enough. Resolve those before advanced planner or GPU work.

## Tasks

States: Todo, In progress, Blocked, Done. P0 blocks basic integration; P1 advances
the race objective; P2 is optional. Assign an owner when work starts. Every item
needs evidence before Done, not just a directory or a successful empty build.

| ID | Priority | Task | State | Acceptance / dependency |
| --- | --- | --- | --- | --- |
| SET-001 | P0 | Establish repository and asset build | Done | See VALIDATION.md |
| RULE-001 | P0 | Record remaining judging rules and crossing order | Todo | Sensing/prior-route allowances confirmed; Q-05 through Q-08 pending |
| HW-001 | P0 | Identify exact F4 board, motors, drivers and encoder scaling | Todo | Inventory plus measured geometry |
| HW-002 | P0 | Define power and motor-stop wiring | Todo | Diagram, ratings and bench check |
| BASE-001 | P0 | Implement measured wheel feedback and transport | Blocked | HW-001; parser and round-trip tests |
| BASE-002 | P0 | Validate command timeout and restart behavior | Blocked | BASE-001; disconnected-host evidence |
| SENS-001 | P0 | Validate ODIN1 driver/firmware on target | Todo | Local build and initial point cloud display recorded in [vendor notes](../../vendor_ws/README.md); Jetson/device firmware pair and raw capture acceptance remain pending |
| SENS-002 | P0 | Test RGB ground visibility and projection | Blocked | SENS-001; straight/crossing/bend dataset |
| CAL-001 | P0 | Calibrate wheels, extrinsics and timestamps | Blocked | HW-001, SENS-001; residual report |
| LOC-001 | P1 | Implement continuous local state and TF authority | Blocked | CAL-001; drift and reset tests |
| TRACK-001 | P0 | Survey course and confirm traversal order | Blocked | RULE-001; ordered metric route |
| VIS-001 | P1 | Extract line candidates with confidence | In progress (simulation; hardware blocked) | SENS-002; recorded lighting cases |
| ROUTE-001 | P1 | Add progress-constrained crossing selection | In progress (simulation; hardware blocked) | TRACK-001, VIS-001; both crossing visits |
| CTRL-001 | P1 | Establish low-speed tracking baseline | In progress (simulation; hardware blocked) | BASE-002, CAL-001; independent line error |
| EVAL-001 | P1 | Implement synchronized independent measurement | Todo | Ground-truth calibration and timing uncertainty |
| EVAL-002 | P1 | Export associated errors and report real trials | Blocked | EVAL-001; no invalid-data masking |
| SPEED-001 | P1 | Add curvature and braking speed limits | In progress (simulation; hardware blocked) | Accurate full-route baseline |
| RACE-001 | P1 | Implement mode/state manager and race launch | In progress (simulation; hardware blocked) | Healthy-device and route gates enforced |
| SIM-001 | P2 | Add drive-model simulation and sensor replay | In progress | Basic motion and onboard image/cloud/IMU validated; [competition drawing scene](../../simulation/COMPETITION_COURSE.md) passes initial-straight projection and short motion; unknown masses deferred, single-branch C++ closure implemented; full-route closure passes; sensor replay pending |
| NAV-001 | P2 | Evaluate optional Nav2 mode | Todo | Separate scope; shared command gate |

For each started item add: owner, branch, requirement IDs, design note, validation
command/procedure, evidence path and known limitations. Move completed evidence
into a dated milestone report when the table becomes difficult to scan.

Simulation prototypes for VIS-001/CTRL-001 can now start: detect the line in onboard images,
project ground points using CameraInfo/TF, then close straight/simple-curve tracking at about
0.05 m/s with stops on low confidence or image timeout. The C++ single-branch algorithms are implemented;
hardware acceptance dependencies in the table remain. IMU attitude compensation can follow,
and clouds are not required for the planar-line prototype. Truth is only for independent evaluation.
Physical-course laps still depend on TRACK-001/ROUTE-001. The user-approved simulation route now passes ordered crossing and continuous-lap checks.

## Risks

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

## Decisions

| Date | Decision | Status | Evidence / follow-up |
| --- | --- | --- | --- |
| 2026-09-10 | Race-course accuracy and speed are the primary goal | Confirmed by owner | REQ-004 and REQ-005 |
| 2026-09-10 | Use English throughout authored repository content | Confirmed by owner | REQ-006 |
| 2026-09-10 | Use one first-party workspace with vendor underlay | Accepted foundation choice | ADR-0003 |
| 2026-09-10 | Propose Humble-compatible target | Provisional | ADR-0001; target inventory pending |
| 2026-09-10 | Select local visual feedback plus ordered route context | Selected design | ADR-0002; physical visibility pending |
| 2026-09-10 | Two rear drive motors and two front passive casters | Confirmed by owner | Differential-drive model; motor/encoder details pending |
| 2026-09-10 | F4 lower-level controller and Jetson host | Confirmed by owner | Exact chip, board and firmware pending |
| 2026-09-10 | Prior mapping, preloaded routes and camera recognition allowed | Confirmed by owner | Use hybrid route/visual strategy |
| 2026-09-10 | Keep physical dimensions, route order and limits unfilled | Accepted foundation choice | Requires measurement |
| 2026-09-11 | Preserve English documents and add sibling `_cn.md` Chinese translations | Requested by owner | Bidirectional language links; code and configuration identifiers remain English |
| 2026-09-21 | Allow Chinese in code and configuration comments | Confirmed by owner | Identifiers, user-facing strings and commit messages remain English; repository checker enforces comment-only use |

Motor/encoder details, exact F4 board, driver/transport, start/direction and
precise judging limits remain unresolved. Do not infer approval from elapsed time.

## C++ tracking development — 2026-09-14

Owner: this Codex implementation; implementation in the current workspace. The user selected C++ runtime nodes.
VIS-001/CTRL-001 now have a flat-ground single-branch prototype; [tests and limits](../../simulation/LINE_FOLLOWING.md).
This does not close hardware M2/M3 dependencies or TRACK-001/ROUTE-001. Crossing, disturbance and replay matrices follow.

## Continuous-lap simulation progress — 2026-09-16

The approved prerecorded-route, visual alignment and wheel-odometry approach completed one C++ continuous selected-map lap: 185/185 gates, 367.29 s, no mid-lap stop. See [results](../../experiments/competition_lap/RESULTS.md). This advances SIM-001 and the simulation portions of VIS-001/CTRL-001; hardware milestones and official route, calibration and rule dependencies remain open.

## Current lap validation summary — 2026-09-16

Three independent nominal starts passed at 0.05 m/s in 367.26–367.36 s. One 0.10 m/s trial passed in 197.43 s with 5.60/24.14 mm RMS/maximum error. Every run passed 185/185 ordered gates without a mid-lap stop. Repeatability at 0.10 m/s is untested; the default remains 0.05 m/s. Hardware milestone dependencies M2–M8 remain open.

[Results](../../experiments/competition_lap/RESULTS.md).
