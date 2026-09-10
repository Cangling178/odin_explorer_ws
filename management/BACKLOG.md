# Local backlog

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
| SENS-001 | P0 | Validate ODIN1 driver/firmware on target | Todo | Build revision and raw capture |
| SENS-002 | P0 | Test RGB ground visibility and projection | Blocked | SENS-001; straight/crossing/bend dataset |
| CAL-001 | P0 | Calibrate wheels, extrinsics and timestamps | Blocked | HW-001, SENS-001; residual report |
| LOC-001 | P1 | Implement continuous local state and TF authority | Blocked | CAL-001; drift and reset tests |
| TRACK-001 | P0 | Survey course and confirm traversal order | Blocked | RULE-001; ordered metric route |
| VIS-001 | P1 | Extract line candidates with confidence | Blocked | SENS-002; recorded lighting cases |
| ROUTE-001 | P1 | Add progress-constrained crossing selection | Blocked | TRACK-001, VIS-001; both crossing visits |
| CTRL-001 | P1 | Establish low-speed tracking baseline | Blocked | BASE-002, CAL-001; independent line error |
| EVAL-001 | P1 | Implement synchronized independent measurement | Todo | Ground-truth calibration and timing uncertainty |
| EVAL-002 | P1 | Export associated errors and report real trials | Blocked | EVAL-001; no invalid-data masking |
| SPEED-001 | P1 | Add curvature and braking speed limits | Blocked | Accurate full-route baseline |
| RACE-001 | P1 | Implement mode/state manager and race launch | Blocked | Healthy-device and route gates enforced |
| SIM-001 | P2 | Add drive-model simulation and sensor replay | Blocked | HW-001 and selected simulator |
| NAV-001 | P2 | Evaluate optional Nav2 mode | Todo | Separate scope; shared command gate |

For each started item add: owner, branch, requirement IDs, design note, validation
command/procedure, evidence path and known limitations. Move completed evidence
into a dated milestone report when the table becomes difficult to scan.
