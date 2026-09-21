# Interface contracts

These are proposed integration interfaces, not implemented hardware adapters or guaranteed vendor topic names.

| Interface | Type | Producer → consumer |
| --- | --- | --- |
| `/sensors/odin/points` | sensor_msgs/PointCloud2 | ODIN adapter → mapping, obstacles |
| `/sensors/odin/odometry` | nav_msgs/Odometry | ODIN adapter → selected localization |
| `/wheel/odometry` | nav_msgs/Odometry | wheel estimation → localization |
| `/joint_states` | sensor_msgs/JointState | real wheel feedback → model |
| `/odometry/filtered` | nav_msgs/Odometry | continuous local state → navigation |
| `/map` | nav_msgs/OccupancyGrid | mapping → exploration, Nav2 |
| `NavigateToPose` action | nav2_msgs/action/NavigateToPose | exploration → Nav2; namespace TBD |
| `/navigation/cmd_vel` | geometry_msgs/TwistStamped | navigation adapter → arbitration |
| `/teleop/cmd_vel` | geometry_msgs/TwistStamped | teleoperation → arbitration |
| `/drive/cmd_vel` | geometry_msgs/TwistStamped | final stop gate → differential controller |
| `/diagnostics` | diagnostic_msgs/DiagnosticArray | components → logs/operator |

Only the final command gate publishes drive commands; remap to the installed controller's actual subscription. Verify the locked Nav2 output type and adapt if necessary. Preserve freshness; never restamp expired commands. SI units; wheel commands in rad/s.

Query TF at acquisition time. Verify QoS, clock mapping, age and reset behavior. Late map subscribers need a complete map. Record map origin changes. Clouds do not establish free space outside sensor coverage.

See [F4 contract](../firmware/README.md). The host performs differential kinematics; F4 owns wheel control and its independent watchdog. Rates, timeouts, covariance and TF ownership need hardware validation.
