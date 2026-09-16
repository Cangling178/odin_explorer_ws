# Continuous competition-map lap

English | [Chinese](COMPETITION_LAP_cn.md)

Goal: follow the existing Gazebo competition line for one complete lap without stopping between startup and the finish.
The approved approach combines a prerecorded ordered route, onboard visual alignment and wheel odometry.
Runtime perception and control are C++; Python prepares resources, launches simulation and independently evaluates it.

## Route and inputs

The map remains 4×3 m with approximately 21.2 mm strokes. Texture, vehicle and camera models are unchanged.
Start midway down the right straight facing down, follow the lower waves, left lobe, upper-left rectangle,
central loop, then pass the crossing toward the upper right and return to the start. The crossing is visited twice.
The original damaged left stroke is traversed using mapped continuity while healthy camera images remain required.
This is an explicitly selected simulation route, not an assertion of official competition order.

`tools/generate_competition_lap.py` extracts an ordered skeleton route into
`racer_control/config/competition_lap.csv` with source provenance. Runtime never subscribes to Gazebo truth,
an overhead camera, or evaluator feedback.

`lap_controller.cpp` associates position inside an ordered progress window to avoid jumping between crossing visits.
Point-to-line registration aligns timestamped narrow-line skeletons from the ground mask with the full map using acquisition-time TF and wheel odometry. The ordered window constrains driving progress; localization includes other visible loop limbs.
During ambiguous visual crossings, travel of at most 0.65 m using the known route is permitted without successful visual alignment.
Pure Pursuit reduces forward speed at tight bends and does not enter the older stop-and-turn state machine.

Image age is limited to 0.35 s, odometry age to 0.15 s and wall watchdogs to 1 s. Fault stops latch.
Explicit enable is required; one completed lap stops automatically.

## Build and run

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --symlink-install
source install/local_setup.bash
export ROS_DOMAIN_ID=96
export GAZEBO_MASTER_URI=http://127.0.0.1: 11396
ros2 launch racer_bringup competition_lap.launch.py gui:=true
```

A working DISPLAY is required for camera rendering. After READY, enable from another terminal with the same environment:

```bash
ros2 service call /sim/racer/line/lap_controller/enable std_srvs/srv/SetBool '{data: true}'
```

Set `data` to `false` to stop. Restart simulation to begin a new full lap with reset spawn and progress.
`control_debug` reports progress, estimated pose, observation age, visual residual and commands.
The existing `line_following.launch.py` remains the single-branch entry point.

## Independent acceptance

This actively starts an isolated simulation and enables the robot. Use a new output directory:

```bash
python3 tools/validate_competition_lap.py --output data/generated/competition_lap/my_run
python3 tools/report_competition_lap.py data/generated/competition_lap/my_run
```

Criteria are fixed before the run:

- Visit ordered gates every 100 mm within 100 mm; return to the start with FINISHED.
- Axle-to-map maximum error ≤100 mm and time-weighted RMS ≤50 mm.
- After the first 1 s and before finish, every forward command is positive and measured translation exceeds 3 mm/s.
- Check observation and truth freshness, command limits, single command publisher and final physical stop.

These are engineering criteria, not a promise that the axle always lies inside the 21 mm stroke or meets official scoring.
Reports include `report.json`, `trajectory.png`, `launch.log` and source/binary hashes.
Gazebo truth is used only by the evaluator and is never fed back to control.

## Validation status

One complete dynamic lap passed: 367.29 s, 185/185 gates, no mid-lap stop; axle RMS 5.32 mm, maximum 22.25 mm, minimum driving speed 19.13 mm/s.

[Acceptance result and scope](../experiments/competition_lap/RESULTS.md). Raw HTML report: `data/generated/competition_lap/attempt07/index.html`.

Final checks: all 11 packages built; 32 C++ test records reported by colcon passed (including suite results); 41 Python tests and 12 ROS controller checks passed.
The historical 54-run isolated dynamic matrix was not repeated and does not cover this new controller.

## Repeated independent trials

Run three sequential, independently started simulations with the same program, map, parameters and acceptance criteria. Each trial rebuilds the simulation world at the nominal start. Use a new output directory:

```bash
python3 tools/repeat_competition_lap.py --output data/generated/competition_lap/my_repeats
```

The output directory contains `index.html` and `summary.json`, plus separate reports and logs for each trial. Input and binary fingerprints guard against combining different runtime versions. This tests repeatability at the nominal start, not arbitrary initial poses, disturbances or hardware robustness.

## Latest results

All three independent 0.05 m/s starts passed in 367.26–367.36 s; one 0.10 m/s trial passed in 197.43 s. The default remains 0.05 m/s and the speed parameter upper limit is 0.10 m/s. Metrics and scope: [results](../experiments/competition_lap/RESULTS.md).
