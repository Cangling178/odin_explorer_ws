# Isolated visual tracking: acceptance and reproduction

English | [Chinese](RESULTS_cn.md)

The original frozen version passed **42/42 tracking trials and 12/12 fault trials**, all with one binary. Source consistency was checked at freeze time, not against today's workspace. Later wave-segment development changed perception/control; its evidence is recorded separately at the end of this page and is not part of that frozen cohort.

These are historical Gazebo engineering results, not hardware, official corridor acceptance or a rerun of the current version. Original criteria, JSON, figures and failure evidence are retained.

[Criteria](acceptance.json) · [Frozen results](results.json) · [Implementation and launch](../../simulation/LINE_FOLLOWING.md) · [Reproduction](#reproduction)

## Fixed-parameter tracking

Each scene includes two centered starts, lateral offsets +/-35 mm, and heading offsets +/-0.08 rad.
Every metric below is the worst value across that scene's six trials, in millimeters.
RMS/P95 use elapsed-time weights and include the initial correction.

| Scene | Passed | Full RMS | Full P95 | Full max | Tail RMS | Swept upper bound |
| --- | --- | --- | --- | --- | --- | --- |
| `line_straight` | 6/6 | 17.53 | 34.81 | 35.00 | 3.73 | 185.73 |
| `line_arc` | 6/6 | 13.53 | 34.18 | 35.00 | 5.41 | 212.07 |
| `line_left` | 6/6 | 17.05 | 34.93 | 35.00 | 7.54 | 212.08 |
| `line_right` | 6/6 | 16.85 | 34.73 | 35.00 | 6.20 | 212.20 |
| `line_s` | 6/6 | 17.45 | 34.70 | 35.11 | 13.86 | 213.50 |
| `line_corner_left` | 6/6 | 29.59 | 65.00 | 75.46 | 43.40 | 220.31 |
| `line_corner_right` | 6/6 | 29.99 | 66.77 | 78.48 | 44.47 | 222.28 |

The 15 mm tail RMS criterion applies to straight/arc regression only. S and corners
use full-run RMS/P95/max limits of 60/100/140 mm plus the unchanged 230 mm corridor
half width, ordered route gates and the end region. The maximum observed acquisition
age was 0.21 s (limit 0.35 s). Normal command limits
were 0.05 m/s, 0.5 rad/s, 0.15 m/s² and 0.8 rad/s²; all passed.

The corner stop setback is 80 mm. The vehicle turns with zero commanded translation,
then requires three distinct valid exit observations before resuming. Rejoining the
exit produces about 75-78 mm maximum deviation in these runs; this is included in
full-run error, not hidden by a tail-only check. Phase metrics in each raw report
follow controller states: correction after REACQUIRE is part of normal tracking.
The filled body envelope includes wheels/front plate, spatial covering error and
motion between samples. Worst final bound is 222.28 mm versus the fixed 230 mm limit.

![S trajectory, error and commands](figures/s_center.png)
![Single left corner, including exit correction](figures/left_corner_center.png)
![Right-turn chassis sweep](figures/right_corner_sweep.png)
![Onboard projected centerline, corner and target](figures/corner_observation.png)

## Faults and focused regression

Each row was a separate fresh simulation. All reached the requested moving phase,
requested stop within 0.6 s, physically stopped within the 1.2 s check, and stayed
latched for the 1 s restored-input observation. Deliberate CORNER_STOP is distinct
from fault STOPPED. Delay below measures the STOPPED notification after injection.

| Phase and fault | Request delay [s] | Stop and recovery latch |
| --- | --- | --- |
| `RUNNING_drop` | 0.29 | PASS |
| `RUNNING_blank` | 0.29 | PASS |
| `RUNNING_tf` | 0.40 | PASS |
| `RUNNING_odom` | 0.17 | PASS |
| `APPROACH_drop` | 0.29 | PASS |
| `APPROACH_blank` | 0.35 | PASS |
| `APPROACH_tf` | 0.35 | PASS |
| `APPROACH_odom` | 0.17 | PASS |
| `TURN_drop` | 0.27 | PASS |
| `TURN_blank` | 0.32 | PASS |
| `TURN_tf` | 0.37 | PASS |
| `TURN_odom` | 0.22 | PASS |

The final source also passed 35 Python tests, 21 C++ test cases (colcon reports
23 including two suite results), 17 synthetic ROS controller checks, and 20
quantized-clock repeated enable trials. Saved static left/right corner and S images
also replayed successfully through the final C++ offline perception executable.

## Baseline, failed attempts and evidence

The unchanged original algorithm passed 3/7 baseline scenes: original/left/right
arcs. Both corners stopped on the horizontal wide region; straight and S each
stopped for missing TF. Baseline source, binaries, images, positions and reasons
are retained. Those single attempts are diagnostic, not a statistically matched
success-rate comparison with the final repeated matrix.

All development failures and aborted earlier frozen rounds remain in
`data/generated/isolated/`. These include seed/branch mistakes, short direction
support, instrumentation TF latency, an 18 mm corner setback with a 282 mm body
sweep bound, a shared-segment endpoint floating-point failure, and startup clock
quantization violating acceleration bounds. The stop position and implementation
were corrected; reference lines, corridor and acceptance thresholds were not relaxed.
Earlier runs are excluded from the final 54-trial result.

Final raw evidence is in `data/generated/isolated/validated/`: `index.html`,
`final_summary.json`, `final_curves/`, `final_turns/`, `final_faults/`, `offline/`
and `final_source/`. Per-run JSON retains all samples, commands, phase metrics,
state transitions, parking positions and checks; PNGs include raw/input images,
mask, ground projection and annotated geometry. Images are sampled once per
simulation second and at transitions; they are not a lossless camera recording.
The full archive is `data/generated/isolated_delivery.tar.gz`; generated evidence
is intentionally ignored by Git. The small figures and numerical summary here are
part of the source delivery. Launch and reproduction commands are in the linked guides.

## Frozen acceptance conditions

[acceptance.json](acceptance.json) records error,
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

These commands run the current workspace version. To reproduce the historical frozen results, restore the recorded source/binary and configuration in a separate workspace first; a current-version rerun is a new cohort.

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

## Later wave-segment results (2026-09-15)

The actively enabled competition segment passed; reports are in `data/generated/competition_waves/final/shared_memory_segment/`.
Spawn `(1.614118, 1.284377, -π/2)`; endpoint region near `(-1.5174, -0.9786)`; simulated travel time 123.13 s.

| Item | Measurement |
| --- | --- |
| Full-run axle lateral error RMS / P95 / maximum | 10.99 / 17.66 / 52.11 mm |
| Maximum chassis-envelope offset, including sampling cover | 214.10 mm, below the 230 mm engineering half-width |
| Ordered route gates | 64/64 |
| Maximum received image gap / accepted observation age | 0.10 / 0.20 s |
| Complete route, command bounds, explicit stop and 0.35 s observation deadline | All passed |

This is one complete low-speed simulation run, not hardware, full-lap or repeated-reliability evidence.

Limited regression for that historical version:

| Check | Result |
| --- | --- |
| Existing isolated S | Endpoint in 41.18 s; RMS 16.09 mm, maximum 39.88 mm |
| Left right-angle corner | Endpoint in 38.81 s; RMS 24.30 mm, maximum 70.20 mm; all corner states exercised |
| Image drop while RUNNING on competition map | Stop requested in 0.24 s; physical stop and fault latch passed |
| C++ geometry/control cases | 24 passed |
| Python evaluation and scene-generation cases | 10 passed |
| Controller ROS input checks | 17 passed |
| Build, documentation pairs/links and syntax | Passed |

S and image-drop reports are in `s_regression/` and `image_drop/` under the same `final/` directory.
The left-corner report is in `corner_left/`; this geometry regression preceded the final shared-memory fix. The full historical matrix was not rerun.
