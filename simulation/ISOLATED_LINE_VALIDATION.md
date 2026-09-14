# Isolated-scene validation and reproduction

English | [Chinese](ISOLATED_LINE_VALIDATION_cn.md)

Final frozen acceptance: **42/42 tracking trials and 12/12 fault trials passed**.
See [delivered results and representative figures](../experiments/isolated_line/RESULTS.md)
for per-scene worst errors, sweep bounds and fault-stop delays.

See [runtime design and interfaces](LINE_FOLLOWING.md). This is an engineering
simulation test, not competition or hardware certification. Reference geometry,
end regions and Gazebo truth enter only the evaluator. Runtime uses onboard
images, CameraInfo, TF and wheel odometry.

## Frozen acceptance conditions

[acceptance.json](../experiments/isolated_line/acceptance.json) records error,
speed, corridor and initial-condition thresholds before algorithm changes. The
formal matrix freezes source, parameters and evaluator SHA-256 and aborts if they
change. Results from different versions cannot be combined as one acceptance run.

| Check | Engineering condition |
| --- | --- |
| Completion | 60 mm end region, heading error <0.25 rad, all sequential reference gates visited, no fault stop |
| Full error | Time-weighted RMS <60 mm, P95 <100 mm, maximum <140 mm; initial/tracking/corner phases also reported |
| Straight/arc regression | Last 30% time-weighted RMS <15 mm |
| Corridor | 230 mm each side of the reference polyline, including filled chassis envelope and temporal sampling cover |
| Commands | v<=0.05 m/s, absolute yaw<=0.5 rad/s; acceleration<=0.15 m/s² and 0.8 rad/s² |
| Freshness | Original successfully transformed acquisition age<=0.35 s; odometry deadline 0.15 s |
| Faults | Zero request <0.6 s; after 1.2 s physical speed<0.005 m/s and yaw<0.02 rad/s; still latched after 1 s recovery |
| Repetition | Center twice; +/-35 mm lateral offset; +/-0.08 rad heading offset |

Measured physical velocities are additionally reported with a stated 10% contact
dynamics tolerance. Fault and explicitly requested zero commands are identified
separately from normal acceleration shaping; deliberate corner stops remain shaped.

Nearest-reference arc coordinates are discontinuous near the bisector of a sharp
L. A 2 mm continuous body movement can switch projections 160 mm apart. Reports
retain the largest raw projection-coordinate jump, while route order is checked
using sequential gates every 100 mm along the reference. Gate radius is the fixed
140 mm maximum error. The frozen 50 mm instantaneous jump limit applies to actual
successive body positions. Tests cover both legitimate corner projection switches
and real skipped path segments; endpoint position alone cannot establish passing.

## Fixture geometry

All fixtures use a 21 mm black line and the existing contact model. Print extends
beyond the end region so completion does not depend on losing the line. The print
is visual-only. Identical strip top faces are batched into one rendering mesh for
repeat-test performance, without changing reference geometry or corridor width.

| Scene | Geometry and end |
| --- | --- |
| `line_straight` | y=0, end (1.2,0) m |
| `line_left`, `line_right` | radius 0.8 m around (0,+/-0.8), end at signed angle +/-1.5 rad |
| `line_arc` | original 0.8 m left-arc regression, end at 2.5 rad |
| `line_s` | x=0..2 m, y=0.14[1-cos(pi*x)] m; end (2,0) m |
| `line_corner_left`, `line_corner_right` | y=0 to x=0.8 m, one signed 90-degree turn; end (0.8,+/-0.7) m |

`course_world.line_fixture` defines dimensions, spawn and end explicitly. Reports
include all parameters and the reference polyline. Development defaults to
(0,-0.035,-0.08); formal matrices use the five initial-condition classes above.

## Independent evaluation and swept envelope

`isolated_line_metrics.py` is never imported by runtime algorithms. It evaluates
Gazebo `LinkStates` body truth against reference segments and sequential route
gates. Errors use actual sampling-interval weights. Phase statistics do not bridge
time spent in other phases. Reports retain all samples, commands, states, ages,
parking positions, termination reasons, and source/binary digests.

The chassis envelope is derived from every existing URDF collision, including
wheels, plate, pillars and sensors. The evaluator fills the conservative overall
XY rectangle on a 10 mm grid and adds spatial covering radius and between-sample
translation/rotation cover. This fills actual chassis voids and is an upper bound.
Exceeding it fails this engineering test; it does not prove that every possible
strategy is geometrically impossible. Development's 18 mm parking setback exceeded
the corridor and is retained as a failure. The final strategy parks approximately
80 mm before the corner without changing the reference or 230 mm corridor.
Official corridor dimensions remain unspecified.

## Reproduction

Build and source ROS/workspace first, with a working DISPLAY and unused ports.
These commands actively drive isolated simulation and do not connect hardware:

```bash
python3 -m unittest discover -s tests -v
colcon test --base-paths src --packages-select racer_perception racer_control
colcon test-result --verbose
python3 tools/validate_line_controller.py
python3 tools/validate_arming_clock.py

python3 tools/validate_isolated_line.py --course line_corner_left \
  --output data/generated/my_corner_run

# Stationary camera inspection; never arms.
python3 tools/validate_isolated_line.py --course line_corner_left --static \
  --spawn-x .35 --spawn-y 0 --spawn-yaw 0 --output data/generated/my_static_run
ros2 run racer_perception line_offline \
  data/generated/my_static_run/0001_static_gray.png data/generated/my_static_run/offline

# Seven scenes x (two centered runs + four offset classes) = 42 runs.
python3 tools/run_isolated_matrix.py --output data/generated/my_fixed_matrix

# Three phases x four independent fault scenarios.
python3 tools/run_isolated_matrix.py --faults --output data/generated/my_fault_matrix

python3 tools/report_isolated_line.py data/generated/my_fixed_matrix
```

Existing output directories are rejected to preserve every attempt. `--domain`
and `--port` isolate suites. The fault matrix injects dropped images, uniform
images, missing TF and missing odometry in `RUNNING`, `APPROACH` and `TURN` of a
fresh left-corner scene. Failure to reach a requested phase is recorded as failed
coverage, never counted as a successful fault stop. The synthetic ROS controller
validator separately checks duplicate/reordered timestamps, delayed TF, invalid
paths, NaN, wrong frames, malformed odometry, restart latching and explicit stop.

Each run saves original and relayed images, metric grayscale, mask, centerline,
corner/exit overlays and acquisition-stamped paths. Images are recorded every
simulation second and at state changes, with extra fault/end captures. Commands
are recorded per received message and body truth at approximately 20 Hz. The
report renderer adds targets, state, age and commands to debugging images and
exports standalone trajectory/error/envelope plots, HTML and JSON indexes.

## Evidence directories

Local `data/generated/isolated/` retains original baselines, stationary/offline
images, every development attempt and formal suites. `baseline/source` is the
original algorithm snapshot; `baseline/binaries.sha256` identifies original
executables. The seven baseline scenes and `development_v*` attempts remain
separate from formal success rates. Formal results are under `validated/final_curves`, `validated/final_turns` and
`validated/final_faults`, with their manifests, individual reports and
`validated/final_summary.json`. Large raw artifacts are
ignored by Git under repository policy; standards, reproduction code, tests and
these notes are source deliverables.

## Retained development failures and regressions

The original row-scanning baseline passed three of seven scenes: left/right arcs
and the original arc. Both right angles stopped after classifying the lateral exit
as a broad dark area. Straight and S runs each had one TF-related stop. Original
source, images, locations and reasons remain in `baseline/`.

Development records also retain near-footprint seeding failures, short-support
incoming-heading errors, ambiguous blind-edge fragments, the 18 mm parking sweep
violation, evaluator TF-relay latency and two controller boundary defects found
by repeated acceptance:

- A lookahead crossing exactly on a shared segment endpoint could be rejected by
  both segments due to floating-point roundoff. A numerical-tolerance clamp fixes
  that boundary; 100,000 deterministic perturbations had no missed crossings,
  with a 1,000-case C++ regression included.
- A disarmed zero and the first armed command could straddle a quantized clock
  boundary and double the measured startup acceleration. Arming now restarts the
  ramp interval and periodic zero/nonzero commands use consistent tick stamps.
  Twenty independent quantized-clock arming repetitions pass.

Acceptance thresholds were unchanged. Interrupted frozen rounds remain separate
from the last version's success rate. When an invalid image cannot produce a new
ground projection, a saved ground debug view can still be the last valid projection.
Fault evidence combines actual relayed input, observation validity, state,
individual commands and physical truth checks; an old overlay is not new evidence.
