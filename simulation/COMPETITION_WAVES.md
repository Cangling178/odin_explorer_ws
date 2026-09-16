# Competition right straight and lower waves

English | [Chinese](COMPETITION_WAVES_cn.md)

Scope: the default scale-2 competition map (4 by 3 m), starting downward at the upper-right pose,
following the right straight, tight lower-right bend and bottom waves toward the left.
This segment excludes the central crossing, full-lap routing and hardware control.

## Implementation

Perception and control remain C++. Python selects the simulation spawn, extracts evaluation-only
reference geometry and records results. Map texture, vehicle and camera models are unchanged.

- Perception expands the ground search region and rejects thick dark areas before near-seed selection;
  at least 100 mm of observed curved line is accepted.
- The controller joins overlapping camera paths in wheel odometry and retains already observed
  points entering the near blind zone. Disjoint distant paths neither replace the near cache nor refresh its age.
- Measured near history permits shorter preview; short remaining paths reduce speed.
  The cache does not invent unseen centerline points.
- When a tight curve exit leaves the camera view, translation pauses and the vehicle aligns with the
  observed exit tangent, resuming only after acquiring a usable camera path.
  Existing right-angle handling, explicit arming and image/TF/odometry watchdogs remain.

## Launch

After building and sourcing ROS and the workspace:

```bash
ros2 launch racer_bringup line_following.launch.py course:=competition gui:=true \
  course_parameters:='{scale: 2.0, line_width: 0.02116, spawn_x: 1.614118, spawn_y: 1.284377, spawn_yaw: -1.570796}'
```

Enable after READY using the service in [line following](LINE_FOLLOWING.md).
Normal launch does not automatically stop at this segment endpoint.

## Single-run validation

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

Image freshness is restored to 0.35 s and the wall watchdog to 1 s. The 12 s path memory only bridges geometric blind spots while images keep updating.
Evaluation uses the original frozen thresholds; experimental relaxed deadlines are absent from the final configuration, and failed reports are retained.
This segment and limited regression do not replace the complete historical 54-run isolated-scene matrix.

## Measured results (2026-09-15)

The actively enabled competition segment passed; reports are in `data/generated/competition_waves/final/shared_memory_segment/`.
Spawn `(1.614118, 1.284377, -π/2)`; endpoint region near `(-1.5174, -0.9786)`; simulated travel time 123.13 s.

| Item | Measurement |
| --- | --- |
| Full-run axle lateral error RMS / P95 / maximum | 10.99 / 17.66 / 52.11 mm |
| Maximum chassis-envelope offset, including sampling cover | 214.10 mm, below the 230 mm engineering half-width |
| Ordered route gates | 64/64 |
| Maximum received image gap / accepted observation age | 0.10 / 0.20 s |
| Complete route, command bounds, explicit stop and 0.35 s observation deadline | All passed |

This is one complete low-speed simulation run, not hardware, full-lap or repeated-reliability evidence.

Limited regression in this change:

| Check | Result |
| --- | --- |
| Existing isolated S | Endpoint in 41.18 s; RMS 16.09 mm, maximum 39.88 mm |
| Left right-angle corner | Endpoint in 38.81 s; RMS 24.30 mm, maximum 70.20 mm; all corner states exercised |
| Image drop while RUNNING on competition map | Stop requested in 0.24 s; physical stop and fault latch passed |
| C++ geometry/control cases | 24 passed |
| Python evaluation and scene-generation cases | 10 passed |
| Controller ROS input checks | 17 passed |
| Build, documentation pairs/links and syntax | Passed |

S and image-drop reports are in `s_regression/` and `image_drop/` under the same `final/` directory.
The left-corner report is in `corner_left/`; this geometry regression preceded the final shared-memory fix. The full historical matrix was not rerun.
