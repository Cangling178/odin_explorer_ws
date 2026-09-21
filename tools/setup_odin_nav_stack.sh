#!/usr/bin/env bash
# Fetch pinned upstream sources and apply the documented ROS1-only integration.
# Does not install packages, build containers, start ROS or connect actuators.
set -euo pipefail
root_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
stack_dir="$root_dir/third_party/Odin-Nav-Stack"
driver_dir="$stack_dir/ros_ws/src/odin_ros_driver"
patch_file="$root_dir/third_party/patches/odin_driver_ros1_navigation.patch"
stack_rev=e6a28acef044bad8aa5daaef3a8f4b07904ca85b
driver_rev=f51051f2d861f7643d4d33d2ade2952efe1a4672

git -C "$root_dir" submodule update --init third_party/Odin-Nav-Stack
[[ "$(git -C "$stack_dir" rev-parse HEAD)" == "$stack_rev" ]] || { echo 'Unexpected navigation stack revision' >&2; exit 1; }
# Upstream NeuPAN uses an SSH URL. HTTPS works without a GitHub SSH key.
git -C "$stack_dir" -c url.https://github.com/.insteadOf=git@github.com: \
  submodule update --init --depth 1 NeuPAN yolov5
if [[ ! -e "$driver_dir/.git" ]]; then
  git -C "$stack_dir" submodule update --init --depth 1 ros_ws/src/odin_ros_driver
fi
if [[ "$(git -C "$driver_dir" rev-parse HEAD)" != "$driver_rev" ]]; then
  if [[ -n "$(git -C "$driver_dir" status --porcelain)" ]]; then
    echo 'Driver has local edits; preserve them and resolve the revision manually.' >&2
    exit 1
  fi
  git -C "$driver_dir" fetch --depth 1 origin "$driver_rev"
  git -C "$driver_dir" checkout --detach "$driver_rev"
fi
if git -C "$driver_dir" apply --reverse --check "$patch_file" 2>/dev/null; then
  echo 'Navigation driver patch already applied.'
else
  git -C "$driver_dir" apply --check "$patch_file"
  git -C "$driver_dir" apply "$patch_file"
fi
# Official first-run Docker layout; preserve any existing local configuration.
mkdir -p "$stack_dir/docker/configs" "$stack_dir/docker/maps/grid" \
  "$stack_dir/docker/maps/relocalization" "$stack_dir/docker/maps/pcd"
for relative in ros_ws/src/odin_ros_driver/config/control_command.yaml \
  NeuPAN/neupan/ros/configs/config.yaml NeuPAN/neupan/ros/configs/planner.yaml \
  ros_ws/src/map_planner/launch/whole.launch; do
  destination="$stack_dir/docker/configs/$(basename "$relative")"
  if [[ ! -e "$destination" ]]; then
    cp -- "$stack_dir/$relative" "$destination"
    if [[ "$relative" == ros_ws/src/odin_ros_driver/config/control_command.yaml ]]; then
      sed -i 's|^  mapping_result_dest_dir:.*|  mapping_result_dest_dir: "/opt/odin/maps/relocalization"|' "$destination"
    fi
  fi
done
printf '%s\n' 'Sources and official config copies prepared. ROS1/Jetson runtime and F4 adaptation remain unvalidated.'
