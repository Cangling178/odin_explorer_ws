# Hardware bringup

Only model preview and historical developer-laptop cloud inspection are available. There is no autonomous hardware launch.

1. **Manually moved mapping:** verify driver commit, firmware and USB. Observe walls, furniture and doors at actual mounting height; return to the start. Check saving, relocalization, loop consistency and measured dimensions. Record clouds, pose, TF and versions. Vendor maps are not navigation grids.
2. **Bench and teleoperation:** verify F4, motor driver, encoders and wiring. Test wheel direction/control with wheels lifted; malformed, duplicate/reordered commands, disconnect and reset stopping. Measure wheel radius, effective track, speeds and braking; discard simulation corrections.
3. **Localization and timing:** measure mounting extrinsics, assign unique TF publishers, keep local odometry continuous and global corrections separate. Record delays, age and resets. Device calibration is not mounting calibration.
4. **Goal navigation while mapping:** choose the mapper; verify occupied/free/unknown, clearing and loop consistency. Check measured footprint, obstacle heights and close/rear blind zones. Start with low-speed goals in observed free space. Stale input stops without automatic restart.
5. **Exploration:** bound the laboratory area; test reachability, timeouts, failed goals and completion/save when no reachable frontier remains. Report successes, interventions, localization failures, coverage, occlusions and all failed trials.

Archive runnable revisions, configuration, reproduction instructions and result summaries per stage. Bags go in `data/bags/`, maps in `data/maps/`. Set numeric acceptance thresholds from measurements before trials.
