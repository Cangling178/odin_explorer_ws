# Development and repository conventions

English | [Chinese](07_development_cn.md)

The local development baseline is Ubuntu 22.04 / ROS 2 Humble. Target Jetson compatibility is not yet validated. Run commands from the workspace root in a clean ROS 2 terminal.

## Build and preview

```bash
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src --rosdistro humble -r -y
colcon build --symlink-install --base-paths src
source install/local_setup.bash
ros2 launch racer_bringup preview.launch.py
```

`rosdep` installs dependencies and assumes rosdep is initialized. Preview uses RViz, robot_state_publisher, joint_state_publisher and xacro; `rviz:=false` disables the window. Preview publishes no motor commands. Simulation entry points are in [simulation](../simulation/README.md).

For vendor hardware, first build/load the [vendor underlay](../vendor_ws/README.md), then build/load this overlay. Do not mix ROS distributions. `vendor_ws/COLCON_IGNORE` and `--base-paths src` isolate vendor packages.

## Checks

```bash
python3 tools/check_workspace.py
python3 -m unittest discover -s tests -v
colcon test --base-paths src --packages-select racer_perception racer_control
colcon test-result --verbose
git diff --check
```

Python requirements are in `tools/requirements-dev.txt`; image tests also use OpenCV and geometry tests use xacro. The standalone CSV evaluator uses the standard library. CI runs repository checks, Python tests, builds and C++ tests; it does not run rendered Gazebo scenarios or hardware.

After building and sourcing the overlay, synthetic ROS controller checks are:

```bash
python3 tools/validate_line_controller.py
python3 tools/validate_arming_clock.py
python3 tools/validate_lap_controller.py
```

These use isolated domains and synthetic inputs. Dynamic tests require a rendering environment and are documented with [lap](../simulation/COMPETITION_LAP.md) and [local tracking](../simulation/LINE_FOLLOWING.md) entry points. Validation scope and evidence live in [experiments](../experiments/README.md), not duplicate running totals in every guide.

## File ownership and contributions

- Code and runtime configuration belong to the owning package under `src/odin_racer/`; device facts to `hardware/`; course facts to `tracks/`; run summaries to `experiments/`.
- `*.template.yaml` files are specification forms. Keep unknown facts unset; create validated runtime parameter files when implementing a component. Record geometry, route and tuning versions separately.
- Keep vendor sources, SDK binaries, recordings, credentials and generated reports out of Git. Record upstream revision/license and data paths/hashes. Raw local evidence lives under `data/generated/` and must not be mistaken for source documentation.
- Retain English and matching `_cn.md` documents with reciprocal links. Identifiers, user-facing program strings and commit messages remain English; code/config comments may be Chinese. Keep technical meaning synchronized.
- Keep one authoritative page per topic; link to test results rather than copying them into status pages. Do not add empty directory READMEs or duplicate roadmaps. The project backlog is [planning](planning/README.md).
- Use focused branches and commits. Document behavior, relevant validation and limitations; distinguish simulation, synthetic data and real measurements. Run relevant checks; test behavior changes where needed, without pretending that package builds prove hardware readiness.

Remote repository: [Cangling178/odin_racer_ws](https://github.com/Cangling178/odin_racer_ws). Follow [LICENSE](../LICENSE) and retain upstream ownership notices. PR/issue templates in `.github/` support concise evidence-based changes.
