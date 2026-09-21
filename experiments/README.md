# Validation evidence and data

English | [Chinese](README_cn.md)

Use this index to distinguish historical simulation evidence from current checks. **No real-vehicle tracking acceptance is recorded.** Updating documentation does not rerun dynamic tests or update their original source hashes.

| Evidence | Version/date and scope |
| --- | --- |
| [Competition laps](competition_lap/RESULTS.md) | 2026-09-16 selected route: original pass, 0.05 m/s 3/3 independent starts and one 0.10 m/s pass; unchanged criteria and original JSON summaries |
| [Isolated tracking](isolated_line/RESULTS.md) | Historical frozen 42 tracking + 12 fault runs; later wave-segment evidence kept separately on the same page |
| [FishPoly camera](../simulation/FISHPOLY_CAMERA.md) | 2026-09-14 geometry, target and course projection; original device/model constraints |
| Foundation/contact/drive | 2026-09-10–13 historical checks; see summary below |
| Documentation cleanup | 2026-09-21: repository checks and 45 Python tests passed during review; no new Gazebo or hardware trial |

## Retained foundation evidence

Initial package/preview checks were for the earlier scaffold, not today's algorithm. Subsequent 2026-09-13 contact tests observed 10.036 simulation seconds: base height about 33.1267 mm vs nominal 33.25 mm, only the two rear wheels and two front supports contacting the ground. Drive tests passed forward/reverse, both turns, arc, saturation and stops. With a 0.1 m/s command, stream loss started observed deceleration around 0.30 s and reached the stop threshold around 0.60 s, with about 44.9 mm extra travel. These are historical model results, not real braking limits.

Local reports: `data/generated/ground_contact_validation.json`, `sim_drive_validation.json`, `sim_drive_with_sensors_validation.json` and `sim_sensors_validation.json`. Early pinhole-camera measurements have been superseded for camera validation by the linked FishPoly record. [Component reproduction commands](../simulation/README.md) remain available; earlier incremental test totals are not current regression counts.

## Data and evaluation

[Evaluation semantics](../docs/08_evaluation.md) define time weighting, invalid intervals and ordered association. The standalone demonstration uses synthetic data:

```bash
python3 tools/evaluate_run.py experiments/examples/synthetic_samples.csv   --metadata experiments/examples/synthetic_run.json
```

`run.template.yaml` and `results.csv` are run-record scaffolding, not real achievements. Git retains source/calibration references, small figures, machine-readable summaries and synthetic examples. Large images, bags, logs and frozen binaries/source snapshots remain in ignored `data/generated/`; preserve paths, hashes, version and conditions when citing them. Do not merge failed/development runs into a frozen acceptance cohort or delete underlying evidence merely because its narrative was consolidated.
