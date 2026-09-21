# ODIN1 vendor underlay

English | [Chinese](README_cn.md)

Documentation consolidated 2026-09-21; the 2026-09-11 import/build record below is retained. No driver upgrade or new firmware/device acceptance was performed.

The local checkout contains `src/odin_ros_driver` cloned from the vendor repository. Vendor sources,
SDK binaries and underlay build products are ignored in the parent Git repository.
`COLCON_IGNORE` prevents accidental root-level discovery. The first-party build
uses `--base-paths src` at the root, not this directory.

Before importing: check the exact release/firmware pair and review the build
script. Keep the vendor package directly under this underlay's `src/` directory
because the vendor documents layout assumptions. Use the audited vendor build
procedure within this directory; the first-party foundation does not invoke it.

The imported commit, license, SDK provenance, local build and initial point cloud
check are recorded below; device firmware and target-platform acceptance remain pending.
Source this underlay before the first-party overlay. See
[ODIN1 integration](../docs/09_bringup.md) for acceptance.
This clone contains an independent vendor source copy. The old vendor_ws/install was not migrated; rebuild here using the commands below. The first-party build does not download, build or install this underlay.

## Source import record — 2026-09-11

- Upstream: https://github.com/manifoldsdk/odin_ros_driver.git
- Branch at import: `main`; driver version: `v0.14.4`.
- Imported commit: `f51051f2d861f7643d4d33d2ade2952efe1a4672`.
- Repository license: Apache-2.0; upstream `LICENSE` retained.
- SDK provenance: `lib/liblydHostApi_amd.a` and `lib/liblydHostApi_arm.a` from the same upstream commit.
- Upstream-required firmware: `v0.14.0`; actual device firmware has not been checked.
- No source patches were applied during import. The vendor build script was not run. See the local build and test record below.
- This records the downloaded revision, not an accepted platform/firmware lock.

Build review note: `script/build_ros2.sh` references undefined `WS_DIR` and runs
`rm -rf build install log`. Resolve the build procedure before executing it.

## Historical source-project build and initial test — 2026-09-11

Ubuntu 22.04 / ROS 2 Humble on the development laptop. The user reported a
successful build (`1 package finished`) and confirmed point cloud display in
RViz. USB enumeration showed `2207:0019` at `5000M`. This is an initial point
cloud check; image, IMU, odometry quality and vehicle integration remain unvalidated.
Actual firmware remains unconfirmed. This is not Jetson platform acceptance.

Build from the project root:

```bash
cd /home/cangling/odin_explorer_ws
source /opt/ros/humble/setup.bash
CMAKE_BUILD_PARALLEL_LEVEL=2 colcon --log-base vendor_ws/log build \
  --base-paths vendor_ws/src \
  --build-base vendor_ws/build \
  --install-base vendor_ws/install \
  --packages-select odin_ros_driver \
  --executor sequential \
  --cmake-args -DBUILD_SYSTEM=ROS2
```

For subsequent runs, source the environment and launch; rebuilding is unnecessary
unless source or installed resources change:

```bash
source /opt/ros/humble/setup.bash
source /home/cangling/odin_explorer_ws/vendor_ws/install/setup.bash
ros2 launch odin_ros_driver odin1_ros2.launch.py
```

The build does not use `--symlink-install`. Rebuild after editing source YAML or
launch files to update installed copies. The launch `config_file` argument can
instead select a YAML directly for the main driver; auxiliary nodes still read
the installed default configuration. Vendor source and build outputs remain
ignored and must be obtained separately when cloning the parent repository.

## Fetch vendor sources after cloning

This machine already has an independent copy. Run once after cloning the parent on another machine; inspect an existing checkout instead of overwriting it.

```bash
# From the odin_explorer_ws root
mkdir -p vendor_ws/src
git clone https://github.com/manifoldsdk/odin_ros_driver.git vendor_ws/src/odin_ros_driver
git -C vendor_ws/src/odin_ros_driver checkout --detach f51051f2d861f7643d4d33d2ade2952efe1a4672
```

The official navigation stack and its ROS1 driver copy live in `third_party/Odin-Nav-Stack`; see [integration](../third_party/README.md). This underlay retains the independent ROS2 driver. Do not connect both copies to the same device simultaneously.
