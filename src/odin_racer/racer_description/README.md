# racer_description

English | [Chinese](README_cn.md)

Robot geometry and frame definitions.

## Status

Available: CAD plate and Odin1 meshes, rear wheels/front ball transfers, RViz preview,
approximate inertias for the existing 0.877 kg mass subtotal and standalone Odin sensors.
Vehicle collision/contact and drive simulation remain pending.

## Responsibility and acceptance

Backlog: HW-001, CAL-001. See the root architecture and interface documents.
This package currently installs assets/documentation through ament_cmake.
A successful build is not evidence that a planned subsystem runs.

## Configuration

Any `*.template.yaml` is a specification form, not a live ROS parameter file.
Add runtime dependencies, executables and tested parameters when implementing
the component. Keep vendor code and large recordings outside this package.

## CAD preview

From the workspace root:

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-select racer_description racer_bringup
source install/local_setup.bash
ros2 launch racer_description preview.launch.py
```

Append `rviz:=false` for headless use. No Odin or F4 is required; no motor commands are published.

## Odin1

Official STEP geometry and approximate 280 g mass added; mounting assumptions
are documented in [the mounting record](../../../hardware/mechanical/odin1/README.md).
