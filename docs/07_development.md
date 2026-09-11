# Development workflow

English | [Chinese](07_development_cn.md)

## Platform baseline

Use a clean shell with the intended ROS distribution. The foundation targets
Humble; the local workstation can build assets without a Jetson or ODIN1.
Record actual software versions in `hardware/platform_lock.template.yaml` when
the target is commissioned. No setup script flashes devices, installs packages,
changes udev rules or starts motors automatically.

## Build and inspect

```bash
cd ~/odin_racer_ws
source /opt/ros/humble/setup.bash
colcon list --base-paths src
colcon build --symlink-install --base-paths src
source install/local_setup.bash
ros2 launch racer_bringup preview.launch.py --show-args
ros2 launch racer_bringup preview.launch.py
```

Preview needs `robot_state_publisher`, `joint_state_publisher` and `xacro` from
the selected ROS installation. To inspect it visually, run `rviz2` in another
sourced terminal, set Fixed Frame to `base_link`, and add RobotModel and TF.
The package launch also supports `use_sim_time:=true` when a clock is supplied.
Stationary preview joints are illustrative; this is not physics simulation.

After ROS and rosdep are installed and initialized, the standard optional
dependency step is:

```bash
rosdep install --from-paths src --ignore-src --rosdistro humble -r -y
```

This command may install system packages; it has not been run by this scaffold.
Planning packages intentionally declare only dependencies used by existing code.
Add runtime dependencies as real nodes are implemented, rather than forcing a
full navigation/GPU stack onto a documentation-only package.

## Offline checks

```bash
python3 tools/check_workspace.py
python3 -m unittest discover -s tests -v
python3 tools/evaluate_run.py experiments/examples/synthetic_samples.csv \
  --metadata experiments/examples/synthetic_run.json
git diff --check
```

The structural checker requires PyYAML; the evaluator and its tests use the
Python standard library. See `tools/requirements-dev.txt`. The optional GitHub
workflow runs structural checks, offline tests and an asset build; it is only
active if the owner later hosts this repository on GitHub.

## Vendor underlay

Use a separately audited vendor build in `vendor_ws/`. A `COLCON_IGNORE` file
prevents accidental recursive discovery from the root. Source its installed
setup before building the first-party overlay, then source the overlay's
`install/local_setup.bash`. The root build uses `--base-paths src` explicitly.
Do not source ROS 1 or a different ROS 2 distribution in the same shell.

## Git workflow

Keep `main` as the reviewed foundation. For work use a focused branch such as
`codex/encoder-odometry`. Link commits to requirement/backlog IDs where useful.
Use concise messages such as `feat(hardware): add wheel feedback parser` or
`docs(course): record crossing order`. Run relevant checks before merging.
Tag actual milestones after recording evidence; do not tag untested autonomy.

No remote is configured. Choosing an open-source license and publishing are
separate future decisions. The local templates work without GitHub: copy a
task entry into `management/BACKLOG.md` and record evidence beside it.
