# Changelog

English | [Chinese](CHANGELOG_cn.md)

## Unreleased

- Three independent nominal starts passed at 0.05 m/s in 367.26–367.36 s. One 0.10 m/s trial passed in 197.43 s with 5.60/24.14 mm RMS/maximum error. Every run passed 185/185 ordered gates without a mid-lap stop. Repeatability at 0.10 m/s is untested; the default remains 0.05 m/s. Hardware milestone dependencies M2–M8 remain open.
- Add the C++ full-map controller, ordered route generation, lap/fault/repeat validators and bilingual status updates distinguishing simulation implementation from hardware dependencies.

- Add ordered skeleton paths, adaptive lookahead and single-corner stop/turn/reacquisition; archive 42/42 isolated tracking and 12/12 fault trials with evaluation tools.
- Default competition map to twice the original size (4 by 3 m), retaining about 21.2 mm stroke width and corresponding spawn positions; synchronize bilingual launch, map and validation scope documentation.

- Add C++ single-branch perception, FishPoly ground projection, Pure Pursuit, explicit enabling and latched stops; add straight/arc fixtures, ROS fault checks and C++ tests.

- Establish an English ROS 2 project foundation for an ODIN1/Jetson four-wheel racer.
- Document course tracking, crossing topology, calibration, timing and evaluation.
- Add ten buildable package asset skeletons and a non-actuating model preview.
- Add an offline time-weighted error evaluator with synthetic fixtures.
- Add local milestones, backlog, risks, decisions and optional GitHub templates.
- Keep hardware drivers and autonomous runtime explicitly unimplemented.
- Add `_cn.md` translations for all Markdown documents with bidirectional language links, language-aware checks and ROS package documentation installation.
- Add plate/Odin1 CAD models, approximate inertias and collisions, a standalone sensor scene, and contact and basic ros2_control motion validation.
- Record the local vendor-driver build and initial point cloud check; target-platform acceptance, F4 communication and autonomous line following remain pending.
- Synchronize English and Chinese architecture, development, bringup, planning and simulation documentation, distinguishing current capabilities, target design and historical validation scope.
- Integrate onboard Odin images, clouds and IMU with shared settings and Xacro extrinsics; add known fixtures and automated motion-response validation.
- Reconstruct the 2.00 x 1.50 m competition drawing with `course:=competition`, an optional overhead camera, reproducible asset generation and projection/motion validation.
- Synchronize English/Chinese course usage, dimension provenance, validation records and source navigation; simulated line-following development can begin, while detection/tracking algorithms and the surveyed route remain pending.
