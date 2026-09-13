#!/usr/bin/env python3
"""Observe the dedicated contact world; optionally reset that test simulation.

Use the same ROS_DOMAIN_ID as ground_contact.launch.py. No drive commands are sent.
--reset invokes /reset_simulation and must only be used in an isolated test world.
"""

import argparse
import json
import math
from pathlib import Path
import time

import rclpy
from gazebo_msgs.srv import GetEntityState
from std_srvs.srv import Empty


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rclpy.init()
    node = rclpy.create_node("validate_ground_contact")

    def call(client, request):
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=5.)
        if not future.done() or future.result() is None:
            raise RuntimeError("Simulation service did not respond")
        return future.result()

    try:
        client = node.create_client(GetEntityState, "/contact_test/get_entity_state")
        if not client.wait_for_service(timeout_sec=15.):
            raise RuntimeError("Start the dedicated contact world first")
        if args.reset:
            reset = node.create_client(Empty, "/reset_simulation")
            if not reset.wait_for_service(timeout_sec=5.):
                raise RuntimeError("Reset service unavailable")
            call(reset, Empty.Request())
        request = GetEntityState.Request()
        request.name = "odin_racer::base_link"
        request.reference_frame = "world"
        samples = []
        deadline = time.monotonic()+45.
        while time.monotonic() < deadline:
            response = call(client, request)
            if not response.success:
                raise RuntimeError("Dynamic base_link missing")
            stamp = response.header.stamp
            t = stamp.sec+stamp.nanosec*1e-9
            state = response.state
            p, q, v, w = state.pose.position, state.pose.orientation, state.twist.linear, state.twist.angular
            sample = [t, p.x, p.y, p.z, math.sqrt(v.x*v.x+v.y*v.y+v.z*v.z),
                      math.sqrt(w.x*w.x+w.y*w.y+w.z*w.z),
                      math.degrees(2*math.acos(min(1., abs(q.w))))]
            if not all(math.isfinite(value) for value in sample):
                raise RuntimeError("Non-finite simulation state")
            if samples and t < samples[-1][0]:
                raise RuntimeError("Simulation time reset during observation")
            if not samples or t > samples[-1][0]:
                samples.append(sample)
            if samples[-1][0]-samples[0][0] >= 10.:
                break
            time.sleep(.05)
        if len(samples) < 2 or samples[-1][0]-samples[0][0] < 10.:
            raise RuntimeError("Simulation did not advance 10 seconds within 45 seconds")
        settled = [s for s in samples if s[0]-samples[0][0] >= 5.]
        z = [s[3] for s in settled]
        metrics = {
            "data_kind": "simulation", "reset_before_observation": args.reset,
            "observation_sim_s": samples[-1][0]-samples[0][0], "sample_count": len(samples),
            "initial_base_z_m": samples[0][3], "final_base_z_m": samples[-1][3],
            "settled_z_span_m": max(z)-min(z),
            "settled_xy_drift_m": max(math.hypot(s[1]-settled[0][1], s[2]-settled[0][2]) for s in settled),
            "settled_max_linear_speed_mps": max(s[4] for s in settled),
            "settled_max_angular_speed_radps": max(s[5] for s in settled),
            "settled_max_orientation_angle_deg": max(s[6] for s in settled),
        }
        checks = {
            "settled_height": all(abs(s[3]-.03325) < .001 for s in settled),
            "no_sinking": min(s[3] for s in samples) > .03125,
            "vertical_stability": metrics["settled_z_span_m"] < .0005,
            "horizontal_stability": metrics["settled_xy_drift_m"] < .001,
            "linear_speed": metrics["settled_max_linear_speed_mps"] < .005,
            "angular_speed": metrics["settled_max_angular_speed_radps"] < .02,
            "orientation": metrics["settled_max_orientation_angle_deg"] < .5,
        }
        if args.reset:
            checks["release_height"] = abs(metrics["initial_base_z_m"]-.05325) < .005
        metrics["checks"] = checks
        metrics["passed"] = all(checks.values())
        output = json.dumps(metrics, indent=2, allow_nan=False)+"\n"
        print(output, end="")
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output)
        return 0 if metrics["passed"] else 1
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
