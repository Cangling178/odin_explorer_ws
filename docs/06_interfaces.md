# Proposed interfaces

English | [Chinese](06_interfaces_cn.md)

These are first-party design contracts. No adapter or control node is implemented
yet, and these names are not claims about the vendor driver's current API.
Prefer standard ROS messages. Add custom messages only when branch/progress
semantics cannot be expressed unambiguously; document their version first.

| Topic | Type | Producer -> consumer | Contract |
| --- | --- | --- | --- |
| `/sensors/odin/image_raw` | sensor_msgs/msg/Image | ODIN adapter -> perception | Acquisition time, optical frame |
| `/sensors/odin/camera_info` | sensor_msgs/msg/CameraInfo | ODIN adapter -> perception | Only after valid conversion to a supported camera model |
| `/sensors/odin/imu` | sensor_msgs/msg/Imu | ODIN adapter -> selected estimator | Units and covariance audited |
| `/sensors/odin/points` | sensor_msgs/msg/PointCloud2 | ODIN adapter -> optional environment checks | Metric frame, bounded age |
| `/sensors/odin/odometry` | nav_msgs/msg/Odometry | ODIN adapter -> localization | Actual pose reference and reset semantics |
| `/wheel/odometry` | nav_msgs/msg/Odometry | hardware -> localization | Measured encoder feedback, body twist |
| `/joint_states` | sensor_msgs/msg/JointState | hardware -> model | Consistent wheel order, SI units |
| `/odometry/filtered` | nav_msgs/msg/Odometry | localization -> tracking | Continuous local pose, quality evidence |
| `/track/local_path` | nav_msgs/msg/Path | perception -> trajectory | Ordered points for selected candidate; never carries hidden branch choices |
| `/race/reference_path` | nav_msgs/msg/Path | trajectory -> controller | Frame explicit; route metadata stored separately |
| `/race/cmd_vel` | geometry_msgs/msg/TwistStamped | controller -> command selector | Body target with freshness check |
| `/teleop/cmd_vel` | geometry_msgs/msg/TwistStamped | teleop -> command selector | Selected mode only |
| `/navigation/cmd_vel` | geometry_msgs/msg/TwistStamped | navigation adapter -> selector | Convert installed Nav2 output explicitly |
| `/drive/cmd_vel` | geometry_msgs/msg/TwistStamped | stop gate -> hardware | Only final gate can publish |
| `/diagnostics` | diagnostic_msgs/msg/DiagnosticArray | components -> operator/logger | Device health; not the motor stop mechanism |

Race progress needs route ID/hash, segment ID, directed progress `s`, checkpoint
state, lateral error, heading error, confidence, validity and source timestamp.
`nav_msgs/Path` alone has no segment IDs or speed profile: the future trajectory
API must transport these separately in a defined message or synchronized contract.
See `racer_trajectory/config/route_contract.template.yaml` for the planned schema.

## Timing and QoS

Choose best-effort sensor QoS only after checking publisher compatibility;
bound queues to avoid stale image processing. Use reliable, small command queues
and explicit age checking. Reject nonfinite values, stale/future timestamps and
untrusted frame IDs. Use monotonic time for watchdog durations and ROS timestamps
for data alignment; replay uses `/clock` consistently across nodes.

Do not silently convert stamped commands to unstamped ones and lose age checks.
For a differential controller, remap to its actual scoped command topic and
configure `use_stamped_vel` explicitly. The preview has no command publisher.

## Lower-level transport

The F4 lower-level board is confirmed; Jetson-to-F4 CAN or serial transport
remains undecided. The eventual protocol
needs version, sequence number, bounded left/right wheel rad/s targets, checksum/error detection, status,
feedback, heartbeat and explicit enable state. See [protocol plan](../firmware/protocol/README.md).
