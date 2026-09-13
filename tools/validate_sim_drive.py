#!/usr/bin/env python3
"""Exercise the isolated simulation drive, compare feedback and test stopping.

Start racer_bringup simulation.launch.py in the same ROS domain first.
This sends commands only to /sim/racer/diff_drive_controller/cmd_vel.
All durations and command stamps use simulation time. No world reset is needed.
"""

import argparse
import json
import math
from pathlib import Path
import statistics
import time

import rclpy
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy
from gazebo_msgs.msg import LinkStates
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from tf2_msgs.msg import TFMessage
from rcl_interfaces.srv import GetParameters


def yaw(q):
    return math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))


def angle(value):
    return math.atan2(math.sin(value), math.cos(value))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rclpy.init()
    node = rclpy.create_node("validate_sim_drive", parameter_overrides=[Parameter("use_sim_time", value=True)])
    publisher = node.create_publisher(TwistStamped, "/sim/racer/diff_drive_controller/cmd_vel", 1)
    data, edges = {}, {}

    def truth(msg):
        if "odin_racer::base_link" in msg.name:
            i = msg.name.index("odin_racer::base_link")
            data["truth"] = (msg.pose[i], msg.twist[i])

    def tf(msg):
        for t in msg.transforms:
            edge = (t.header.frame_id, t.child_frame_id)
            edges.setdefault(edge, set()).add(t.header.frame_id)

    node.create_subscription(LinkStates, "/contact_test/link_states", truth, qos_profile_sensor_data)
    node.create_subscription(Odometry, "/sim/racer/diff_drive_controller/odom", lambda m: data.update(odom=m), 10)
    node.create_subscription(JointState, "/sim/racer/joint_states", lambda m: data.update(joints=m), qos_profile_sensor_data)
    node.create_subscription(TwistStamped, "/sim/racer/diff_drive_controller/cmd_vel_out", lambda m: data.update(limited=m), 10)
    node.create_subscription(TFMessage, "/sim/racer/tf", tf, 100)
    node.create_subscription(TFMessage, "/sim/racer/tf_static", tf,
                             QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))

    def now():
        return node.get_clock().now().nanoseconds*1e-9

    def command(v, w, stale=False):
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        if stale:
            msg.header.stamp.sec -= 1
        msg.header.frame_id = "base_link"
        msg.twist.linear.x, msg.twist.angular.z = float(v), float(w)
        publisher.publish(msg)

    def sample():
        p, tw = data["truth"]
        heading = yaw(p.orientation)
        joints = data["joints"]
        velocity = dict(zip(joints.name, joints.velocity))
        return {"t": now(), "x": p.position.x, "y": p.position.y, "z": p.position.z, "yaw": heading,
                "v": tw.linear.x*math.cos(heading)+tw.linear.y*math.sin(heading), "w": tw.angular.z,
                "odom_x": data["odom"].pose.pose.position.x, "odom_y": data["odom"].pose.pose.position.y,
                "odom_yaw": yaw(data["odom"].pose.pose.orientation),
                "left": velocity["left_wheel_joint"], "right": velocity["right_wheel_joint"],
                "max_effort": max(abs(e) for e in joints.effort),
                "limited_t": data["limited"].header.stamp.sec+data["limited"].header.stamp.nanosec*1e-9,
                "limited_v": data["limited"].twist.linear.x, "limited_w": data["limited"].twist.angular.z}

    def run(duration, v=None, w=None, stale=False):
        start, deadline, previous = now(), time.monotonic()+max(15., duration*5), -1.
        samples = []
        while now()-start < duration:
            if time.monotonic() > deadline:
                raise RuntimeError("Simulation stalled")
            rclpy.spin_once(node, timeout_sec=.01)
            if now()-previous >= .02:
                if v is not None:
                    command(v, w, stale)
                samples.append(sample())
                previous = now()
        return samples

    report = {"data_kind": "simulation", "stages": [], "checks": {}}
    all_samples = []
    try:
        deadline = time.monotonic()+30
        while len(data) < 4 or now() == 0:
            if time.monotonic() > deadline:
                raise RuntimeError("Missing clock, truth, odometry, joint state or limited-command feedback")
            rclpy.spin_once(node, timeout_sec=.1)
        client = node.create_client(GetParameters, "/sim/racer/diff_drive_controller/get_parameters")
        if not client.wait_for_service(timeout_sec=5.):
            raise RuntimeError("Controller parameters unavailable")
        request = GetParameters.Request()
        request.names = ["wheel_radius", "wheel_separation", "wheel_separation_multiplier"]
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=5.)
        if not future.done() or future.result() is None:
            raise RuntimeError("Controller parameters did not respond")
        radius, separation, multiplier = [v.double_value for v in future.result().values]
        report["wheel_geometry"] = {"radius_m": radius, "separation_m": separation, "separation_multiplier": multiplier}
        run(1., 0., 0.)
        for name, v, w in [("forward", .1, 0.), ("reverse", -.1, 0.),
                            ("left_turn", 0., .5), ("right_turn", 0., -.5),
                            ("arc", .1, .5), ("saturation", .5, 2.)]:
            begin = sample()
            moving = run(3., v, w)
            # Silence after forward explicitly tests publisher loss; other stages send zero.
            last_sent = moving[-1]["t"]
            stopped = run(1.5, None if name == "forward" else 0., None if name == "forward" else 0.)
            all_samples.extend(moving+stopped)
            end = stopped[-1]
            steady = [s for s in moving if s["t"] > moving[-1]["t"]-1.]
            expected_v, expected_w = max(-.2, min(.2, v)), max(-1., min(1., w))
            measured_v = statistics.mean(s["v"] for s in steady)
            measured_w = statistics.mean(s["w"] for s in steady)
            wheel_v = statistics.mean((s["left"]+s["right"])*radius/2 for s in steady)
            wheel_w = statistics.mean((s["right"]-s["left"])*radius/(separation*multiplier) for s in steady)
            dx, dy = end["x"]-begin["x"], end["y"]-begin["y"]
            odx, ody = end["odom_x"]-begin["odom_x"], end["odom_y"]-begin["odom_y"]
            stopped_at = next((s["t"]-last_sent for s in stopped
                               if abs(s["v"]) < .005 and abs(s["w"]) < .02
                               and abs(s["limited_v"]) < .001 and abs(s["limited_w"]) < .001), None)
            result = {"name": name, "mean_v_mps": measured_v, "mean_w_radps": measured_w,
                      "wheel_v_mps": wheel_v, "wheel_w_radps": wheel_w,
                      "travel_m": math.hypot(dx, dy), "turn_rad": angle(end["yaw"]-begin["yaw"]),
                      "odom_delta_error_m": math.hypot(dx-odx, dy-ody),
                      "odom_delta_yaw_error_rad": abs(angle(end["yaw"]-begin["yaw"]-end["odom_yaw"]+begin["odom_yaw"])),
                      "stop_after_last_motion_command_s": stopped_at,
                      "stop_travel_m": math.hypot(end["x"]-moving[-1]["x"], end["y"]-moving[-1]["y"])}
            checks = {
                "linear_tracking": abs(measured_v-expected_v) < .025,
                "angular_tracking": abs(measured_w-expected_w) < .1,
                "wheel_linear_consistency": abs(wheel_v-measured_v) < .025,
                "wheel_angular_consistency": abs(wheel_w-measured_w) < .1,
                "odom_translation": result["odom_delta_error_m"] < .04,
                "odom_rotation": result["odom_delta_yaw_error_rad"] < .15,
                "stopped": stopped_at is not None and stopped_at < 1.1,
                "remains_stopped": all(abs(s["v"]) < .005 and abs(s["w"]) < .02 for s in stopped if s["t"] > end["t"]-.3),
            }
            result["checks"] = checks
            if name == "forward":
                delay = next((s["t"]-last_sent for s in stopped if abs(s["limited_v"]) < .099), None)
                result["timeout_brake_delay_s"] = delay
                checks["timeout_brake_delay"] = delay is not None and .20 <= delay <= .35
            report["stages"].append(result)
            print(json.dumps(result), flush=True)
        stale = run(.75, .1, .5, stale=True)
        all_samples.extend(stale)
        accelerations = [(abs(b["limited_v"]-a["limited_v"])/(b["limited_t"]-a["limited_t"]),
                          abs(b["limited_w"]-a["limited_w"])/(b["limited_t"]-a["limited_t"]))
                         for a, b in zip(all_samples, all_samples[1:]) if b["limited_t"] > a["limited_t"]]
        report["max_limited_acceleration_mps2"] = max(a[0] for a in accelerations)
        report["max_limited_yaw_acceleration_radps2"] = max(a[1] for a in accelerations)
        report["checks"] = {
            "stale_commands_stop": all(abs(s["v"]) < .005 and abs(s["w"]) < .02 for s in stale),
            "linear_limit": all(abs(s["limited_v"]) <= .200001 for s in all_samples),
            "angular_limit": all(abs(s["limited_w"]) <= 1.000001 for s in all_samples),
            "linear_acceleration_limit": report["max_limited_acceleration_mps2"] <= .30001,
            "angular_acceleration_limit": report["max_limited_yaw_acceleration_radps2"] <= 1.50001,
            "effort_limit": all(s["max_effort"] <= .100001 for s in all_samples),
            "height_stable": all(.030 < s["z"] < .036 for s in all_samples),
            "tf_unique": len({child for _, child in edges}) == len(edges)
            and sorted(p.node_name for p in node.get_publishers_info_by_topic("/sim/racer/tf"))
            == ["diff_drive_controller", "robot_state_publisher"],
            "tf_complete": all(e in edges for e in [("odom", "base_link"), ("base_link", "left_wheel_link"),
                                                      ("base_link", "right_wheel_link"), ("base_link", "odin_link")]),
        }
        report["max_effort_nm"] = max(s["max_effort"] for s in all_samples)
        report["tf_edges"] = [list(edge) for edge in sorted(edges)]
        report["passed"] = all(report["checks"].values()) and all(all(s["checks"].values()) for s in report["stages"])
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
        print(json.dumps({"checks": report["checks"], "passed": report["passed"]}), flush=True)
        return 0 if report["passed"] else 1
    finally:
        for _ in range(5):
            command(0., 0.)
            rclpy.spin_once(node, timeout_sec=.02)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
