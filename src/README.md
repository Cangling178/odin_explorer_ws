# Source guide

English | [简体中文](README_cn.md)

First-party code lives under `src/odin_explorer/`. There are six ROS 2 packages; only model/preview functionality is implemented. The other packages retain development contracts.

| Package | Responsibility | Current implementation |
| --- | --- | --- |
| `explorer_description` | Body, wheel, motor and ODIN housing geometry and frames | Xacro, STL, RViz configuration and preview launch |
| `explorer_bringup` | Module composition, operating modes and launch order | Only `preview.launch.py`; no actuator or sensor connection |
| `explorer_hardware` | Host-to-F4 transport, wheel feedback and differential base interface | Contract templates; no transport or hardware plugin |
| `explorer_odin` | Vendor cloud/pose, clock and TF adaptation | Contract templates; actual driver lives in the vendor underlay |
| `explorer_localization` | Continuous odometry, global localization and occupancy integration | Contract templates; no estimator or occupancy mapper |
| `explorer_navigation` | Nav2 obstacle avoidance, exploration goals and waypoint patrol | Contract templates; no navigation launch |

Each package declares ROS dependencies in `package.xml`, installs resources with `CMakeLists.txt`, and stores configuration or contracts in `config/`. Implemented launches live in `launch/`; only description has `urdf/` and `meshes/`. `*.template.yaml` files are not runtime parameters.

`explorer_hardware` runs on the host. Root-level `firmware/` is reserved for F4 code and currently contains protocol notes only. The host performs differential kinematics; F4 will own wheel loops and an independent command watchdog. These functions remain unimplemented.

`vendor_ws/src/odin_ros_driver/` is an independent vendor repository. It is excluded from the first-party colcon build and the parent Git push. After cloning, fetch the pinned source and build it separately using the [vendor instructions](../vendor_ws/README.md).

Model dimensions and inertia include assumptions. Real mounting extrinsics require measurement. Preview publishes synthetic wheel joint states, not real base feedback.

[Project structure](../README.md#project-structure) · [Architecture and data flow](../docs/02_architecture.md) · [Development](../docs/07_development.md)
