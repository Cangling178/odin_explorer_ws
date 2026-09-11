# Course tracking and speed strategy

English | [Chinese](05_course_strategy_cn.md)

## What the image establishes

See [reference](../tracks/reference/README.md). The annotated board dimensions
are 2.00 x 1.50 m; the red course extents are 1.61 x 1.20 m. There is a central
crossing, several tight turns and a lower sequence of S-bends. The image has
cropping and unknown print/capture scaling. No driveable coordinates have been
generated from it. Confirm line width, route direction and start/finish physically.

## Selected sensing mode

The owner instructed us to treat prior mapping, preloaded routes and camera
line recognition as allowed. Use a surveyed or taught ordered route as the
reference, local RGB line observations as error feedback, and wheel/ODIN1 motion
as context. Ground visibility still needs a physical test. Start/finish, direction,
judged point and allowed error are not yet defined.

A localization-only system cannot be assumed to match the line closely enough.
Keep it as a measured diagnostic baseline, not an automatic substitute for local
visual feedback. ODIN1 drift, alignment and control errors accumulate; the small
flat board can also provide limited localization features.

## Perception pipeline, planned

Acquire RGB -> validate age -> apply the correct camera model -> select a ground
region -> separate black line from background -> reject shadows and printed
annotations -> extract candidate centerlines -> project to metric ground points.
Begin with explainable classical image processing and save intermediate debug
images. Add more complex models only if recorded failures justify them.

Output multiple branches near the crossing. Confidence should reflect visible
length, segmentation quality, reprojection checks and ambiguity. A blank image
must produce invalid status, not a zero cross-track error. Keep observation
timestamps even when predicting the robot state to the current control time.

## Route topology and crossing association

A point cloud or unordered set of nearest line pixels is not a route. Represent
the course with ordered segments, travel direction, cumulative distance `s`,
crossing entry/exit identities and start/finish gates. Survey samples contain
segment IDs even when two points share the same world coordinates.

Constrain each association to a progress window around the previous segment,
then check heading continuity, plausible traveled distance and allowed next
edges. At a crossing, do not select a branch using global nearest Euclidean
distance alone. Maintain hysteresis and only advance on evidence of the expected
exit. Count laps with ordered checkpoint traversal plus a directed finish gate;
spatial proximity to the start is insufficient.

Replay tests must include both traversals through the crossing, a pause at the
intersection, temporary line loss, pose jumps and deliberate wrong-branch entry.
Race mode must not let a shortest-path planner bypass loops to reach a goal.

## Tight turns and physical feasibility

An ideal drawing corner has discontinuous heading. A moving robot cannot track
that corner at finite speed with bounded angular velocity and acceleration.
Measure allowed lateral deviation and swept footprint before smoothing. A pivot
may be feasible for this rear differential-drive robot if rules allow stopping. Check passive caster
realignment and the front overhang sweep during a pivot. Never smooth away a required loop
or cut a corner beyond the allowed corridor to improve lap time.

## Control progression

1. Close the wheel-speed loop and calibrate geometry using slow straight/turn trials.
2. Follow a simple measured line with low-speed pure pursuit or a comparable baseline.
3. Add heading/error feedback, limited lookahead and progress-aware path selection.
4. Demonstrate the crossing and every tight bend at low speed.
5. Add curvature-aware speed planning and measured braking limits.
6. Compare a more advanced controller, such as MPC, only against the same dataset
   and validated baseline. Nav2 Regulated Pure Pursuit is a reference candidate,
   but its installed-version behavior on self-intersections must be tested.

## Speed profile, proposed equations

For nonzero curvature `kappa`, candidate limits include:

```text
v_curve <= sqrt(a_lateral_max / abs(kappa))
v_yaw   <= omega_max / abs(kappa)
v_next^2 <= v_current^2 + 2 * a_accel * ds
v_current^2 <= v_next^2 + 2 * a_brake * ds
d_stop >= v * total_latency + v^2 / (2 * a_brake) + margin
```

Use separate acceleration and deceleration magnitudes and forward/backward
passes over the route. Also constrain wheel speed, steering limits, footprint,
available lookahead and observation confidence. Handle near-zero curvature
without division by zero. These equations are design bounds, not calibrated limits.

At 0.5 m/s, 100 ms of latency consumes 0.05 m before braking starts. This simple
distance example explains why camera timing matters on this small board; it is
not a recommended vehicle speed. Reduce speed before a tight bend, not after
large error appears. Increase one speed parameter at a time and repeat trials.

## Accuracy budget

Separate survey/ground-truth error, camera projection error, sensor-to-body
extrinsic error, timestamp error, localization drift and tracking error. Do not
report estimator self-consistency as absolute track accuracy. Benchmark both
whole-route and per-segment results to expose fast straights hiding poor bends.
