#!/usr/bin/env python3
"""Validate onboard Odin output in a fresh, isolated default motion world.

Launch simulation.launch.py gui:=false sensor_targets:=true in the same ROS domain.
Requires rendering even without a GUI. Actively drives the simulated car; no other
command publisher may run. Does not reset the world. Stops on exit.
Camera/cloud geometry checks use settled snapshots; IMU checks use moving samples.
Gazebo truth is an independent test input, never a localization output.
"""

import argparse
import json
from pathlib import Path
import time

import numpy as np
import rclpy
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from gazebo_msgs.msg import LinkStates
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import Image, CameraInfo, PointCloud2, Imu
from tf2_ros import Buffer, TransformListener, TransformException


def matrix(position, q):
    x, y, z, w = q.x, q.y, q.z, q.w
    result = np.eye(4)
    result[:3, :3] = [[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                       [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                       [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]]
    result[:3, 3] = [position.x, position.y, position.z]
    return result


def stamp(msg):
    return msg.header.stamp.sec+msg.header.stamp.nanosec*1e-9


def color_box(msg, channel):
    if msg.encoding != "rgb8":
        raise ValueError("Expected rgb8 image")
    pixels = np.frombuffer(msg.data, dtype=np.uint8).reshape(msg.height, msg.step)
    pixels = pixels[:, :msg.width*3].reshape(msg.height, msg.width, 3)[::2, ::2].astype(np.int16)
    mask = (pixels[:, :, channel] > 50)
    for other in set(range(3))-{channel}:
        mask &= pixels[:, :, channel] > 2*pixels[:, :, other]
    rows, cols = np.where(mask)
    if len(cols) < 10:
        raise ValueError("Colored sensor fixture not visible")
    return np.array([cols.min(), rows.min(), cols.max(), rows.max()], dtype=float)*2


def cloud_xyz(msg):
    fields = {f.name: f for f in msg.fields}
    if any(fields[k].datatype != 7 or fields[k].count != 1 for k in ("x", "y", "z")):
        raise ValueError("Expected FLOAT32 XYZ fields")
    dtype = np.dtype({"names": ["x", "y", "z"], "formats": [(">" if msg.is_bigendian else "<")+"f4"]*3,
                      "offsets": [fields[k].offset for k in ("x", "y", "z")], "itemsize": msg.point_step})
    array = np.ndarray((msg.height, msg.width), dtype=dtype, buffer=msg.data,
                       strides=(msg.row_step, msg.point_step))
    return np.column_stack([array[k].ravel() for k in ("x", "y", "z")])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/generated/sim_sensors_validation.json"))
    args = parser.parse_args()
    rclpy.init()
    node = rclpy.create_node("validate_sim_sensors", parameter_overrides=[Parameter("use_sim_time", value=True)],
                             cli_args=["--ros-args", "-r", "/tf:=/sim/racer/tf", "-r", "/tf_static:=/sim/racer/tf_static"])
    buffer = Buffer(node=node)
    listener = TransformListener(buffer, node)
    publisher = node.create_publisher(TwistStamped, "/sim/racer/diff_drive_controller/cmd_vel", 1)
    latest, times, frames, imu_samples = {}, {}, {}, []
    max_age, regressions = {}, {}
    report = {"data_kind": "simulation", "checks": {}, "snapshots": [], "stages": []}

    def now():
        return node.get_clock().now().nanoseconds*1e-9

    def receive(name, msg):
        t = stamp(msg)
        history = times.setdefault(name, [])
        if history and t <= history[-1]:
            regressions[name] = regressions.get(name, 0)+1
        history.append(t)
        frames.setdefault(name, set()).add(msg.header.frame_id)
        max_age[name] = max(max_age.get(name, 0.), abs(now()-t))
        latest[name] = msg
        if name == "imu" and "truth" in latest:
            pose, twist = latest["truth"]
            imu_samples.append((t, msg.angular_velocity.z, twist.angular.z,
                                msg.linear_acceleration.x, msg.linear_acceleration.z,
                                twist.linear.x, twist.linear.y))

    for name, kind in (("image", Image), ("camera_info", CameraInfo), ("cloud_raw", PointCloud2), ("imu", Imu)):
        node.create_subscription(kind, "/sim/racer/odin1/"+name,
                                 lambda msg, key=name: receive(key, msg),
                                 5 if name in ("image", "camera_info") else qos_profile_sensor_data)

    def truth(msg):
        if "odin_racer::base_link" in msg.name:
            i = msg.name.index("odin_racer::base_link")
            latest["truth"] = (msg.pose[i], msg.twist[i])

    node.create_subscription(LinkStates, "/contact_test/link_states", truth, qos_profile_sensor_data)

    def command(v=0., w=0.):
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        msg.twist.linear.x, msg.twist.angular.z = float(v), float(w)
        publisher.publish(msg)

    def run(duration, v=0., w=0.):
        start, wall, last = now(), time.monotonic(), -1.
        while now()-start < duration:
            if time.monotonic()-wall > max(30., duration*15):
                raise RuntimeError("Simulation stalled or too slow for this validator")
            rclpy.spin_once(node, timeout_sec=.005)
            if now()-last >= .02:
                command(v, w)
                last = now()
        return [s for s in imu_samples if start <= s[0] <= now()]

    def snapshot(name):
        p, tw = latest["truth"]
        if np.linalg.norm([tw.linear.x, tw.linear.y, tw.linear.z]) > .005 or abs(tw.angular.z) > .02:
            raise ValueError("Geometry snapshots require a stopped car")
        world_from_base = matrix(p.position, p.orientation)
        def world_from_sensor(msg):
            tf = buffer.lookup_transform("base_link", msg.header.frame_id, Time.from_msg(msg.header.stamp)).transform
            # Also require the dynamic odom chain at the acquisition timestamp.
            buffer.lookup_transform("odom", msg.header.frame_id, Time.from_msg(msg.header.stamp))
            return world_from_base @ matrix(tf.translation, tf.rotation)
        image, info, cloud = (latest[k] for k in ("image", "camera_info", "cloud_raw"))
        if max(now()-stamp(m) for m in (image, info, cloud, latest["imu"])) > .3:
            raise ValueError("Stale sensor snapshot")
        camera_from_world = np.linalg.inv(world_from_sensor(image))
        k = np.array(info.k).reshape(3, 3)
        def projected_box(xs, ys, zs, clip_marker=False):
            corners = np.array([[x, y, z, 1.] for x in xs for y in ys for z in zs])
            optical = (camera_from_world @ corners.T).T[:, :3]
            if np.any(optical[:, 2] <= 0):
                raise ValueError("Fixture behind the camera")
            uv = (k @ optical.T).T
            uv = uv[:, :2]/uv[:, 2:]
            if clip_marker:
                # Clip the planar marker polygon at image edges. A turn can make
                # part of the marker leave the FOV without invalidating projection.
                center = uv.mean(axis=0)
                uv = uv[np.argsort(np.arctan2(uv[:, 1]-center[1], uv[:, 0]-center[0]))]
                for axis, boundary, sign in ((0, 0., 1), (0, image.width-1., -1),
                                              (1, 0., 1), (1, image.height-1., -1)):
                    clipped = []
                    for a, b in zip(uv, np.roll(uv, -1, axis=0)):
                        a_in, b_in = sign*(a[axis]-boundary) >= 0, sign*(b[axis]-boundary) >= 0
                        if a_in:
                            clipped.append(a)
                        if a_in != b_in:
                            clipped.append(a+(b-a)*(boundary-a[axis])/(b[axis]-a[axis]))
                    if not clipped:
                        raise ValueError("Ground marker outside camera FOV")
                    uv = np.array(clipped)
            return np.r_[uv.min(axis=0), uv.max(axis=0)]
        red, blue = color_box(image, 0), color_box(image, 2)
        target_error = float(np.max(np.abs(red-projected_box([1.95, 2.05], [-.15, .15], [0., .4]))))
        marker_error = float(np.max(np.abs(blue-projected_box([.65, .95], [-.06, .06], [.0015], clip_marker=True))))
        points = cloud_xyz(cloud)
        if not np.isfinite(points).all():
            raise ValueError("Nonfinite points should have been filtered by the ray plugin")
        lidar_pose = world_from_sensor(cloud)
        world_points = points @ lidar_pose[:3, :3].T+lidar_pose[:3, 3]
        mask = ((world_points[:, 0] > 1.90) & (world_points[:, 0] < 2.10)
                & (np.abs(world_points[:, 1]) < .18) & (world_points[:, 2] > .04) & (world_points[:, 2] < .42))
        target = world_points[mask]
        if len(target) < 10:
            raise ValueError("Too few point-cloud returns on the known target")
        face_error = np.min(np.abs(target[:, :, None]-np.array([[1.95, 2.05], [-.15, .15], [0., .4]])[None, :, :]), axis=(1, 2))
        plane_mask = (world_points[:, 0] > .4) & (world_points[:, 0] < 1.5) & (np.abs(world_points[:, 1]) < .4)
        ground = world_points[plane_mask, 2]
        ground_error = float(np.percentile(np.abs(ground), 95)) if len(ground) else 1.
        checks = {
            "camera_projection": target_error < 8., "ground_marker_visible": marker_error < 8.,
            "cloud_target_geometry": float(np.percentile(face_error, 95)) < .02,
            "cloud_ground_plane": ground_error < .01,
            "image_info_agree": image.width == info.width == 1600 and image.height == info.height == 1296
            and abs(stamp(image)-stamp(info)) < .11 and info.distortion_model == "plumb_bob"
            and np.allclose(info.d, 0.) and abs(k[0, 0]-381.58275109) < .01,
        }
        result = {"name": name, "base_xyz_m": [p.position.x, p.position.y, p.position.z],
                  "red_box_px": red.tolist(), "blue_box_px": blue.tolist(),
                  "target_projection_max_error_px": target_error, "marker_projection_max_error_px": marker_error,
                  "cloud_target_points": len(target), "cloud_target_p95_error_m": float(np.percentile(face_error, 95)),
                  "cloud_ground_p95_error_m": ground_error, "checks": {k: bool(v) for k, v in checks.items()}}
        report["snapshots"].append(result)
        print(json.dumps(result), flush=True)

    try:
        deadline = time.monotonic()+45
        while len(latest) < 5 or now() == 0:
            if time.monotonic() > deadline:
                raise RuntimeError("Missing onboard sensors, clock or Gazebo truth; check rendering and launch options")
            rclpy.spin_once(node, timeout_sec=.1)
        if np.linalg.norm([latest["truth"][0].position.x, latest["truth"][0].position.y]) > .05:
            raise ValueError("Start this validator in a fresh world at the default origin")
        run(1.5)
        wall_start, sim_start = time.monotonic(), now()
        times.clear()
        max_age.clear()
        regressions.clear()
        snapshot("stationary")
        for name, v, w in (("forward", .1, 0.), ("left_turn", 0., .25), ("right_turn", 0., -.25)):
            moving = np.array(run(2., v, w))
            steady = moving[moving[:, 0] > moving[-1, 0]-.8]
            braking = np.array(run(1.5))
            yaw_error = float(np.mean(np.abs(steady[:, 1]-steady[:, 2])))
            checks = {"imu_yaw_matches_truth": yaw_error < .03,
                      "commanded_turn_seen": abs(float(np.mean(steady[:, 1]))-w) < .05}
            if name == "forward":
                checks.update(acceleration_seen=float(np.percentile(moving[moving[:, 0] < moving[0, 0]+.5, 3], 90)) > .1,
                              braking_seen=float(np.percentile(braking[braking[:, 0] < braking[0, 0]+.5, 3], 10)) < -.1,
                              steady_acceleration_small=abs(float(np.mean(steady[:, 3]))) < .05)
            result = {"name": name, "imu_mean_yaw_radps": float(np.mean(steady[:, 1])),
                      "truth_mean_yaw_radps": float(np.mean(steady[:, 2])), "imu_yaw_mae_radps": yaw_error,
                      "steady_mean_accel_x_mps2": float(np.mean(steady[:, 3])), "checks": checks}
            report["stages"].append(result)
            print(json.dumps(result), flush=True)
            snapshot("after_"+name)
        rates = {k: (len(ts)-1)/(ts[-1]-ts[0]) for k, ts in times.items() if len(ts) > 1}
        publishers = {k: len(node.get_publishers_info_by_topic("/sim/racer/odin1/"+k)) for k in times}
        imu = latest["imu"]
        report["checks"] = {
            "sensor_publishers_unique": len(publishers) == 4 and all(n == 1 for n in publishers.values()),
            "tf_publishers": sorted(p.node_name for p in node.get_publishers_info_by_topic("/sim/racer/tf"))
            == ["diff_drive_controller", "robot_state_publisher"]
            and [p.node_name for p in node.get_publishers_info_by_topic("/sim/racer/tf_static")] == ["robot_state_publisher"],
            "frame_ids": frames == {"image": {"odin_sim_camera_optical"}, "camera_info": {"odin_sim_camera_optical"},
                                     "cloud_raw": {"odin_sim_lidar"}, "imu": {"odin_sim_imu"}},
            "timestamps_increase": not regressions,
            "fresh_sim_time": len(max_age) == 4 and max(max_age.values()) < .5,
            "rates": len(rates) == 4 and all(.8*expected < rates.get(k, 0) < 1.15*expected
                         for k, expected in (("image", 10), ("camera_info", 10), ("cloud_raw", 10), ("imu", 400))),
            "stationary_gravity": abs(imu.linear_acceleration.z-9.81) < .1 and abs(imu.linear_acceleration.x) < .05,
            "translation_exercised": report["snapshots"][1]["base_xyz_m"][0]-report["snapshots"][0]["base_xyz_m"][0] > .15,
            "image_turn_response": report["snapshots"][2]["red_box_px"][0]-report["snapshots"][1]["red_box_px"][0] > 80.,
        }
        report.update(received_rates_per_sim_second=rates, max_message_age_sim_s=max_age,
                      real_time_factor=(now()-sim_start)/(time.monotonic()-wall_start))
        report["passed"] = all(report["checks"].values()) and all(all(x["checks"].values()) for x in report["stages"]+report["snapshots"])
    except (RuntimeError, ValueError, TransformException) as exc:
        report.update(passed=False, error=str(exc))
    finally:
        for _ in range(5):
            command()
            rclpy.spin_once(node, timeout_sec=.02)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
        node.destroy_node()
        rclpy.shutdown()
    print(json.dumps(report), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
