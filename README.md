# Odin Racer

A ROS 2 workspace for a four-wheel, Jetson Orin Nano robot using the Manifold
ODIN1 sensor module. The primary objective is to follow a marked competition
course accurately and quickly **without a dedicated line-tracking module**.

**Current stage: project foundation, not a drive-ready robot.** The existing chassis has two rear drive motors and two front passive casters.
A separate F4 lower-level controller is present; its exact board and motor/encoder
specifications are not yet recorded. Sensor adapters, motor
drivers, perception and autonomous control remain to be implemented.

## Start here

1. Read [requirements](docs/01_requirements.md); resolve the remaining judging and route details.
2. Fill [hardware inventory](hardware/bom.csv) and [robot specification](hardware/robot_spec.template.yaml).
3. Review [architecture](docs/02_architecture.md) and [course strategy](docs/05_course_strategy.md).
4. Follow [development setup](docs/07_development.md) to build the foundation.
5. Work through [milestones](management/ROADMAP.md) and [backlog](management/BACKLOG.md).

## Design priorities

- Use local camera observations to measure line-relative error, with camera use allowed by the owner
  and a required ODIN1 ground-visibility test.
- Use wheel feedback and ODIN1 localization for motion continuity and route context.
- Track an **ordered route**, including the correct branch at the crossing.
- Establish repeatable accurate runs before increasing speed.
- Treat general Nav2 navigation as an optional later capability.

The proposed software baseline is Ubuntu 22.04 / ROS 2 Humble with a compatible
JetPack 6.x installation. Confirm the actual Jetson image, driver and firmware
together before freezing versions. See [platform decision](docs/adr/0001_platform.md).

## Workspace layout

```text
odin_racer_ws/
  src/odin_racer/       Ten first-party ROS 2 packages
  vendor_ws/           Separate future ODIN1 vendor underlay
  docs/                Requirements, design, interfaces, runbooks and decisions
  hardware/            Inventory, dimensions, electrical and calibration records
  firmware/            Future lower-level controller and protocol specification
  tracks/              Reference image, surveyed routes and course metadata
  simulation/          Future simulation scenarios and acceptance criteria
  tools/               Offline evaluation and repository validation
  tests/               Offline evaluator regression tests
  experiments/         Run manifests, procedure and compact result tables
  data/                Ignored bag files, video, maps and generated outputs
  management/          Roadmap, backlog, risks and decision log
  .github/             Optional issue/PR templates and scaffold CI
```

The repository root is also the colcon workspace root. `build/`, `install/` and
`log/` are generated and ignored. See [validation evidence](management/VALIDATION.md). Detailed package responsibilities are in
[src/README.md](src/README.md). Planning YAML files are explicitly named
`*.template.yaml`; they are not executable ROS parameter configurations.

## Available now

```bash
cd ~/odin_racer_ws
python3 tools/check_workspace.py
python3 -m unittest discover -s tests -v
python3 tools/evaluate_run.py experiments/examples/synthetic_samples.csv \
  --metadata experiments/examples/synthetic_run.json
source /opt/ros/humble/setup.bash
colcon build --symlink-install --base-paths src
source install/local_setup.bash
ros2 launch racer_bringup preview.launch.py
```

The preview publishes an illustrative robot model and stationary joint states.
It does not connect to hardware. Launch RViz separately if desired. Dimensions
in the preview must be replaced with measured geometry before integration.
The evaluator example is synthetic; its results are not robot performance.

## Implementation status

| Capability | State |
| --- | --- |
| English documentation and local project management | Included |
| ROS package discovery, asset build and model preview | Included |
| Offline error/time report from validated CSV and metadata | Included |
| ODIN1 driver and calibration adapter | Planned; vendor code not downloaded |
| Motor interface, watchdog and encoder odometry | Planned |
| Visual line extraction and crossing association | Planned |
| Trajectory generation, speed profile and tracking controller | Planned |
| Autonomous race launch and hardware validation | Planned |
| Nav2 integration and physics simulation | Planned |

This is a local repository; no remote hosting or publishing is configured.
Original scaffold licensing is reserved pending the owner's decision; see
[LICENSE](LICENSE). References and upstream distinctions are in
[sources](docs/REFERENCES.md).
