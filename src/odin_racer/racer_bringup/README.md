# racer_bringup

English | [Chinese](README_cn.md)

Launch composition for preview and simulation. [Build instructions](../../../docs/07_development.md).

| Launch | Scope |
| --- | --- |
| `preview.launch.py` | Static model/TF in RViz; no drive commands |
| `simulation.launch.py` | ros2_control base, optional onboard sensors/course/targets |
| `line_following.launch.py` | Local visual tracking; explicit enable |
| `competition_lap.launch.py` | Image-map-assisted ordered lap; explicit enable and finish stop |

[Simulation options](../../../simulation/README.md) · [Local tracking](../../../simulation/LINE_FOLLOWING.md) · [Lap operation](../../../simulation/COMPETITION_LAP.md).
No real-vehicle race launch exists. Hardware adapters, readiness checks and command arbitration remain to implement. `robot_profile.template.yaml` is a specification, not a deployable robot profile.
