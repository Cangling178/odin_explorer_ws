# Accuracy and speed evaluation

English | [Chinese](08_evaluation_cn.md)

## Define what is measured

Confirm the competition's judged point on the robot. Until then, report errors
at the chosen `base_link` control origin and label that choice. Use calibrated
overhead video or another independently surveyed reference to evaluate absolute
path error. Onboard estimates remain useful diagnostics but are not ground truth.

Register the measured course and robot reference point in one metric frame.
Associate samples with the correct ordered course segment, including repeated
crossing visits. An unconstrained nearest-line metric can reward the wrong branch.
Record survey and camera uncertainty alongside the results.

## Core report

- Valid completion time: directed start-to-finish event time, only after the
  required checkpoints in order. Report incomplete attempts separately.
- RMS lateral error, mean absolute error, P95 absolute error and maximum error.
- Valid measurement time coverage and invalid intervals; lost samples are not zeros.
- Time outside the selected error tolerance, labeled as an internal threshold.
- Wrong-branch events, retries, intervention and completion status.
- Across repeated runs: success fraction and valid-time median/spread, with sample count.

## Included offline evaluator

`tools/evaluate_run.py` consumes timestamped, **already associated** cross-track
error samples and a run manifest. It does not process images, infer ground truth,
assign crossing branches, or certify the manifest's completion claim.

Required CSV columns are `time_s,error_m,valid`. `valid` is exactly `0` or `1`;
valid errors must be finite. Timestamps must be finite and strictly increasing.
Each sample holds until the next sample or the declared finish time, limited by
`max_sample_hold_s`. Uncovered and invalid intervals count against coverage.
Samples must lie inside the declared run interval. The last sample can cover a
bounded final interval; a lone sample cannot cover an arbitrary whole run.

Errors are weighted by their valid held duration. P95 is the smallest absolute
error whose cumulative time weight reaches 95%. Tolerance uses strict `>`.
Report both raw elapsed time and `completion_time_s`; the latter is null for an
incomplete or wrong-branch attempt. A fully covered interval with zero error
still needs a valid, positive elapsed duration. No valid duration yields null
error metrics, never perfect accuracy.

The manifest includes `run_id`, `data_kind`, `measurement_source`, `start_time_s`,
`end_time_s`, `completed`, `wrong_branch_events`, `tolerance_m` and
`max_sample_hold_s`. The included `data_kind=synthetic` example only demonstrates
the tool. Future bag extraction and route association belong in `racer_evaluation`.

## Experiment procedure

1. Freeze the route hash, calibration revision, Git commit and parameter snapshot.
2. Record tire/surface condition, lighting, sensor pose, battery state and payload.
3. Start independent measurement and onboard recording; verify synchronized events.
4. Run an accuracy baseline, then change one control/speed setting at a time.
5. Repeat each setting with the same start condition; log every attempt.
6. Compare valid completion time versus error, not speed alone. Retain failures.

Hold out a few trials from tuning. Separate controller error from localization
error by comparing both to the independent reference. Inspect per-segment plots
and crossing event logs before accepting an apparent speed improvement.

## Proposed test matrix

| Scenario | Failure being tested |
| --- | --- |
| Straight at several modest speeds | Scale, delay and oscillation |
| Both crossing traversals | Wrong branch or progress jumps |
| Tight turn and reverse curvature | Lookahead corner cutting, wheel saturation |
| Bright/dim light and shadows | Segmentation confidence and recovery |
| Image dropout or stale pose | Timely stop and no false zero error |
| Controller restart / command loss | Lower-level watchdog |
| Repeated full route | Thermal, battery and accumulated drift |

The test matrix is a plan; no real-world results are included at initialization.
