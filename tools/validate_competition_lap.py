#!/usr/bin/env python3
"""Run and independently score a continuous full Gazebo lap (actively enables)."""
import argparse,json,math,os,signal,socket,subprocess,time,hashlib
from pathlib import Path
import numpy as np
import rclpy
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data,QoSProfile,DurabilityPolicy
from gazebo_msgs.msg import LinkStates
from geometry_msgs.msg import TwistStamped
from std_msgs.msg import String
from std_srvs.srv import SetBool
from racer_interfaces.msg import LineObservation
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True);parser.add_argument('--duration',type=float,default=650)
    parser.add_argument('--domain',type=int,default=96);parser.add_argument('--port',type=int,default=11396)
    parser.add_argument('--speed',type=float,default=.05);parser.add_argument('--lookahead',type=float,default=.10)
    args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    if (args.output/'report.json').exists():raise ValueError('Use a new output directory')
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1',args.port))==0:raise RuntimeError('Gazebo port occupied')
    os.environ['ROS_DOMAIN_ID']=str(args.domain);os.environ['GAZEBO_MASTER_URI']=f'http://127.0.0.1:{args.port}'
    os.environ['FASTRTPS_DEFAULT_PROFILES_FILE']=str(ROOT/'src/odin_racer/racer_bringup/config/line_fastdds.xml')
    path=np.loadtxt(ROOT/'src/odin_racer/racer_control/config/competition_lap.csv',delimiter=',')
    delta=np.diff(path,axis=0);length=np.linalg.norm(delta,axis=1);arc=np.r_[0,np.cumsum(length)]
    stations=np.arange(0,arc[-1],.10);gates=np.c_[np.interp(stations,arc,path[:,0]),np.interp(stations,arc,path[:,1])]
    report=dict(criteria=dict(max_axle_error_m=.10,rms_axle_error_m=.05,gate_radius_m=.10,gate_spacing_m=.10,
        minimum_moving_speed_mps=.003,startup_exclusion_s=1.,max_observation_age_s=.35),samples=[],events=[],commands=[],checks={})
    report['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'src/odin_racer/racer_control/src/lap_controller.cpp',ROOT/'src/odin_racer/racer_control/include/racer_control/lap_route.hpp',ROOT/'src/odin_racer/racer_control/config/competition_lap.csv']}
    report['binary_sha256']=hashlib.sha256((ROOT/'install/racer_control/lib/racer_control/lap_controller').read_bytes()).hexdigest()
    log=(args.output/'launch.log').open('w');process=subprocess.Popen(['ros2','launch','racer_bringup','competition_lap.launch.py','gui:=false',f'speed:={args.speed}',f'lookahead:={args.lookahead}'],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    rclpy.init();node=rclpy.create_node('competition_lap_evaluator',parameter_overrides=[Parameter('use_sim_time',value=True)])
    latest={};visited=0;start=None
    def now():return node.get_clock().now().nanoseconds*1e-9
    def status(msg):
        latest['state']=msg.data
        if not report['events'] or report['events'][-1]['state']!=msg.data:report['events'].append(dict(time=now(),state=msg.data))
    node.create_subscription(String,'/sim/racer/line/tracking_status',status,QoSProfile(depth=1,durability=DurabilityPolicy.TRANSIENT_LOCAL))
    def debug(msg):
        try:latest['debug']=json.loads(msg.data)
        except ValueError:pass
    node.create_subscription(String,'/sim/racer/line/control_debug',debug,5)
    def command(msg):
        latest['command']=(msg.twist.linear.x,msg.twist.angular.z)
        report['commands'].append(dict(time=now(),v=msg.twist.linear.x,w=msg.twist.angular.z,state=latest.get('state')))
    node.create_subscription(TwistStamped,'/sim/racer/diff_drive_controller/cmd_vel',command,100)
    def truth(msg):
        if 'odin_racer::base_link' in msg.name:
            i=msg.name.index('odin_racer::base_link');latest['truth']=(msg.pose[i],msg.twist[i]);latest['truth_stamp']=now()
    node.create_subscription(LinkStates,'/contact_test/link_states',truth,qos_profile_sensor_data)
    def observation(msg):
        latest['observation']=dict(valid=msg.path_valid,reason=msg.reason,exits=msg.exits,confidence=msg.confidence,points=len(msg.path.poses),first=([msg.path.poses[0].pose.position.x,msg.path.poses[0].pose.position.y] if msg.path.poses else None))
    node.create_subscription(LineObservation,'/sim/racer/line/observation',observation,1)
    client=node.create_client(SetBool,'/sim/racer/line/lap_controller/enable')
    def spin():
        rclpy.spin_once(node,timeout_sec=.01)
        if process.poll() is not None:raise RuntimeError('Launch exited')
    def wait(predicate,seconds):
        end=time.monotonic()+seconds
        while not predicate():
            if time.monotonic()>end:raise RuntimeError('Wait timeout '+str(latest.get('state')))
            spin()
    def enable(value):
        wait(client.service_is_ready,5);req=SetBool.Request();req.data=value;future=client.call_async(req);wait(future.done,5)
        if not future.result().success:raise RuntimeError('Enable rejected '+future.result().message)
    try:
        wait(lambda:latest.get('state')=='READY' and 'truth' in latest,100)
        settle=now();wait(lambda:now()-settle>.8,20)
        report['checks']['single_command_publisher']=node.count_publishers('/sim/racer/diff_drive_controller/cmd_vel')==1
        report['checks']['initially_disarmed']=latest['command']==(0.,0.)
        enable(True);start=now();last=-1;printed=-20;deadline=time.monotonic()+args.duration*15
        while now()-start<args.duration:
            spin()
            if time.monotonic()>deadline:raise RuntimeError('Wall timeout')
            if now()-last<.05:continue
            last=now();pose,twist=latest['truth'];p=np.array([pose.position.x,pose.position.y]);q=pose.orientation
            fraction=np.clip(np.sum((p-path[:-1])*delta,axis=1)/length**2,0,1)
            error=float(np.min(np.linalg.norm(p-path[:-1]-fraction[:,None]*delta,axis=1)))
            while visited<len(gates) and np.linalg.norm(p-gates[visited])<=.10:visited+=1
            sample=dict(time=now()-start,x=float(p[0]),y=float(p[1]),yaw=math.atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z)),
                speed=math.hypot(twist.linear.x,twist.linear.y),w=twist.angular.z,error=error,gates=visited,state=latest.get('state'),
                cmd_v=latest['command'][0],cmd_w=latest['command'][1],debug=latest.get('debug',{}),truth_age=now()-latest['truth_stamp'],observation=latest.get('observation'))
            report['samples'].append(sample)
            if sample['time']-printed>=15:
                print(f"t={sample['time']:.1f} gates={visited}/{len(gates)} xy={p.round(3)} error={error:.3f} state={sample['state']}",flush=True);printed=sample['time']
                (args.output/'progress.json').write_text(json.dumps(sample,indent=2))
            if sample['state'].startswith('STOPPED') or sample['state']=='FINISHED':break
        report['termination']=latest.get('state');enable(False)
        stopped=now();wait(lambda:now()-stopped>1.2,20)
        report['checks']['final_physical_stop']=math.hypot(latest['truth'][1].linear.x,latest['truth'][1].linear.y)<.005
    except (Exception,KeyboardInterrupt) as exc:report['error']=str(exc)
    finally:
        try:enable(False)
        except Exception:pass
        samples=report['samples'];active=[s for s in samples if s['time']>1 and s['state']=='RUNNING']
        if samples:
            e=np.array([s['error'] for s in samples]);dt=np.diff([0]+[s['time'] for s in samples]);dt=np.maximum(dt,1e-6)
            report['metrics']=dict(duration_s=samples[-1]['time'],rms_error_m=float(np.sqrt(np.sum(dt*e*e)/sum(dt))),max_error_m=float(max(e)),
                gates_visited=visited,gates_total=len(gates),min_moving_speed_mps=min((s['speed'] for s in active),default=0))
            report['checks'].update(full_lap=visited==len(gates) and samples[-1]['state']=='FINISHED' and math.dist([samples[-1]['x'],samples[-1]['y']],path[0])<.10,
                no_mid_lap_stop=bool(active) and all(s['speed']>.003 and s['cmd_v']>0 for s in active) and all(s['state']=='RUNNING' for s in samples if s['time']>1 and s['state']!='FINISHED'),
                max_error=max(e)<=.10,rms_error=report['metrics']['rms_error_m']<=.05,truth_fresh=all(s['truth_age']<.15 for s in samples),
                observation_fresh=bool(active) and all(s['debug'].get('observation_age',1)<.351 for s in active),
                command_bounds=all(0<=s['cmd_v']<=args.speed+.0001 and abs(s['cmd_w'])<=.501 for s in samples))
        report['checks']={k:bool(v) for k,v in report['checks'].items()}
        report['passed']='error' not in report and bool(samples) and all(report['checks'].values())
        (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('samples','commands','events','source_sha256')},indent=2),flush=True)
        if process.poll() is None:
            os.killpg(process.pid,signal.SIGINT)
            try:process.wait(timeout=15)
            except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
        node.destroy_node()
        if rclpy.ok():rclpy.shutdown()
        log.close()
        if samples:
            import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
            fig,axes=plt.subplots(1,2,figsize=(13,6));axes[0].plot(path[:,0],path[:,1],'k--',lw=1,label='map line');axes[0].plot([s['x'] for s in samples],[s['y'] for s in samples],label='Gazebo axle');axes[0].axis('equal');axes[0].legend()
            axes[1].plot([s['time'] for s in samples],[s['speed'] for s in samples],label='physical speed m/s');axes[1].plot([s['time'] for s in samples],[s['error'] for s in samples],label='line error m');axes[1].legend();axes[1].grid();fig.tight_layout();fig.savefig(args.output/'trajectory.png')
    return 0 if report['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
