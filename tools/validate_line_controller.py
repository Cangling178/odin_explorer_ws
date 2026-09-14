#!/usr/bin/env python3
"""Exercise the installed C++ controller with synthetic ROS inputs, no actuators."""
import argparse
import copy
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from collections import deque

import rclpy
from geometry_msgs.msg import PoseStamped, TransformStamped, TwistStamped
from nav_msgs.msg import Odometry, Path as RosPath
from racer_interfaces.msg import LineObservation
from std_msgs.msg import String
from std_srvs.srv import SetBool
from tf2_ros import TransformBroadcaster
from rclpy.qos import QoSProfile, DurabilityPolicy


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--domain', type=int, default=92)
    args = parser.parse_args()
    os.environ['ROS_DOMAIN_ID'] = str(args.domain)
    output = Path('data/generated/line_controller_validation.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    log = output.with_suffix('.log').open('w')
    process = subprocess.Popen(['ros2','run','racer_control','line_controller','--ros-args','-r',
                                '__ns:=/validation','-r','/tf:=/validation/tf','-r',
                                '/tf_static:=/validation/tf_static'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    rclpy.init()
    node = rclpy.create_node('controller_test',cli_args=['--ros-args','-r','/tf:=/validation/tf'])
    tf = TransformBroadcaster(node)
    odom_pub = node.create_publisher(Odometry,'/validation/odom',1)
    path_pub = node.create_publisher(LineObservation,'/validation/observation',1)
    latest={}
    node.create_subscription(TwistStamped,'/validation/cmd_vel',lambda m:latest.update(command=m),1)
    node.create_subscription(String,'/validation/tracking_status',lambda m:latest.update(state=m.data),
                             QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))
    client=node.create_client(SetBool,'/validation/line_controller/enable')
    last=0.
    mode='normal'
    tf_history=deque()
    report={'data_kind':'synthetic_ros_inputs','checks':{}}
    def step():
        nonlocal last
        rclpy.spin_once(node,timeout_sec=.003)
        if time.monotonic()-last<.04:
            return
        last=time.monotonic()
        stamp=node.get_clock().now().to_msg()
        transform=TransformStamped(); transform.header.stamp=stamp
        transform.header.frame_id='odom'; transform.child_frame_id='base_link'; transform.transform.rotation.w=1.
        tf_history.append((time.monotonic(),copy.deepcopy(transform)))
        delayed=None
        while tf_history and time.monotonic()-tf_history[0][0]>=.12:
            delayed=tf_history.popleft()[1]
        if mode=='lagged_tf':
            if delayed is not None:tf.sendTransform(delayed)
        elif mode!='missing_tf':
            tf.sendTransform(transform)
        odom=Odometry(); odom.header=copy.deepcopy(transform.header); odom.child_frame_id='base_link'; odom.pose.pose.orientation.w=1.
        if mode=='future_odom':
            odom.header.stamp.sec+=2
        if mode=='stale_odom':
            odom.header.stamp.sec-=2
        if mode=='malformed_odom':
            odom.pose.pose.position.x=float('nan')
        if mode!='missing_odom':
            odom_pub.publish(odom)
        path=RosPath(); path.header.stamp=stamp; path.header.frame_id='base_link'
        if mode=='duplicate_path':
            path.header.stamp=copy.deepcopy(latest.setdefault('frozen_stamp',copy.deepcopy(stamp)))
        if mode=='future':
            path.header.stamp.sec+=2
        if mode=='stale':
            path.header.stamp.sec-=2
        if mode=='wrong_frame':
            path.header.frame_id='camera'
        if mode!='empty':
            for x in (.2,.3,.4,.5,.6,.7):
                pose=PoseStamped(); pose.header=path.header; pose.pose.position.x=x
                pose.pose.position.y=.03; pose.pose.orientation.w=1.
                path.poses.append(pose)
        if mode=='nan':
            path.poses[2].pose.position.y=float('nan')
        if mode!='missing_path':
            observation=LineObservation();observation.path=path
            observation.image_valid=mode!='empty';observation.path_valid=bool(path.poses)
            observation.confidence=1.;observation.exits=1;observation.reason=mode
            path_pub.publish(observation)
    def wait(condition,timeout=8):
        end=time.monotonic()+timeout
        while not condition():
            if process.poll() is not None or time.monotonic()>end:
                raise RuntimeError('Timeout: '+str(latest.get('state')))
            step()
    def run(duration):
        end=time.monotonic()+duration
        while time.monotonic()<end:
            step()
    def enable(value):
        wait(client.service_is_ready)
        req=SetBool.Request(); req.data=value
        future=client.call_async(req); wait(future.done)
        if not future.result().success:
            raise RuntimeError(future.result().message)
    try:
        wait(lambda:latest.get('state')=='READY' and 'command' in latest)
        report['checks']['no_automatic_motion']=latest['command'].twist.linear.x==0
        enable(True); run(.2)
        bad=Odometry(); bad.header.frame_id='odom'; bad.child_frame_id='base_link'
        bad.header.stamp=node.get_clock().now().to_msg(); bad.header.stamp.sec+=2
        bad.pose.pose.orientation.w=1.; odom_pub.publish(bad)
        run(.2)
        report['checks']['isolated_future_odom_rejected_without_erasing_fresh_state']=latest.get('state')=='RUNNING'
        mode='duplicate_path'; run(.12); mode='normal'; run(.2)
        report['checks']['isolated_duplicate_path_does_not_stop']=latest.get('state')=='RUNNING'
        mode='lagged_tf';run(1.0)
        report['checks']['delayed_tf_does_not_starve_pending_observation']=latest.get('state')=='RUNNING'
        mode='normal';run(.3)
        enable(False)
        for fault in ('empty','missing_path','future','stale','wrong_frame','nan','missing_odom','missing_tf','future_odom','stale_odom','malformed_odom','duplicate_path'):
            latest.pop('frozen_stamp',None)
            mode='normal'; run(.3); enable(True)
            wait(lambda:latest.get('command',TwistStamped()).twist.linear.x>.01)
            mode=fault
            wait(lambda:latest.get('state','').startswith('STOPPED'))
            run(.1)
            stopped=latest['command'].twist.linear.x==0 and latest['command'].twist.angular.z==0
            mode='normal'; run(.35)
            report['checks'][fault]=stopped and latest.get('state','').startswith('STOPPED') and latest['command'].twist.linear.x==0
        enable(True); run(.2); enable(False); run(.1)
        report['checks']['explicit_disable']=latest['command'].twist.linear.x==0
    except Exception as exc:
        report['error']=str(exc)
    finally:
        report['passed']='error' not in report and bool(report['checks']) and all(report['checks'].values())
        output.write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
        node.destroy_node(); rclpy.shutdown()
        if process.poll() is None:
            os.killpg(process.pid,signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL); process.wait(timeout=5)
        log.close()
    return 0 if report['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
