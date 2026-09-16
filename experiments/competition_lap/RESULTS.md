# Continuous competition lap: acceptance result

English | [Chinese](RESULTS_cn.md)

Current summary: initial acceptance passed, followed by three passing 0.05 m/s repeats and one passing 0.10 m/s trial. The first table records initial acceptance; later sections record repeat and speed results.

**One complete continuous Gazebo lap passed: 185/185 ordered gates, no mid-lap stop, and automatic stop at the finish.**

| Metric | Measured |
| --- | --- |
| Ordered reference length | 18.440 m |
| Completion time, simulation clock | 367.29 s |
| Axle line error RMS / maximum | 5.32 / 22.25 mm |
| Minimum measured translation during driving | 19.13 mm/s |
| Maximum valid image-health observation age | 0.18 s |
| Longest visual alignment age | 7.05 s; image health and wheel odometry remained current |
| Ordered gates | 185/185 |
| Mid-lap stop / final physical stop | None / passed |

![Full trajectory, measured speed and line error](trajectory.png)

## Scope

The C++ runtime uses a prerecorded ordered route, onboard FishPoly visual alignment and wheel odometry.
Map, vehicle and camera are unchanged. Gazebo truth only enters the independent Python evaluator.
The lap starts down the right straight, covers the lower waves, left lobe, upper-left rectangle, central loop,
and both crossing visits before returning to the start.

Criteria were fixed before running: ordered gates every 100 mm with 100 mm radius; maximum axle error 100 mm and time-weighted RMS 50 mm.
After the first 1 s and before finish braking, every measured translation must exceed 3 mm/s and every forward command must be positive.
The run recorded 6619 trajectory samples; all 6599 moving samples after startup and before finish passed continuity checks.
Finish uses a 25 mm route-progress tolerance near the start and an independent 100 mm position radius, not exact mathematical coincidence.

This is one selected-route simulation acceptance, not repeatability, hardware, body-corridor or official route-order acceptance.
The 22.25 mm maximum error does not mean the axle always remained inside the approximately 21 mm painted stroke.

## Version and reproduction

[Run and validate](../../simulation/COMPETITION_LAP.md) | [Machine-readable summary](results.json)

The full report is `data/generated/competition_lap/attempt07/index.html`; its directory also contains `report.json`,
`trajectory.png`, `launch.log`, `source_manifest.json` and `final_source/`.
The controller source, route header, route data and runtime binary were checked against recorded hashes after the run.
Large raw evidence remains local; this page, plot and summary are included in the source tree.

Earlier failures remain alongside it: early attempts stopped after insufficient single-branch observations;
`attempt04` latched a startup stale frame before moving; `attempt06` misassociated other visible loop segments after the central loop,
reached 188.88 mm maximum error and stopped. The final implementation localizes against the complete map while ordered progress
constrains driving branch selection. Acceptance limits were not relaxed.
`attempt01` has incomplete evidence after evaluator serialization failed and is excluded from success counts;
`attempt05` never started because the test port was occupied.

## Nominal-start repeat acceptance

Three independent starts using identical runtime inputs and parameters all passed full-lap, continuous-motion and final-stop acceptance, each with 185/185 gates.

| Trial | Time/s | RMS/mm | Max error/mm | Min moving speed/mm/s |
| --- | --- | --- | --- | --- |
| run_01 | 367.31 | 5.27 | 22.07 | 19.17 |
| run_02 | 367.36 | 5.27 | 22.19 | 19.01 |
| run_03 | 367.26 | 5.30 | 21.97 | 19.47 |

All three complete command streams also passed: no nonpositive mid-lap forward commands. This validates nominal-start repeatability, not arbitrary poses, disturbances or hardware. [Machine-readable summary](repeat_results.json). Raw report: `data/generated/competition_lap/repeat_nominal_01/index.html`. All 41 Python regression tests passed.

## Single 0.10 m/s speed trial

Only the speed setting changed to 0.10 m/s; lookahead stayed 0.10 m and acceptance limits were unchanged. All checks passed: 185/185 gates, continuous motion and final stop.

- Lap time: 197.43 s, 46.2% shorter than the three-run 0.05 m/s baseline mean.
- RMS / maximum error: 5.60 / 24.14 mm.
- Minimum moving speed: 16.71 mm/s; tight bends automatically slow down.
- Full command audit: 14405 mid-lap commands, none zero or reverse.

[Machine-readable result](speed_010_results.json). Raw report: `data/generated/competition_lap/speed_010_01/index.html`. One trial only; default launch speed remains 0.05 m/s. The controller was unchanged.
