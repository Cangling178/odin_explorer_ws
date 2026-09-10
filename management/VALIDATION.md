# Foundation validation

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
