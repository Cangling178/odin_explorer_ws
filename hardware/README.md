# Hardware records

English | [Chinese](README_cn.md)

Hardware facts and modeling assumptions belong here. Host/firmware integration and calibration procedures are in [hardware bringup](../docs/09_bringup.md).

| Record | Scope |
| --- | --- |
| [bom.csv](bom.csv) | Inventory and unresolved electrical/device details |
| [robot_spec.template.yaml](robot_spec.template.yaml) | Unfilled measured robot specification; not runtime parameters |
| [platform_lock.template.yaml](platform_lock.template.yaml) | Target OS/JetPack, driver and firmware lock; not yet validated |
| [Chassis record](mechanical/chassis_plate/README.md) | CAD source, confirmed/reference dimensions, assumptions and conversion |
| [ODIN record](mechanical/odin1/README.md) | CAD provenance, installation assumptions and device calibration |

Two rear drive motors, passive front supports and an F4 controller are confirmed. Mechanical references identify MG513X GMR 500-line, 1:28 motors; actual electrical ratings, counts per output revolution, driver, F4 board and transport remain unverified. Device point-cloud display was observed on the workstation; Jetson readiness is not established.

Create `electrical/` when wiring/power records exist and `calibration/<revision>/` for measured data and residuals. Empty placeholder READMEs have been removed. Unknown specification fields remain unset; source CAD, device calibration and reference values are not a complete measured vehicle model.
