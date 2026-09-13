# racer_description

English | [Chinese](README_cn.md)

Robot geometry and frame definitions.

## Status

Available: CAD plate and Odin1 meshes, rear drive wheels/front ball transfers,
RViz preview, approximate inertias for the existing 0.877 kg mass subtotal, and
primitive collision geometry. The level plate height is a user-selected 62 mm.
Chassis contact and ros2_control motion tests pass; measured calibration remains pending.

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

## Collision geometry

The expanded model contains 25 primitive collisions on 16 physical/visual links:

- Plate: a 247.416 x 220 x 3.5 mm slab and a separate box enclosing raised CAD
  features. Bounds were extracted from the existing STL. Cutouts and the empty
  space between raised features are conservatively filled; narrow-clearance and
  self-collision checks require a more detailed shape.
- Tires: cylinders matching the visual radius/width, with their axes along Y.
- Motors, encoder covers, brackets and output shafts: boxes/cylinders matching
  the existing approximate visual geometry. Brackets retain their two-piece L shape.
- Standoffs: circumscribed cylinders around the hex prisms, radius equal to
  across-flats width divided by sqrt(3), extending downward from the mounting face.
- Ball transfers: separate sphere and housing cylinder per assembly. The flange
  remains omitted because its dimensions are incomplete.
- Odin1: a 46.4 x 100 x 62 mm box centered at (-3.6, 0, 31) mm in odin_link,
  enclosing the CAD body and connectors. This differs from the body-only inertia box.

No mass, inertia, visual geometry or joint topology was changed by this addition.
Internal overlaps at the shaft/hub and ball/housing are intentional assembly
approximations; self-collision is not enabled. The source URDF retains component
structure; the dedicated contact generator lumps fixed bodies, preserves massless
part collisions and applies ground_contact.yaml settings. Front balls use
low-friction sliding, not real rolling support.

Validation (2026-09-13): source Xacro expansion and package build passed. All
collision dimensions are positive; all visual links have collisions; both tires
and both balls reach Z=-0.03325 m relative to base_link, with no collision below
that plane. The 9 inertial links still total 0.877 kg. These are geometry checks,
not a Gazebo drop, rolling or motion test.

## Dynamic contact scene

After building, run `ros2 launch racer_description ground_contact.launch.py`;
append `gui:=false` for headless use. The generator creates three bodies from the
current Xacro, preserving all collisions and the 0.877 kg mass subtotal.
This scene tests gravity, support and settling. It accepts no drive commands and
publishes no vehicle TF or Odin sensor data. Settings, isolated launch commands
and passed drop checks are in the [simulation guide](../../../simulation/README.md#chassis-ground-contact-test).

The motion scene starts through `racer_bringup simulation.launch.py`. The optional sim_control Xacro argument declares control interfaces; the existing contact generator gains the Gazebo control plugin. See [motion simulation](../../../simulation/README.md#ros2_control-vehicle-motion-simulation).
