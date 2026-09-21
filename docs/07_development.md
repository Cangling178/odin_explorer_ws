# Development and minimal checks

## Clone the project

This is a public repository and can be cloned directly over HTTPS. The main branch is `main`.

```bash
git clone https://github.com/Cangling178/odin_explorer_ws.git
cd odin_explorer_ws
```

See [project structure](../README.md#project-structure) and [source guide](../src/README.md). Local commands below assume `/home/cangling/odin_explorer_ws`; use your own clone path on other machines.

## Build and check

Development baseline: Ubuntu 22.04 / ROS 2 Humble; Jetson image still unvalidated. Use a fresh terminal without the original project's install overlay.

First-party dependencies: ament_cmake, colcon, xacro, launch, launch_ros, ament_index_python, robot_state_publisher, joint_state_publisher and rviz2. No Gazebo, OpenCV or custom message generation.

```bash
cd /home/cangling/odin_explorer_ws
source /opt/ros/humble/setup.bash
rosdep install --from-paths src --ignore-src -r -y
colcon build --base-paths src --symlink-install
source install/local_setup.bash
python3 tools/check_workspace.py
ros2 launch explorer_bringup preview.launch.py rviz:=false
```

Initialize rosdep beforehand. Ctrl+C exits preview. The check covers package dependencies, document links, Python syntax and expanded model meshes/TF tree, not hardware behavior.

Old competition tests, world generation and repeated-lap tools were removed. Add protocol failure, watchdog, timing/TF and navigation behavior tests only as real functions are implemented. Do not test empty placeholders.

See [vendor build](../vendor_ws/README.md). Build outputs, maps and bags are local ignored data.

## Where changes belong

- Host functions belong in the appropriate `explorer_*` package; launch composition belongs in `explorer_bringup/launch/`.
- F4 firmware belongs in `firmware/`; wiring, measured parameters and extrinsics belong in `hardware/`.
- Create `data/bags/` and `data/maps/` as needed for raw captures and maps; commit reviewable summaries in documentation.
- Keep vendor sources separately versioned; do not commit SDK binaries or vendor build outputs to the parent repository.
- Update Chinese and English documentation together; add focused validation as actual motion functions are implemented.

Model preview is the only runnable entry point. Successful builds do not establish base, localization or navigation acceptance.

## Official navigation stack

Follow [integration instructions](../third_party/README.md) and run `bash tools/setup_odin_nav_stack.sh`. This only prepares isolated ROS1 sources, patch and configuration, without installing runtimes or starting motion. Build it separately from the ROS2 packages.
