# Competition reference course world

English | [Chinese](COMPETITION_COURSE_cn.md)

The complete track has been reconstructed from the supplied [competition drawing](../tracks/reference/course_reference.jpg),
including straights, the central crossing, loops, tight bends and lower S-bends. It uses the existing
vehicle physics, ros2_control and onboard Odin image, CameraInfo, cloud and IMU. The scene supports
black-line perception development. Single-branch low-speed tracking is implemented; see [line following](LINE_FOLLOWING.md) and [right-straight/lower-wave tracking](LINE_FOLLOWING.md). Full-course routing and crossing selection are validated with the selected simulation route; see [continuous lap](COMPETITION_LAP.md).

## Launch

From the workspace root:

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-select racer_description racer_control racer_bringup
source install/local_setup.bash
ros2 launch racer_bringup simulation.launch.py course:=competition
```

Gazebo and onboard sensors are enabled by default. The car starts on the upper straight, facing
right in the drawing, and waits for velocity commands. `course:=empty` keeps the original default
test scene; `sensors:=false` disables onboard sensors. `gui:=false` closes the window, but cameras
still require a working DISPLAY/rendering environment. Competition mode rejects `sensor_targets:=true`
to keep sensor test fixtures out of the course.

Onboard topics and RViz setup follow the [simulation guide](README.md). For RViz Image, use
`/sim/racer/odin1/image`, Reliable, Volatile, depth=5 and `use_sim_time=true`. The camera sees the
black line; the ray cloud does not model black/white material intensity and will not show its pattern.

Add `course_overview:=true` for the fixed inspection camera: `/sim/course/overview/image`
(1000x750, 2 Hz, Reliable) and `/sim/course/overview/camera_info`. This is inspection instrumentation,
not part of Odin or an algorithm input. It has a separate frame name without a published TF;
use RViz Image for display.

## Scale, coordinates and approximations

| Item | Implementation |
| --- | --- |
| Board | Default scale 2: 4.00 x 3.00 m white plane, centered at the world origin; original assets are 2.00 x 1.50 m |
| Axes | Drawing right = +X, drawing top = +Y, up = +Z |
| Extraction | Source 905x738; crop `[9,90,859,728]` with exclusive right/bottom bounds; 850x638 texture |
| Black line | Source extraction removes text, annotations and borders; runtime redraws the connected skeleton at about 21.2 mm independently of map scale |
| Pixel scale | Original texture: about 2.35 mm/px in X/Y; runtime uses four-times pixel resolution, about 1.18 mm/px at default map scale 2 |
| Black outer extent | Original assets: about 1.635 x 1.218 m, not current runtime dimensions; not forced to match red annotations. Runtime scales the centerline independently of stroke width |
| Initial vehicle pose | `base_link` X about -1.1929 m, Y about 1.2014 m, yaw=0; release height from the contact model |
| Ground | Black and white areas share existing flat contact/friction; visual at Z=0.2 mm, no added collision |

The white board and black line share one textured mesh, surrounded by gray ground. Physical support
remains the original 20x20 m scene plane. There are no board-edge steps, fences, boundary obstacles
or automatic penalties. Part of the vehicle can extend outside the white board; this does not establish
competition compliance. Lighting is fixed and basic; illumination changes, dirt and real print materials are absent.

This version is an **image reconstruction, not a surveyed replica**. Annotation extents may refer to
different boundaries, and pixel uncertainty remains. Scale follows the outer board dimensions while
preserving the drawing's internal proportions. Line width, start/finish, direction and crossing order
still need confirmation. The initial pose is a debug spawn, not an official start. The
[surveyed route template](../tracks/competition/course.template.yaml) remains unfilled; no ordered
centerline suitable as hardware ground truth has been generated.

![Extracted complete course texture](../src/odin_racer/racer_description/meshes/competition_course/course.png)

## Generation and changes

- [Extraction specification](../tracks/competition/reference_reconstruction.yaml): source, board crop/dimensions and debug spawn.
- [Generator](../tools/generate_competition_course.py): PNG, metric COLLADA plane and source-hashed configuration.
- [Generated configuration](../src/odin_racer/racer_description/config/competition_course.yaml): scale, estimated width, spawn and provenance status.
- [World assembly](../src/odin_racer/racer_description/racer_description/course_world.py): inserts the course into the driven vehicle world.

Original texture and mesh are checked in; source extraction is unnecessary for normal use. Runtime uses OpenCV to generate temporary assets with a fixed physical stroke width.
`course_parameters` accepts `scale` (default 2.0), `line_width` (default about 0.02116 m), and `spawn_x/y/yaw`.
Default spawn scales with the map; explicit spawn coordinates are world metres and are not scaled again.
See [line following](LINE_FOLLOWING.md#competition-wave-segment) for the corresponding upper-right spawn.
 After changing the
specification, regenerate, rebuild and restart:

```bash
# Runtime map repainting, asset generation and image validation need these dependencies.
sudo apt-get install python3-opencv python3-numpy python3-yaml
python3 tools/generate_competition_course.py
```

Image extraction is not survey acceptance evidence. Revise scale/width when vector originals or measurements arrive.

## Validation

This historical projection validator reads original asset coordinates. Use `scale: 1.0` below; it does not validate the default scale-2 map.

Start a fresh world in a dedicated ROS domain and Gazebo port without another velocity publisher:

```bash
source /opt/ros/humble/setup.bash
source install/local_setup.bash
export ROS_DOMAIN_ID=74
export GAZEBO_MASTER_URI=http://127.0.0.1:11356
ros2 launch racer_bringup simulation.launch.py course:=competition course_overview:=true gui:=false \
  course_parameters:='{scale: 1.0}'
```

In another terminal with the same ROS/workspace environment and `ROS_DOMAIN_ID=74`:

```bash
python3 tools/validate_competition_course.py
```

This projection validator uses original resource coordinates and requires `scale: 1.0` as above; it does not validate the default scale-2 map.

The validator commands 0.08 m/s on the upper straight for 1.5 simulated seconds, then stops. Restart
before repeating. It compares overhead black pixels to the texture and checks onboard projection
using CameraInfo, TF and settled Gazebo poses. It also checks cloud ground returns, stationary IMU,
received sensor rates and short forward motion. Overhead comparison excludes the vehicle/shadow;
onboard comparison covers useful forward ground within 1 m, not complete-course visibility.
The JSON report and two pairs of PNGs are written to `data/generated/competition_course_validation*`.

Current camera evidence is in [FishPoly validation](FISHPOLY_CAMERA.md); former pinhole metrics are not the current baseline.

Structural tests are in `tests/test_course_world.py`:

```bash
python3 tools/check_workspace.py
python3 -m unittest discover -s tests -v
```

The existing `validate_sim_sensors.py` requires red/blue fixtures in the empty scene;
`validate_sim_drive.py` also assumes the empty-scene origin. Neither is a competition-course validator.
Acceptance here establishes scene loading, texture projection and basic motion, not autonomous laps,
crossing decisions or agreement with the physical course.
