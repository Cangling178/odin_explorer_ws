#!/usr/bin/env python3
"""Check arming ramps against command timestamps under a quantized ROS clock."""
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
import rclpy
from builtin_interfaces.msg import Time
from geometry_msgs.msg import PoseStamped,TransformStamped,TwistStamped
from nav_msgs.msg import Odometry
from racer_interfaces.msg import LineObservation
from rosgraph_msgs.msg import Clock
from std_msgs.msg import String
from std_srvs.srv import SetBool
from tf2_ros import TransformBroadcaster
from rclpy.qos import QoSProfile,DurabilityPolicy


def main():
    os.environ['ROS_DOMAIN_ID']='90'
    output=Path('data/generated/isolated/arming_clock_validation.json');output.parent.mkdir(parents=True,exist_ok=True)
    log=output.with_suffix('.log').open('w')
    process=subprocess.Popen(['ros2','run','racer_control','line_controller','--ros-args','-r','__ns:=/arming',
        '-r','/tf:=/arming/tf','-r','/tf_static:=/arming/tf_static','-p','use_sim_time:=true'],
        stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    rclpy.init();node=rclpy.create_node('arming_clock_test',cli_args=['--ros-args','-r','/tf:=/arming/tf'])
    clock=node.create_publisher(Clock,'/clock',1);odom=node.create_publisher(Odometry,'/arming/odom',10)
    observations=node.create_publisher(LineObservation,'/arming/observation',1);tf=TransformBroadcaster(node)
    commands=[];latest={};report=dict(data_kind='synthetic_quantized_clock',clock_step_s=.01,trials=[])
    node.create_subscription(TwistStamped,'/arming/cmd_vel',lambda m:commands.append(dict(time=m.header.stamp.sec+m.header.stamp.nanosec*1e-9,v=m.twist.linear.x,w=m.twist.angular.z)),100)
    node.create_subscription(String,'/arming/tracking_status',lambda m:latest.update(state=m.data),QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))
    client=node.create_client(SetBool,'/arming/line_controller/enable');epoch=time.monotonic();last_clock=last_obs=-1
    def step():
        nonlocal last_clock,last_obs
        rclpy.spin_once(node,timeout_sec=.001)
        tick=int((time.monotonic()-epoch)*100)
        if tick==last_clock:return
        last_clock=tick;stamp=Time(sec=10+tick//100,nanosec=(tick%100)*10000000)
        msg=Clock();msg.clock=stamp;clock.publish(msg)
        transform=TransformStamped();transform.header.stamp=stamp;transform.header.frame_id='odom';transform.child_frame_id='base_link';transform.transform.rotation.w=1.;tf.sendTransform(transform)
        state=Odometry();state.header=transform.header;state.child_frame_id='base_link';state.pose.pose.orientation.w=1.;odom.publish(state)
        if tick-last_obs>=5:
            last_obs=tick;ob=LineObservation();ob.path.header=transform.header;ob.path.header.frame_id='base_link';ob.image_valid=True;ob.path_valid=True;ob.confidence=1.;ob.exits=1;ob.reason='valid'
            for i in range(51):
                pose=PoseStamped();pose.header=ob.path.header;pose.pose.position.x=.2+i*.01;pose.pose.position.y=.03;pose.pose.orientation.w=1.;ob.path.poses.append(pose)
            observations.publish(ob)
    def wait(condition,timeout=10):
        end=time.monotonic()+timeout
        while not condition():
            if process.poll() is not None or time.monotonic()>end:raise RuntimeError('Timeout: '+str(latest))
            step()
    def run(duration):
        end=time.monotonic()+duration
        wait(lambda:time.monotonic()>=end,duration+5)
    def enable(value):
        wait(client.service_is_ready);req=SetBool.Request();req.data=value;future=client.call_async(req);wait(future.done)
        if not future.result().success:raise RuntimeError(future.result().message)
    try:
        wait(lambda:latest.get('state')=='READY' and bool(commands))
        for index in range(20):
            enable(False);run(.10+(index%7)*.003);wait(lambda:commands[-1]['v']==0)
            start=len(commands)-1;enable(True);run(.18)
            values=commands[start:]
            pairs=[(a,b) for a,b in zip(values,values[1:]) if b['time']>a['time'] and b['v']>0]
            av=max((abs(b['v']-a['v'])/(b['time']-a['time']) for a,b in pairs),default=math.inf)
            aw=max((abs(b['w']-a['w'])/(b['time']-a['time']) for a,b in pairs),default=math.inf)
            report['trials'].append(dict(index=index,linear_acceleration=av,yaw_acceleration=aw,commands=values,passed=av<=.15001 and aw<=.80001))
        enable(False)
    except Exception as exc:report['error']=str(exc)
    finally:
        report['passed']='error' not in report and len(report['trials'])==20 and all(t['passed'] for t in report['trials'])
        output.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(dict(passed=report['passed'],trials=len(report['trials']),error=report.get('error'))))
        node.destroy_node();rclpy.shutdown()
        if process.poll() is None:
            os.killpg(process.pid,signal.SIGINT)
            try:process.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
        log.close()
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
