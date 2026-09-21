# C++ local visual tracking

English | [Chinese](LINE_FOLLOWING_cn.md)

Use `line_controller` for straight, arc, S-curve and single-corner experiments. It can stop and turn and does not have a full-course route. Use [lap control](COMPETITION_LAP.md) for continuous ordered laps. Historical frozen acceptance and reproduction are in [isolated results](../experiments/isolated_line/RESULTS.md); those results do not certify later controller changes.

## Build and run

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --symlink-install
source install/local_setup.bash
export ROS_DOMAIN_ID=73
export GAZEBO_MASTER_URI=http://127.0.0.1:11355
ros2 launch racer_bringup line_following.launch.py course:=line_corner_left gui:=false
```

The simulated onboard camera needs a working `DISPLAY`. Use unused domain/master
ports. Scenes: `line_straight`, legacy regression `line_arc`, `line_left`,
`line_right`, `line_s`, `line_corner_left`, `line_corner_right`. The existing
`competition` entry remains available without full-route support.

In another terminal with the same environment, inspect readiness and explicitly
arm the vehicle. Enabling causes actual simulation motion:

```bash
ros2 topic echo /sim/racer/line/tracking_status
# Use another terminal for services while echo runs.
ros2 service call /sim/racer/line/line_controller/enable std_srvs/srv/SetBool '{data: true}'
ros2 service call /sim/racer/line/line_controller/enable std_srvs/srv/SetBool '{data: false}'
```

Fixtures accept a YAML/JSON map, for example:

```bash
ros2 launch racer_bringup line_following.launch.py course:=line_right \
  course_parameters:='{radius: 0.8, line_width: 0.021, spawn_y: 0.035, spawn_yaw: 0.08}'
```

Only the renderer and independent evaluator receive fixture geometry. The end
region is evaluator instrumentation: runtime nodes have no preset end or turn
answer. The evaluator requests an explicit stop after reaching the end region.

To start near the leftmost trough of the bottom S bend on the complete map,
facing right, close the old simulation and launch:

```bash
ros2 launch racer_bringup line_following.launch.py course:=competition gui:=true \
  course_parameters:='{scale: 2.0, spawn_x: -1.20, spawn_y: -1.16, spawn_yaw: 0.0}'
```

This pose is estimated from the reconstructed texture, not an official start.
Competition now defaults to twice the original linear map dimensions: 4 by 3 m
instead of 2 by 1.5 m. Stroke width now defaults to approximately 21.2 mm
independently of map scale. The S-bend example above
explicitly selects scale 2. Vehicle geometry, onboard
camera intrinsics are unchanged by map scaling; current tracking parameters are listed below. Set `scale: 1.0` for the
original map size. Explicit spawn overrides are world metres after scaling and
are not scaled again; the default map spawn scales automatically. GUI and optional
overview camera positions also scale. Original map asset files remain unchanged. Motion still requires explicit enable.
The compact S bend on the full map has not passed the isolated-scene acceptance
matrix; successful placement does not establish successful tracking.

## Perception

The original FishPoly forward projection, six distortion coefficients, skew and
acquisition-time image/CameraInfo matching are retained. A three-image queue selects the newest complete pair so interleaved DDS delivery cannot overwrite every unpaired image. A metric ground grid is
projected into the onboard image using camera TF. Visible dark pixels form a mask;
Zhang–Suen thinning forms the centerline skeleton. An eight-neighbor graph removes
redundant diagonal triangles and short terminal noise spurs attached to junctions.

One near-vehicle connected component is seeded using the previous acquisition's
position and heading, motion compensated through TF when available. The search
accounts for the actual near camera footprint. The graph is traversed in connected
arc order, allowing lateral exits and decreasing forward coordinates. Occluded
gaps are not bridged. Corners retain their original geometry instead of being
replaced by a smoothed chord. Thickness is measured locally, independent of line
orientation. Multiple exits truncate the prefix and prohibit driving into a fork.

A direction change supported by approximately 65 mm on each side produces a
corner and observed exit direction. The controller additionally fits incoming
heading from a straight support longer than 120 mm before the corner; insufficient support cannot
refresh corner memory. Invalid path, absent line, ambiguous exits and unhealthy
image/projection are explicit. A nearly uniform raw frame is unhealthy. Image
health does not imply that a line is visible.

The header algorithm is ROS independent. `line_offline` replays a saved
metric ground grayscale PNG (append `0.10 0.50` after the output prefix for the current grid; omit for the historical grid) and writes mask, skeleton, annotated corner/exit and
ordered-path JSON. The fixed threshold is validated only for the current simulated
lighting, not real-world shadows. Confidence is an engineering quality score, not a calibrated probability.

## Tracking and compensation

`racer_interfaces/LineObservation` atomically carries the acquisition-stamped
path, image health, confidence and corner/exit evidence. Paths are transformed
into wheel `odom` at acquisition time and back into the current body frame each
control cycle. A bounded five-entry FIFO waits for asynchronously arriving TF
without blocking the timer. Only successful transforms renew freshness; missing
TF still expires the original acquisition deadline. Duplicate/reordered data
cannot renew either watchdog.

Path checks validate finite coordinates, segment gaps and total arc length,
replacing the previous strict forward-coordinate ordering. Pure Pursuit selects
the first forward lookahead-circle crossing. Lookahead depends on speed, measured
curvature and visible distance with hard 0.12–0.45 m bounds, and must lie beyond
the retained observed-path start. Insufficient evidence stops the vehicle. The previous target
is retained in odometry and constrains the next target in both current-path arc
coordinates and physical distance. Angular capability and remaining visible
stopping distance cap speed. Normal commands retain acceleration shaping.

The controller retains observed near points in `odom`, joining only overlapping paths and replacing
the overlap boundary to avoid accumulating clipped skeleton tips. `observed_path_memory` defaults to
12 s; healthy image/TF acquisitions must still meet the 0.35 s deadline, and odometry freshness is unchanged.
Short remaining paths reduce speed. A tight bend may enter `CURVE_ALIGN`: translation pauses while
turning toward the last observed exit tangent, and resumes only with a new usable camera path.
Failure to reacquire within 5 s stops the vehicle. This is separate from the right-angle sequence below.

## One-corner state machine

```text
RUNNING -> APPROACH -> CORNER_STOP -> TURN -> REACQUIRE -> RUNNING
                              fault -> STOPPED (latched)
```

At least three distinct, consistent acquisitions confirm a corner. Approach
follows the observed incoming direction, slows and requests stopping roughly
80 mm before the corner at the axle center. `CORNER_STOP` requires valid odometry
below 5 mm/s and 0.02 rad/s, plus at least 0.3 s dwell. Failure to stop is a fault.

The differential chassis turns with zero translation and bounded low yaw speed.
The last reliable observed corner and exit may survive the near blind zone in
wheel odometry, bounded by 18 s, 0.45 m cumulative translation and 1.9 rad cumulative
rotation. Exceeding any bound latches a fault. Healthy images, TF and odometry
remain mandatory throughout; fixture identity never provides a turn direction.

Heading agreement only enters `REACQUIRE`. Translation remains zero until three
different camera acquisition stamps contain a sufficiently long, position- and
direction-consistent exit path. No reacquisition within 2.5 s stops the vehicle.
The completed isolated corner cannot retrigger. This is not multi-corner routing.

`CORNER_STOP` is a deliberate maneuver state; `STOPPED` is a latched fault.
Recovered data never automatically re-arms a faulted vehicle. Fault zero requests
bypass normal shaping; physical braking remains subject to the lower controller
and contact model.

## Parameters and debugging

| Setting | Default |
| --- | --- |
| Metric grid | x 0.10–0.75 m, y +/-0.50 m, 5 mm cells |
| Ground plane | 33.25 mm below base_link, flat-ground approximation |
| Dark threshold / thickness | gray 65 / 8–50 mm |
| Minimum path length / lateral seed gate | 0.10 m / +/-0.45 m |
| Speed / lookahead | <=0.05 m/s / 0.12–0.45 m |
| Yaw / linear / angular acceleration | <=0.5 rad/s / 0.15 m/s² / 0.8 rad/s² |
| Corner approach / yaw speed | <=0.04 m/s / <=0.30 rad/s |
| Observation / odometry deadline | 0.35 s / 0.15 s; 0.02 s future tolerance |
| Wall watchdog / control timer | 1 s / 20 ms; not a hard realtime guarantee |

Files: [perception](../src/odin_racer/racer_perception/config/line_perception.yaml),
[control](../src/odin_racer/racer_control/config/line_controller.yaml). Override with
`perception_config` or `controller_config` and restart; live tuning is not implemented.

Topics below use the `/sim/racer/line/` prefix:

| Topic | Meaning |
| --- | --- |
| `observation` | Atomic `LineObservation` used for control |
| `local_path` | Acquisition-stamped ordered metric `nav_msgs/Path`, for inspection |
| `perception_status` | Detection reason, confidence, truncation reason and processing time in ms |
| `ground_gray`, `black_mask`, `ground_debug` | Metric grayscale, mask, centerline/corner/exit overlay |
| `tracking_status` | State and stopping reason; Transient Local |
| `control_debug` | JSON ages, target, lookahead, odometry corner/exit, memory use and commands |

Images publish only with subscribers. Commands go to
`/sim/racer/diff_drive_controller/cmd_vel`. Fault-test launch remaps are
`image_topic`, `odom_topic`, `tf_topic`; defaults use direct onboard simulation
streams. Runtime nodes never subscribe to Gazebo truth, overview cameras, fixture
geometry or reference paths.

## Competition wave segment

After building and sourcing ROS and the workspace:

```bash
ros2 launch racer_bringup line_following.launch.py course:=competition gui:=true \
  course_parameters:='{scale: 2.0, line_width: 0.02116, spawn_x: 1.614118, spawn_y: 1.284377, spawn_yaw: -1.570796}'
```

Enable after READY using the service shown above.
Normal launch does not automatically stop at this segment endpoint.

This command starts an isolated simulation, actively enables tracking and stops at the evaluation endpoint.
A working DISPLAY is required:

```bash
python3 tools/validate_isolated_line.py --course competition --duration 240 \
  --output data/generated/my_competition_waves
python3 tools/report_isolated_line.py data/generated/my_competition_waves
```

Reference geometry is extracted from the connected right/bottom source-image skeleton solely for
error, order and endpoint checks; runtime algorithms never receive it. The spawn precedes the visible
straight, so its tangent is extended backward only for initial-error and footprint measurement.
The scene is unchanged. The endpoint is at the left end of the waves before the small source-image gap.
Reports include axle error and chassis sweep; the inherited 230 mm corridor half-width is an engineering condition only.

## Simulation timing

Normal validation uses onboard image, TF and odometry directly, enabling relays only for the selected fault injection.
Perception/control default to Release; perception, camera plugin and evaluator limit OpenCV workers.
Line-following enables `lockstep:=true` to synchronize physics and rendering; actual speed depends on host load.
Map, output resolution/calibration, physics integration step and vehicle speed retain their original values.

A 1600 by 1296 RGB frame is about 6.22 MB, exceeding Fast DDS's default 512 KiB shared-memory segment.
When reception drops frames while the source keeps producing them, adjusting rendering threads or watchdogs does not fix transport.
Line-following defaults to [line_fastdds.xml](../src/odin_racer/racer_bringup/config/line_fastdds.xml),
providing 64 MiB shared memory per DDS participant while retaining UDP discovery; image receivers use SensorDataQoS.
See the [Fast DDS shared-memory documentation](https://fast-dds.docs.eprosima.com/en/2.6.x/fastdds/transport/shared_memory/shared_memory.html).
Override with `dds_profile:=...`; an existing `FASTRTPS_DEFAULT_PROFILES_FILE` environment setting is respected.

Image freshness remains 0.35 s and the wall watchdog 1 s. The 12 s path memory only bridges geometric blind regions while healthy images continue.
