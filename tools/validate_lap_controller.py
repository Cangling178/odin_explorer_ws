#!/usr/bin/env python3
"""Synthetic ROS input faults for the C++ lap controller; no simulator or hardware."""
import json,os,signal,subprocess,time
from pathlib import Path
import numpy as np
import rclpy
from geometry_msgs.msg import TransformStamped,TwistStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Image
from racer_interfaces.msg import LineObservation
from std_msgs.msg import String
from std_srvs.srv import SetBool
from tf2_msgs.msg import TFMessage
from rclpy.qos import QoSProfile,DurabilityPolicy
ROOT=Path(__file__).resolve().parents[1]

def main():
    os.environ['ROS_DOMAIN_ID']='98'
    output=ROOT/'data/generated/competition_lap';output.mkdir(parents=True,exist_ok=True)
    log=(output/'controller_faults.log').open('w')
    process=subprocess.Popen(['ros2','run','racer_control','lap_controller','--ros-args','-r','__ns:=/lap_test',
        '-r','/tf:=/lap_test/tf','-r','/tf_static:=/lap_test/tf_static','-p',
        'route_file:='+str(ROOT/'src/odin_racer/racer_control/config/competition_lap.csv')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    rclpy.init();node=rclpy.create_node('lap_fault_inputs');latest={};mode='normal';last_message=None;checks={}
    qos=QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL)
    node.create_subscription(String,'/lap_test/tracking_status',lambda m:latest.update(state=m.data),qos)
    node.create_subscription(TwistStamped,'/lap_test/cmd_vel',lambda m:latest.update(v=m.twist.linear.x,w=m.twist.angular.z),10)
    op=node.create_publisher(Odometry,'/lap_test/odom',10);tp=node.create_publisher(TFMessage,'/lap_test/tf',10)
    ip=node.create_publisher(LineObservation,'/lap_test/observation',5);mp=node.create_publisher(Image,'/lap_test/black_mask',3)
    mask=np.zeros((131,201),np.uint8);mask[:,98:103]=255
    def publish():
        nonlocal last_message
        stamp=node.get_clock().now().to_msg()
        tf=TransformStamped();tf.header.stamp=stamp;tf.header.frame_id='odom';tf.child_frame_id='base_link';tf.transform.rotation.w=1.
        if mode!='tf':tp.publish(TFMessage(transforms=[tf]))
        odom=Odometry();odom.header=tf.header;odom.child_frame_id='base_link';odom.pose.pose.orientation.w=1.
        if mode!='odom':op.publish(odom)
        obs=LineObservation();obs.path.header.stamp=stamp;obs.path.header.frame_id='base_link';obs.image_valid=mode!='invalid';obs.reason='synthetic_healthy_image'
        if mode=='duplicate' and last_message is not None:obs=last_message
        if mode!='image':ip.publish(obs)
        if mode=='normal':last_message=obs
        image=Image();image.header.stamp=stamp;image.header.frame_id='camera';image.height=131;image.width=201;image.step=201;image.encoding='mono8';image.data=mask.tobytes()
        if mode not in ('image','duplicate'):mp.publish(image)
    timer=node.create_timer(.05,publish)
    client=node.create_client(SetBool,'/lap_test/lap_controller/enable')
    def wait(predicate,limit):
        end=time.monotonic()+limit
        while not predicate():
            if time.monotonic()>end:raise RuntimeError('Timeout '+str(latest))
            rclpy.spin_once(node,timeout_sec=.01)
    def run(duration):
        start=time.monotonic();wait(lambda:time.monotonic()-start>duration,duration+2)
    def enable():
        req=SetBool.Request();req.data=True;future=client.call_async(req);wait(future.done,3)
        if not future.result().success:raise RuntimeError('Enable rejected')
        wait(lambda:latest.get('v',0)>.01,2)
    try:
        wait(lambda:latest.get('state')=='READY' and client.service_is_ready(),15);run(.3)
        checks['no_automatic_motion']=latest.get('v')==0
        for fault in ('image','odom','tf','invalid','duplicate'):
            mode='normal';run(.8);enable();mode=fault;start=time.monotonic()
            wait(lambda:latest.get('state','').startswith('STOPPED'),1.5)
            delay=time.monotonic()-start;run(.1)
            checks[fault+'_stop']=latest.get('v')==0 and latest.get('w')==0 and delay<.65
            mode='normal';run(.6)
            checks[fault+'_latch']=latest.get('state','').startswith('STOPPED') and latest.get('v')==0
        checks['explicit_reenable']=True
    except Exception as exc:checks['error']=str(exc)
    finally:
        if process.poll() is None:
            os.killpg(process.pid,signal.SIGINT)
            try:process.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
        node.destroy_node()
        if rclpy.ok():rclpy.shutdown()
        log.close();(output/'controller_faults.json').write_text(json.dumps(checks,indent=2)+'\n');print(json.dumps(checks,indent=2))
    return 0 if checks and all(v is True for v in checks.values()) else 1
if __name__=='__main__':raise SystemExit(main())
