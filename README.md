# Odin Racer

English | [Chinese](README_cn.md)

A ROS 2 four-wheel line-following robot: Jetson Orin Nano + ODIN1 + an F4 controller. The goal is accurate, fast tracking of a marked competition course without a dedicated line-tracking module.

**This is a project scaffold. Model preview, ros2_control vehicle simulation and offline evaluation run; autonomous hardware control is not implemented.**

## Start here

| Task | Entry point |
| --- | --- |
| Find the main code and module responsibilities | [Source guide](src/README.md) → `src/odin_racer/` |
| Build and preview the robot model | [Development](docs/07_development.md) |
| Understand design and interfaces | [Architecture](docs/02_architecture.md), [interface contracts](docs/06_interfaces.md) |
| Find the next task | [Project plan](docs/planning/README.md) |
| Find other documentation | [Documentation map](docs/README.md) |

## Workspace layout

| Directory | Contents |
| --- | --- |
| `src/odin_racer/` | First-party ROS 2 packages; implement the main functions here |
| `firmware/` | F4 firmware and protocol; documentation only for now |
| `hardware/` | Inventory, measured geometry, wiring and calibration |
| `tracks/` | Course reference image and unfilled route data |
| `tools/`, `tests/` | Runnable offline evaluator, repository checker and evaluator tests |
| `experiments/` | Run records, result table and synthetic examples |
| `data/` | Large local captures and generated results, excluded from Git |
| `vendor_ws/` | Separate vendor driver workspace; v0.14.4 built locally; point cloud display confirmed |
| `simulation/` | Usage and validation for sensor, ground-contact and vehicle-motion simulation |
| `docs/` | Technical docs, contribution guide and changelog; plans in `planning/` |

The root is also the colcon workspace root. `build/`, `install/` and `log/` are generated build outputs. `*.template.yaml` files are specification forms, not runtime ROS parameters.

## Run the offline example first

From the workspace root, without connecting a robot:

```bash
python3 tools/evaluate_run.py experiments/examples/synthetic_samples.csv \
  --metadata experiments/examples/synthetic_run.json
```

The output uses synthetic data, not measured robot performance. Build, preview and full check commands are maintained in [Development](docs/07_development.md).

Before hardware integration, fill the [inventory](hardware/bom.csv) and [robot specification](hardware/robot_spec.template.yaml), then follow the [project plan](docs/planning/README.md). Two rear drive wheels and two front passive casters are confirmed; the exact F4 board, motors and encoders still need verification.

See [LICENSE](LICENSE) for licensing and [References](docs/REFERENCES.md) for sources.
