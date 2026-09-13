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
