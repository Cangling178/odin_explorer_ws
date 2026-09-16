# Isolated visual tracking: delivered results

English | [Chinese](RESULTS_cn.md)

The final frozen implementation passed **42/42 tracking trials and 12/12 fault trials**.
All 54 trials used one binary version; the archived source matched the workspace at freeze time.
Competition-map generation and documentation have since changed to default scale 2 with fixed stroke width;
subsequent map-wave development also changes perception and control, so the results here apply only to the original frozen version. The source-match field in `results.json` records the freeze-time check, not a live check of the current workspace.
This is Gazebo validation of the existing vehicle under an engineering corridor condition;
it does not establish hardware performance or official competition compliance.

[Criteria](acceptance.json) | [Machine-readable results](results.json) |
[Implementation and launch](../../simulation/LINE_FOLLOWING.md) |
[Independent evaluation and reproduction](../../simulation/ISOLATED_LINE_VALIDATION.md)

This page records the original frozen version. Subsequent [map wave tracking changes](../../simulation/COMPETITION_WAVES.md) modify perception and control; these 54 trials are not repeated acceptance of the new version.

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
