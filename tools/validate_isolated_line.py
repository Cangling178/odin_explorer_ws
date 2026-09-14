#!/usr/bin/env python3
"""Actively run one isolated simulation; truth only enters this evaluator."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import cv2
import numpy as np
import rclpy
from rclpy.parameter import Parameter
from rclpy.executors import SingleThreadedExecutor
from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy
from gazebo_msgs.msg import LinkStates
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Path as RosPath, Odometry
from sensor_msgs.msg import Image
from std_msgs.msg import String
from std_srvs.srv import SetBool
from tf2_msgs.msg import TFMessage
from ament_index_python.packages import get_package_share_directory
from racer_description.course_world import LINE_SCENES, line_fixture
from isolated_line_metrics import Evaluator, footprint, summarize

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--course',choices=LINE_SCENES,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--duration',type=float,default=100.)
    parser.add_argument('--spawn-x',type=float,default=0.)
    parser.add_argument('--spawn-y',type=float,default=-.035)
    parser.add_argument('--spawn-yaw',type=float,default=-.08)
    parser.add_argument('--domain',type=int,default=93)
    parser.add_argument('--port',type=int,default=11393)
    parser.add_argument('--fault',choices=['drop','blank','tf','odom'])
    parser.add_argument('--fault-phase',choices=['RUNNING','APPROACH','TURN'],default='RUNNING')
    parser.add_argument('--static',action='store_true',help='Save stationary observations without enabling')
    args=parser.parse_args()
    if not all(math.isfinite(v) for v in (args.duration,args.spawn_x,args.spawn_y,args.spawn_yaw)) or args.duration<=0:
        parser.error('Nonfinite/invalid test parameters')
    args.output.mkdir(parents=True,exist_ok=True)
    if (args.output/'report.json').exists():
        parser.error('Output exists; use a new directory to retain every attempt')
    criteria=json.loads((ROOT/'experiments/isolated_line/acceptance.json').read_text())
    fixture=line_fixture(args.course,dict(spawn_x=args.spawn_x,spawn_y=args.spawn_y,spawn_yaw=args.spawn_yaw))
    body,envelope=footprint(Path(get_package_share_directory('racer_description')))
    evaluator=Evaluator(fixture,body)
    report=dict(course=args.course,fixture=fixture,criteria=criteria,footprint=envelope,
                data_kind='gazebo_onboard_image',checks={},samples=[],commands=[],events=[],captures=[],fault=None)
    report['binary_sha256']={name:hashlib.sha256((ROOT/'install'/name/'lib'/name/exe).read_bytes()).hexdigest() for name,exe in [('racer_perception','line_perception'),('racer_control','line_controller')]}
    report['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
      for folder in ('racer_perception','racer_control') for p in (ROOT/'src/odin_racer'/folder).rglob('*')
      if p.is_file() and p.suffix in ('.cpp','.hpp','.yaml')}
    os.environ['ROS_DOMAIN_ID']=str(args.domain);os.environ['GAZEBO_MASTER_URI']=f'http://127.0.0.1:{args.port}'
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1',args.port))==0:
            raise RuntimeError('Test Gazebo port occupied')
    log=(args.output/'launch.log').open('w')
    process=subprocess.Popen(['ros2','launch','racer_bringup','line_following.launch.py','gui:=false',
        f'course:={args.course}','course_parameters:='+json.dumps(dict(spawn_x=args.spawn_x,spawn_y=args.spawn_y,spawn_yaw=args.spawn_yaw)),
        'image_topic:=/validation/image',
        'odom_topic:='+('/validation/odom' if args.fault=='odom' else '/sim/racer/diff_drive_controller/odom'),
        'tf_topic:='+('/validation/tf' if args.fault=='tf' else '/sim/racer/tf')],
        stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    rclpy.init();node=rclpy.create_node('isolated_line_evaluator',parameter_overrides=[Parameter('use_sim_time',value=True)])
    relay_node=rclpy.create_node('isolated_sensor_relay')
    relay_executor=SingleThreadedExecutor();relay_executor.add_node(relay_node)
    latest={};mode='normal';last_capture=-1.;last_state='';injected=None
    writer=ThreadPoolExecutor(max_workers=1)
    image_writes=[]
    def now(): return node.get_clock().now().nanoseconds*1e-9
    relay=relay_node.create_publisher(Image,'/validation/image',1)
    odom_relay=relay_node.create_publisher(Odometry,'/validation/odom',10)
    tf_relay=relay_node.create_publisher(TFMessage,'/validation/tf',100)
    def image(msg):
        latest['image']=msg
        if mode=='drop': return
        if mode=='blank':
            msg=copy.deepcopy(msg);msg.data=bytes([200])*len(msg.data)
        latest['input']=msg;relay.publish(msg)
    relay_node.create_subscription(Image,'/sim/racer/odin1/image',image,1)
    relay_node.create_subscription(Odometry,'/sim/racer/diff_drive_controller/odom',lambda m: odom_relay.publish(m) if mode!='odom' else None,qos_profile_sensor_data)
    relay_node.create_subscription(TFMessage,'/sim/racer/tf',lambda m:tf_relay.publish(m) if mode!='tf' else None,100)
    relay_thread=threading.Thread(target=relay_executor.spin,daemon=True);relay_thread.start()
    for key,topic in [('ground','ground_debug'),('mask','black_mask'),('gray','ground_gray')]:
        node.create_subscription(Image,'/sim/racer/line/'+topic,lambda m,k=key:latest.update({k:m}),1)
    for key,topic in [('state','tracking_status'),('perception','perception_status'),('telemetry','control_debug')]:
        def status(m,k=key):
            latest[k]=m.data
            if k=='state' and (not report['events'] or report['events'][-1]['state']!=m.data):
                report['events'].append(dict(time=now(),state=m.data))
        node.create_subscription(String,'/sim/racer/line/'+topic,status,
            QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL) if key=='state' else 1)
    node.create_subscription(RosPath,'/sim/racer/line/local_path',lambda m:latest.update(path=m),1)
    def command(m):
        latest['command']=m
        report['commands'].append(dict(time=m.header.stamp.sec+m.header.stamp.nanosec*1e-9,v=m.twist.linear.x,w=m.twist.angular.z,state=latest.get('state','')))
    node.create_subscription(TwistStamped,'/sim/racer/diff_drive_controller/cmd_vel',command,100)
    def truth(m):
        if 'odin_racer::base_link' in m.name:
            i=m.name.index('odin_racer::base_link');latest['truth']=(m.pose[i],m.twist[i])
    node.create_subscription(LinkStates,'/contact_test/link_states',truth,qos_profile_sensor_data)
    client=node.create_client(SetBool,'/sim/racer/line/line_controller/enable')
    def spin():
        if process.poll() is not None: raise RuntimeError('Launch exited')
        rclpy.spin_once(node,timeout_sec=.005)
    def wait(condition,timeout):
        deadline=time.monotonic()+timeout
        while not condition():
            if time.monotonic()>deadline: raise RuntimeError('Timeout: '+str({k:latest.get(k) for k in ('state','perception')}))
            spin()
    def run(seconds):
        start=now();wait(lambda:now()-start>=seconds,seconds*20+10)
    def enable(value):
        if not value: report.setdefault('explicit_stop_times',[]).append(now())
        wait(client.service_is_ready,10)
        req=SetBool.Request();req.data=value;future=client.call_async(req)
        wait(future.done,10)
        if not future.result().success:raise RuntimeError('Enable rejected: '+future.result().message)
    def capture(tag):
        entry=dict(time=now(),tag=tag,files={},perception=latest.get('perception'),telemetry=latest.get('telemetry'))
        for key in ('image','input','ground','mask','gray'):
            if key not in latest:continue
            msg=latest[key];channels=1 if msg.encoding=='mono8' else 3
            arr=np.frombuffer(msg.data,np.uint8).reshape(msg.height,msg.step)[:,:msg.width*channels].reshape(msg.height,msg.width,channels)
            if msg.encoding=='rgb8':arr=cv2.cvtColor(arr,cv2.COLOR_RGB2BGR)
            name=f'{len(report["captures"]):04d}_{tag}_{key}.png';image_writes.append(writer.submit(cv2.imwrite,str(args.output/name),arr.copy()));entry['files'][key]=name
        path=latest.get('path',RosPath())
        entry['path_stamp']=path.header.stamp.sec+path.header.stamp.nanosec*1e-9
        entry['path']=[[p.pose.position.x,p.pose.position.y] for p in path.poses]
        report['captures'].append(entry)
    try:
        wait(lambda:('perception' in latest if args.static else latest.get('state')=='READY') and 'truth' in latest,100)
        run(.6)
        if not args.static: wait(lambda:latest.get('state')=='READY',10)
        capture('initial')
        report['checks']['disarmed_at_start']=abs(latest['command'].twist.linear.x)<1e-9
        report['checks']['single_command_publisher']=node.count_publishers('/sim/racer/diff_drive_controller/cmd_vel')==1
        if args.static:
            run(2);capture('static');report['checks']['stationary']=abs(latest['truth'][1].linear.x)<.005
        else:
            enable(True);start=now();deadline=time.monotonic()+args.duration*20+30;last=-1
            while now()-start<args.duration:
                spin()
                if time.monotonic()>deadline:raise RuntimeError('Simulation stalled')
                if now()-last<.05:continue
                sample_dt=.05 if last<0 else now()-last
                last=now();pose,twist=latest['truth'];q=pose.orientation
                yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z))
                x,y=pose.position.x,pose.position.y;cmd=latest['command'].twist
                sample=dict(time=now()-start,sample_dt=sample_dt,x=x,y=y,yaw=yaw,speed=math.hypot(twist.linear.x,twist.linear.y),
                    yaw_rate=twist.angular.z,cmd_v=cmd.linear.x,cmd_w=cmd.angular.z,state=latest.get('state',''),
                    perception=latest.get('perception',''),telemetry=latest.get('telemetry',''))
                sample.update(evaluator.sample(x,y,yaw));report['samples'].append(sample)
                if now()-last_capture>=1. or sample['state']!=last_state:
                    capture('run');last_capture=now();last_state=sample['state']
                if args.fault and injected is None and sample['state']==args.fault_phase and now()-start>2 and (abs(sample['yaw_rate'])>.08 if args.fault_phase=='TURN' else sample['speed']>.015):
                    mode=args.fault;injected=now();capture('fault_start')
                if sample['state'].startswith('STOPPED'):
                    report['termination']=dict(reason=sample['state'],time=sample['time'],x=x,y=y)
                    capture('stopped')
                    if injected is not None:
                        delay=now()-injected;run(1.2);t=latest['truth'][1]
                        physical=math.hypot(t.linear.x,t.linear.y)<.005 and abs(t.angular.z)<.02
                        mode='normal';run(1.0);cmd=latest['command'].twist
                        report['fault']=dict(kind=args.fault,phase=args.fault_phase,request_delay_s=delay,physical_stop=physical,
                            latched=latest.get('state','').startswith('STOPPED') and cmd.linear.x==0 and cmd.angular.z==0)
                    break
                if sample['at_end']:
                    report['termination']=dict(reason='evaluation_end_region',time=sample['time'],x=x,y=y);break
            report.setdefault('termination',dict(reason='evaluation_timeout',time=now()-start))
            capture('final')
            metrics,checks=summarize(report['samples'],criteria,args.course,fixture);report['metrics']=metrics
            if args.fault:
                fault=report['fault'];checks=dict(fault_reached=fault is not None)
                if fault: checks.update(fault_stop=fault['physical_stop'],fault_latched=fault['latched'],fault_latency=fault['request_delay_s']<criteria['fault_request_max_s'])
            report['checks'].update(checks)
            enable(False);run(1.2)
            report['checks']['explicit_stop']=math.hypot(latest['truth'][1].linear.x,latest['truth'][1].linear.y)<.005
    except Exception as exc:
        report['error']=str(exc)
        capture('failure')
    finally:
        try: enable(False)
        except Exception:pass
        writer.shutdown(wait=True)
        report['checks']['captures_written']=all(f.result() for f in image_writes)
        if 'truth' in latest:
            pose,twist=latest['truth']
            report['parking_pose']=dict(x=pose.position.x,y=pose.position.y,speed=math.hypot(twist.linear.x,twist.linear.y),yaw_rate=twist.angular.z)
        report['last_state']=latest.get('state');report['last_perception']=latest.get('perception')
        active=[s for s in report['samples'] if s['state'] in ('RUNNING','APPROACH','CORNER_STOP','TURN','REACQUIRE')]
        telemetry=[]
        for sample in active:
            try: telemetry.append(json.loads(sample['telemetry']))
            except (ValueError,KeyError): pass
        if telemetry:
            report['max_observation_age_s']=max(t['observation_age'] for t in telemetry)
            report['checks']['observation_age']=report['max_observation_age_s']<=criteria['path_age_max_s']+.001
        if active:
            report['max_truth_speed_mps']=max(s['speed'] for s in active)
            report['max_truth_yaw_radps']=max(abs(s['yaw_rate']) for s in active)
            # Contact dynamics may overshoot command limits; report and test a
            # separately stated 10% physical tolerance (not an error tolerance).
            report['checks']['physical_velocity_bounds']=report['max_truth_speed_mps']<=criteria['speed_max_mps']*1.1 and report['max_truth_yaw_radps']<=criteria['yaw_rate_max_radps']*1.1

        # Fault zero requests intentionally bypass acceleration shaping.
        stop_times=report.get('explicit_stop_times',[])+[e['time'] for e in report['events'] if e['state'].startswith('STOPPED')]
        def intentional_zero(b):
            return b['v']==0 and b['w']==0 and any(-.06<=b['time']-t<=.20 for t in stop_times)
        pairs=[(a,b) for a,b in zip(report['commands'],report['commands'][1:]) if b['time']>a['time'] and not intentional_zero(b) and a['state']==b['state'] and b['state'] in ('RUNNING','APPROACH','TURN','REACQUIRE')]
        if pairs:
            report['command_acceleration']=dict(v=max(abs(b['v']-a['v'])/(b['time']-a['time']) for a,b in pairs),w=max(abs(b['w']-a['w'])/(b['time']-a['time']) for a,b in pairs))
            report['checks']['acceleration']=report['command_acceleration']['v']<=criteria['acceleration_max_mps2']+.005 and report['command_acceleration']['w']<=criteria['yaw_acceleration_max_radps2']+.02
        report['passed']='error' not in report and bool(report['checks']) and all(report['checks'].values())
        (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('fixture','samples','commands','captures','source_sha256')},indent=2),flush=True)
        relay_executor.shutdown();relay_thread.join(timeout=3);relay_node.destroy_node()
        node.destroy_node();rclpy.shutdown()
        if process.poll() is None:
            os.killpg(process.pid,signal.SIGINT)
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait(timeout=5)
        log.close()
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
