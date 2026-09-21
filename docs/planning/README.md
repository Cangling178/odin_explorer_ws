# Remaining work

English | [Chinese](README_cn.md)

See [work assignments for the first three development roles](TEAM_ASSIGNMENTS.md) for prerequisites, interfaces, acceptance criteria, and integration handoffs.

Reviewed 2026-09-21. C++ local tracking and image-map-assisted full laps work in simulation. Real-vehicle M1–M8 acceptance is not complete; M0 is the completed foundation milestone. Recorded results live only in the [validation index](../../experiments/README.md).

## Priority and acceptance

| Priority / IDs | Next work | Acceptance / dependency |
| --- | --- | --- |
| P0 RULE-001, TRACK-001 | Confirm rules, survey dimensions and prescribed crossing order | Q-05–Q-08 in [requirements](../01_requirements.md); ordered measured route |
| P0 HW-001, HW-002 | Confirm F4 board, motor ratings/counting and power/stop wiring | Completed [hardware forms](../../hardware/README.md), verified pinout and ratings |
| P0 BASE-001, BASE-002 | Implement F4 transport, measured wheel feedback and watchdog | Hardware confirmation; round-trip, disconnect and reset tests |
| P0 SENS-001, SENS-002 | Verify Jetson/vendor combination and raw line images | Driver/firmware lock, ground visibility, matching CameraInfo and TF |
| P0 CAL-001 | Calibrate wheel scale, installation and timing | Measured residuals and versioned data |
| P1 LOC-001, VIS-001, CTRL-001 | Integrate local state and low-speed hardware tracking | Hardware/ODIN adapters; straight/arc error and fault-stop evidence |
| P1 ROUTE-001, RACE-001 | Verify crossings, body clearance and explicit race start | Surveyed route; full laps and final command ownership |
| P1 EVAL-001, EVAL-002 | Add independent real-vehicle measurement and recording | Synchronized external reference, coverage and failed-run reporting |
| P1 SPEED-001 | Repeated 0.10 m/s simulation trials and disturbance matrix; later predictive braking | Fixed versions and limits; hardware speed work follows accurate full laps |
| P2 SIM-001 | Sensor replay and measured model-error calibration | Real recordings; preserve truth/control separation |
| P2 NAV-001 | Optional navigation | Separate scope after race baseline |

Simulation already supplies parts of VIS-001, CTRL-001, ROUTE-001, SPEED-001 and RACE-001; their hardware acceptance remains open. SET-001 (foundation) is complete. New tasks should record owner, branch, requirement ID, acceptance command and evidence path; unassigned tasks above remain unassigned.

## Hardware gates

M1: requirements and inventory → M2: wheel/sensor bench → M3: simple low-speed tracking → M4: correct full route → M5: repeatable accuracy → M6: faster valid laps → M7: frozen race build. M8 is optional navigation. Use [bringup](../09_bringup.md) for procedures and [requirements](../01_requirements.md) for proposed repeated-run/error gates. A simulation result does not close these hardware gates.

## Current risks

The unresolved drivers are camera ground view/installation, tight-turn swept clearance, wheel slip/passive-support behavior, sensor and actuator delay, power/USB stability and unknown scoring rules. Wrong-branch or missing-data results must not appear as faster valid laps. Model omissions are in [simulation model](../../simulation/MODEL.md).

Immediate hardware goal: wheel-speed feedback + real ODIN image projection + a short straight-line loop. Until hardware data is available, strengthen the existing lap validation with controlled initial-pose and sensor/odometry perturbations; 0.10 m/s currently has only one recorded pass. The repeat runner does not yet expose speed/lookahead options.
