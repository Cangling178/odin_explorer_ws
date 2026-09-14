# Foundation validation

English | [Chinese](VALIDATION_cn.md)

Date: 2026-09-10. Platform: existing x86_64 workstation, Ubuntu 22.04 userspace,
ROS 2 Humble, Python 3.10.12. This is not Jetson or physical robot validation.

| Check | Result | Scope |
| --- | --- | --- |
| `python3 tools/check_workspace.py` | Pass | Ten package manifests, Python/YAML syntax, authored English text and local Markdown links |
| `python3 -m unittest discover -s tests -v` | Seven tests pass | Time weighting, invalid data, gaps, completion policy and malformed inputs |
| Synthetic evaluator command in README | Pass | 0.4 s synthetic elapsed time, 75% valid time coverage, approximately 0.02160 m RMS |
| `colcon list --base-paths src` | Ten packages discovered | First-party assets only |
| `colcon build --symlink-install --base-paths src --executor sequential` | Ten packages built successfully | Asset installation, not implemented autonomy |
| `ros2 launch racer_bringup preview.launch.py --show-args` | Pass | Installed launch loading and argument resolution |
| Installed Xacro expansion and structural inspection | Pass | Six links, five joints, exactly two drive joints and two caster links; no actuator plugin |
| `git diff --cached --check` | Pass at foundation commit | Whitespace consistency |
| Generated/vendor/capture ignore checks | Pass | Build, install, logs, vendor sources and bag paths excluded |

The sandboxed colcon process stalled after CMake configuration. A bounded build
outside that sandbox completed all ten packages in approximately 5.2 seconds.
This was an execution-environment limitation; no dependency installation was needed.

No live ROS preview nodes, RViz window, camera, motor controller, Jetson target,
firmware flash, simulated physics or autonomous run was tested. The supplied
course image is retained unchanged; measured centerline coordinates remain empty.
The initial local Git repository has branch `main` and no remote. Generated
build artifacts are excluded from the delivered source workspace; build again
at its final location using the documented command.

## Chinese documentation update

Date: 2026-09-11. Added 51 `_cn.md` counterparts and reciprocal language links.
Checks passed for translation coverage, local links, matching section/table counts,
unchanged shell commands and issue-template front matter fields. The updated
structural checker accepts Chinese only in `_cn.md` documents and requires
paired language navigation. All ten ROS packages rebuilt successfully; each
installed Chinese README was compared with its source. No robot runtime changed.

## ros2_control basic motion validation — 2026-09-13

Local Gazebo Classic 11.10.2 / ROS 2 Humble, not F4 or Jetson hardware acceptance.
The existing 0.877 kg mass and 25 collisions are preserved. A differential-drive
controller commands both wheel velocity interfaces; wheel odometry is separate
from Gazebo truth. Build and 14 unit tests pass. Forward/reverse, both in-place
turns, arc, excessive input, zero-command stop, publisher loss and stale-command
checks pass, including speed/acceleration/effort limits, wheel feedback and TF.
Settings, the simulator-only 1.10 separation fit and reproduction commands are in
the [simulation guide](../../simulation/README.md#ros2_control-vehicle-motion-simulation).
`tools/validate_sim_drive.py` produces full metrics. Race arbitration, hardware
communication and moving sensor generation remain unimplemented. Commit preparation corrected full
repository checker binary/vendor scanning and temporary-document language pairing;
full repository checks pass.

## Onboard Odin sensor validation — 2026-09-13

The vehicle includes image, CameraInfo, cloud and IMU by default, sharing bench settings
and deriving extrinsics from the Xacro fixed-joint chain. All ten local packages build
and 18 unit tests pass. New tests cover rotated mounts and camera axes, bench/vehicle
consistency, unchanged physics when sensors are disabled, and invalid settings/moving-mount rejection.

`tools/validate_sim_sensors.py` passed stationary, forward, both turn directions, acceleration/braking,
projection/cloud/IMU/TF/stamp/rate checks in a fresh known-target world; the local report is
`data/generated/sim_sensors_validation.json`. A subsequent `tools/validate_sim_drive.py` run passed
all six motion stages and stopping/limit regression checks, saved as
`data/generated/sim_drive_with_sensors_validation.json`. The standalone bench entry point was
rechecked: all four message types arrived, with 1600x1296 images, a nonempty cloud and stationary
IMU Z=9.81 m/s^2; local record: `data/generated/odin_bench_regression.json`. Generated reports are
not tracked in Git. Key parameters, metrics and reproduction commands are in the
[onboard sensor guide](../../simulation/README.md#onboard-odin-sensors).

Real-time factor was about 0.62 and still needs optimization. Complete black-line visibility,
a self-occlusion test matrix, algorithm closure and hardware equivalence remain unaccepted.

## Competition drawing scene — 2026-09-13, prepared for commit on 2026-09-14

The 2.00 x 1.50 m image reconstruction is integrated into the vehicle scene, preserving vehicle
mass, collisions and contact settings. Four new structural tests cover physics isolation, asset scale
and provenance hashes, disabled onboard sensors/optional overview combinations, and incompatible
scene settings. All 22 unit tests pass.

`tools/validate_competition_course.py` passed a live run: approximately 0.116 m forward motion
followed by a stop, overhead black IoU about 0.853/0.851 and onboard IoU about 0.926/0.933.
Cloud ground, stationary IMU, stamp and rate checks passed. Image/cloud reception was about 10 Hz,
overview 2 Hz and IMU 333 Hz against a configured 400 Hz target, with real-time factor about 0.84.
Rates use simulation time and apply only to this computer and run load.

Local reports and images are `data/generated/competition_course_validation*`, excluded from Git.
Key metrics, thresholds, limitations and reproduction commands are in the
[competition course guide](../../simulation/COMPETITION_COURSE.md). The source image is unchanged;
survey templates remain empty and official start/direction/branch sequence are unconfirmed.
This change does not implement line detection or autonomous tracking.

Pre-commit checks on 2026-09-14 passed: repository structure/language pairs/local links,
22 unit tests and all ten first-party packages with `colcon build --base-paths src`.
README, architecture, development workflow, plan and changelog are synchronized.
