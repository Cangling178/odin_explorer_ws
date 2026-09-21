# Architecture

Target: bounded, low-speed laboratory exploration, obstacle avoidance and online mapping, followed by waypoint patrol. See [implementation status](../src/README.md).

```text
ODIN clouds/pose → selected SLAM and occupancy mapping → /map → exploration goals → Nav2
Fresh clouds → obstacle processing → Nav2 local costmap
Wheel feedback/selected estimator → continuous odometry and TF → Nav2
Nav2 / teleoperation → command arbitration → stop gate → differential controller → F4
```

Validate ODIN SLAM saving, relocalization and map quality before choosing the occupancy integration. Its map file is not an OccupancyGrid. Preserve occupied/free/unknown and ray-clearing semantics, including loop-closure consistency. Cloud-to-scan plus SLAM Toolbox is a candidate fallback; never run competing global TF authorities.

Target TF: `map → odom → base_link → odin_link → actual sensor frames`, one publisher per edge. Local odometry stays continuous; global corrections belong in map-to-odom. Align ODIN output to the chosen local odometry convention. Do not independently fuse an ODIN pose and the same IMU already used in that pose without accounting for correlation.

The retained URDF contains housing/body geometry, not calibrated device extrinsics. Simulated sensor TF was removed. Preview publishes synthetic wheel joint states and must not share them with hardware.

Use measured footprint, braking and sensor coverage. Unknown is not free; avoid blind reverse motion. Exploration needs reachable goals in known free space near frontiers, timeout, failed-goal suppression, operating boundaries and completion handling.

Start disarmed. Stale input, invalid localization, boundary violation or communication faults stop motion; restored data does not rearm. An independent F4 watchdog is required. These motion functions remain unimplemented.

Decision: laboratory exploration replaces ordered-track following. Retain the Humble candidate and separate vendor underlay; the Jetson combination still needs validation.
