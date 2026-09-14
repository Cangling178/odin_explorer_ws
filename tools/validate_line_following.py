#!/usr/bin/env python3
"""Launch an isolated C++ visual tracking test and actively drive in Gazebo.

Requires a sourced workspace and DISPLAY. Analytic truth is evaluation-only.
A relay injects image loss/blank frames; the algorithm only sees camera data,
CameraInfo, TF and wheel odometry. No world reset or hardware command is used.
"""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time

import cv2
import numpy as np
import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data, QoSProfile, DurabilityPolicy
from gazebo_msgs.msg import LinkStates
from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Path as RosPath
from sensor_msgs.msg import Image
from std_msgs.msg import String
from std_srvs.srv import SetBool


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--course', choices=['line_straight', 'line_arc', 'competition'], default='line_straight')
    parser.add_argument('--duration', type=float, default=25.)
    parser.add_argument('--domain', type=int, default=91)
    parser.add_argument('--port', type=int, default=11391)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not math.isfinite(args.duration) or args.duration <= 0:
        parser.error('duration must be positive and finite')
    if args.course == 'competition' and args.duration > 8:
        parser.error('competition validation covers only the first 8 seconds of the initial straight')
    course_y = 0.
    if args.course == 'competition':
        course_config = Path(get_package_share_directory('racer_description'))/'config/competition_course.yaml'
        course_y = yaml.safe_load(course_config.read_text())['spawn_y_m']
    output = args.output or Path('data/generated')/(args.course+'_following_validation.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        import shutil
        shutil.copy2(output, output.with_name(output.stem+'_previous_'+str(time.time_ns())+'.json'))
    os.environ['ROS_DOMAIN_ID'] = str(args.domain)
    os.environ['GAZEBO_MASTER_URI'] = f'http://127.0.0.1:{args.port}'
    # Refuse an occupied master instead of connecting to someone else's world.
    import socket
    with socket.socket() as probe:
        if probe.connect_ex(('127.0.0.1', args.port)) == 0:
            raise RuntimeError('Gazebo test port is already in use')
    log = output.with_suffix('.log').open('w')
    process = subprocess.Popen(['ros2', 'launch', 'racer_bringup', 'line_following.launch.py',
                                'gui:=false', f'course:={args.course}', 'image_topic:=/validation/image'],
                               stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    rclpy.init()
    node = rclpy.create_node('validate_line_following', parameter_overrides=[Parameter('use_sim_time', value=True)])
    latest = {}
    relay_mode = 'normal'
    samples = []
    report = {'data_kind': 'simulation', 'course': args.course, 'checks': {}, 'faults': [], 'perception_events': []}
    relay = node.create_publisher(Image, '/validation/image', 1)
    def image(msg):
        latest['image'] = msg
        if relay_mode == 'drop':
            return
        if relay_mode == 'blank':
            msg = copy.deepcopy(msg)
            msg.data = bytes([200])*len(msg.data)
        relay.publish(msg)
    node.create_subscription(Image, '/sim/racer/odin1/image', image, 1)
    node.create_subscription(Image, '/sim/racer/line/ground_debug', lambda m: latest.update(debug=m), 1)
    def perception_status(msg):
        latest['perception'] = msg.data
        if not msg.data.startswith('valid'):
            report['perception_events'].append({'time': node.get_clock().now().nanoseconds*1e-9, 'reason': msg.data, 'mode': relay_mode})
    node.create_subscription(String, '/sim/racer/line/perception_status', perception_status, 1)
    node.create_subscription(String, '/sim/racer/line/tracking_status', lambda m: latest.update(state=m.data),
                             QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL))
    node.create_subscription(RosPath, '/sim/racer/line/local_path', lambda m: latest.update(path=m), 1)
    node.create_subscription(TwistStamped, '/sim/racer/diff_drive_controller/cmd_vel', lambda m: latest.update(command=m), 1)
    def truth(msg):
        if 'odin_racer::base_link' in msg.name:
            i = msg.name.index('odin_racer::base_link')
            latest['truth'] = (msg.pose[i], msg.twist[i])
    node.create_subscription(LinkStates, '/contact_test/link_states', truth, qos_profile_sensor_data)
    client = node.create_client(SetBool, '/sim/racer/line/line_controller/enable')
    def now():
        return node.get_clock().now().nanoseconds*1e-9
    def wait_until(condition, timeout=60):
        end = time.monotonic()+timeout
        while not condition():
            if process.poll() is not None or time.monotonic() > end:
                raise RuntimeError('Timed out: '+str({k: latest.get(k) for k in ('state','perception')}))
            rclpy.spin_once(node, timeout_sec=.01)
    def enable(value):
        if not client.wait_for_service(timeout_sec=5):
            raise RuntimeError('Missing enable service')
        request = SetBool.Request(); request.data = value
        future = client.call_async(request)
        wait_until(future.done, 10)
        if not future.result().success:
            raise RuntimeError('Enable rejected: '+future.result().message)
    def run(duration, collect=False):
        start, wall, last = now(), time.monotonic(), -1
        while now()-start < duration:
            if time.monotonic()-wall > duration*15+30:
                raise RuntimeError('Simulation stalled')
            rclpy.spin_once(node, timeout_sec=.003)
            if collect and 'truth' in latest and now()-last >= .05:
                last = now()
                pose, twist = latest['truth']; x, y = pose.position.x, pose.position.y
                error = (y if args.course == 'line_straight' else
                         y-course_y if args.course == 'competition' else math.hypot(x,y-.8)-.8)
                command = latest.get('command', TwistStamped()).twist
                samples.append({'time': now()-start, 'x': x, 'y': y, 'error': error,
                                'speed': math.hypot(twist.linear.x,twist.linear.y),
                                'cmd_v': command.linear.x, 'cmd_w': command.angular.z,
                                'state': latest.get('state',''), 'perception': latest.get('perception',''),
                                'path_size': len(latest.get('path',RosPath()).poses)})
    def save_image(key, suffix):
        if key not in latest:
            return
        msg = latest[key]
        array = np.frombuffer(msg.data,np.uint8).reshape(msg.height,msg.step)[:,:msg.width*3].reshape(msg.height,msg.width,3)
        if msg.encoding=='rgb8':
            array=cv2.cvtColor(array,cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(output.with_name(output.stem+suffix+'.png')),array)
    try:
        wait_until(lambda: latest.get('state') == 'READY' and 'truth' in latest, 100)
        run(1.)
        report['checks']['disarmed_at_start'] = abs(latest['command'].twist.linear.x) < 1e-9
        report['checks']['single_command_publisher'] = node.count_publishers('/sim/racer/diff_drive_controller/cmd_vel') == 1
        save_image('image','_initial'); save_image('debug','_ground_initial')
        enable(True)
        run(args.duration, collect=True)
        save_image('image','_final'); save_image('debug','_ground_final')
        tail = [s for s in samples if s['time'] > args.duration*.7]
        distance = sum(math.hypot(b['x']-a['x'],b['y']-a['y']) for a,b in zip(samples,samples[1:]))
        times = np.array([s['time'] for s in tail])
        errors = np.array([s['error'] for s in tail])
        tail_rms = float(np.sqrt(np.trapz(errors**2, times)/(times[-1]-times[0])))
        progress = (np.unwrap([math.atan2(s['x'], .8-s['y']) for s in samples])*.8
                    if args.course == 'line_arc' else np.array([s['x'] for s in samples]))
        report['metrics'] = {'distance_m': distance, 'forward_progress_m': float(progress[-1]-progress[0]),
                             'tail_rms_error_m': tail_rms,
                             'max_abs_error_m': max(abs(s['error']) for s in samples),
                             'tail_max_abs_error_m': max(abs(s['error']) for s in tail)}
        report['checks'].update(continuous_tracking=all(s['state']=='RUNNING' for s in samples[2:]),
                                 moved=distance > args.duration*.035,
                                 ordered_forward_progress=bool(progress[-1]-progress[0] > args.duration*.035 and np.min(np.diff(progress)) > -.002),
                                 command_bounds=all(0<=s['cmd_v']<=.050001 and abs(s['cmd_w'])<=.500001 for s in samples))
        if args.course != 'competition':
            report['checks']['converged'] = report['metrics']['tail_rms_error_m'] < .015
        for mode in (() if args.course == 'competition' else ('drop','blank')):
            if latest.get('state') != 'RUNNING':
                raise RuntimeError('Fault injection requires active tracking')
            relay_mode = mode
            began = now()
            wait_until(lambda: latest.get('state','').startswith('STOPPED'), 10)
            stop_request_delay = now()-began
            run(1.2)
            twist=latest['truth'][1]
            stopped=math.hypot(twist.linear.x,twist.linear.y)<.005 and abs(twist.angular.z)<.02
            relay_mode='normal'
            run(1.)
            latched=latest.get('state','').startswith('STOPPED') and latest['command'].twist.linear.x==0
            report['faults'].append({'mode':mode,'stop_request_delay_s':stop_request_delay,
                                     'physical_stop':stopped,'no_auto_restart':latched})
            enable(True)
            run(.8)
        enable(False)
        run(1.)
        if report['faults']:
            report['checks']['fault_stops'] = all(f['physical_stop'] and f['no_auto_restart'] and f['stop_request_delay_s']<.6 for f in report['faults'])
        report['checks']['explicit_disable'] = latest['command'].twist.linear.x==0 and abs(latest['truth'][1].angular.z)<.02
    except Exception as exc:
        report['error'] = str(exc)
    finally:
        try:
            if client.service_is_ready():
                enable(False)
        except Exception:
            pass
        report['samples'] = samples
        report['passed'] = 'error' not in report and bool(report['checks']) and all(report['checks'].values())
        output.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:v for k,v in report.items() if k not in ('samples','perception_events')},indent=2),flush=True)
        node.destroy_node(); rclpy.shutdown()
        if process.poll() is None:
            os.killpg(process.pid,signal.SIGINT)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL); process.wait(timeout=5)
        log.close()
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
