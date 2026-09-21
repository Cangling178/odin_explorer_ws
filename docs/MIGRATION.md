# Independent clone and reduction

2026-09-21. New project: **Odin Explorer**, workspace `/home/cangling/odin_explorer_ws`, package prefix `explorer_`.

Source: `/home/cangling/odin_racer_ws`, commit `4c90a5bb555000edf11772b69beb729c93b187bd`. Cloned with `--no-hardlinks` for independent history/object storage; branch `explorer-foundation`. Removed the new clone's origin to avoid pushing to the source. No edits to the original directory.

Retained body/motor/ODIN housing Xacro and meshes, original CAD/device calibration, BOM and unmeasured specifications, F4 protocol, ODIN notes, preview and relevant hardware/localization/navigation contracts. Retained wheel interface choices from the differential controller, without simulation tuning.

Removed five competition packages (control, perception, interfaces, trajectory, evaluation), LineObservation, line algorithms/routes, track images/world generation, Gazebo/camera plugins, simulated sensor TF, competition results, old tools/tests and CI.

Renamed six retained packages to explorer_description, explorer_bringup, explorer_hardware, explorer_odin, explorer_localization and explorer_navigation. Keep one workspace/model checker and lightweight CI, no placeholder algorithm tests.

Old build/install/log and generated data were not copied. Independently copied ignored `vendor_ws/src/odin_ros_driver`, its Git history and SDK at `f51051f2d861f7643d4d33d2ade2952efe1a4672`; third-party naming is unchanged. Rebuild the vendor underlay in the new directory.

Old implementation/results remain recoverable from the source and cloned Git history, not the current tree. This migration does not implement F4 transport, SLAM occupancy adaptation or navigation, and inherits no simulation acceptance claims.

## Verification

All six packages built with colcon. Minimal checks passed for dependencies, 40 documents, Python syntax, 16 model links and mesh assets. Headless preview published both wheel joint states and shut down cleanly. First-party current files reduced from 224 to 82, excluding Git history, build outputs and the independent vendor checkout. SHA-256 comparisons confirmed the original 224 tracked files and Git index were unchanged. No hardware, device connection or navigation tests were performed.
