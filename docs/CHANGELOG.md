# Changes

English | [Chinese](CHANGELOG_cn.md)

## 2026-09-21

Consolidated documentation by topic: architecture includes tracking decisions; development includes repository/contribution rules; hardware bringup includes calibration and ODIN integration; model scope replaces temporary gap/component lists. Local experiment criteria, reproduction and wave-segment evidence now share the isolated-results page. Removed duplicate directory indexes and superseded status narratives; kept bilingual package READMEs required by installation, original CAD/calibration, source configurations and acceptance artifacts. Corrected inventory reference status. No code or runtime-parameter changes.

The preceding code commit formatted C++ and allowed Chinese comments; identifiers and program-facing strings remain English.

## 2026-09-16

Added C++ ordered full-lap control, image-map alignment, route generation and independent lap/fault/repeat tools. [Lap evidence](../experiments/competition_lap/RESULTS.md) retains original and repeated outcomes.

## 2026-09-14–15

Added FishPoly rendering, C++ visual tracking, bounded corner behavior and independent/fault validation. Default map became 4×3 m with separately controlled line width; subsequent local wave tracking changed perception/control. [Frozen and later local evidence](../experiments/isolated_line/RESULTS.md) remain separate cohorts.

## 2026-09-10–13

Created the ROS workspace, bilingual documentation and synthetic evaluator; imported vendor driver with workstation cloud-display evidence; added CAD/approximate dynamics, contact, drive, sensors and image-derived course. These foundations did not establish hardware autonomous operation.
