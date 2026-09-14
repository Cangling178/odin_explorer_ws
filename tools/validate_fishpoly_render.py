#!/usr/bin/env python3
"""Render isolated angular targets at center, edges, corners and cubemap seams.

Launches and cleans up its own gzserver; no vehicle control. Run with a free ROS
domain and Gazebo master port (defaults 90/11389). Requires DISPLAY and built packages.
This deliberately removes housing/ground occlusion to test lens coverage alone.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

import cv2
import numpy as np
import rclpy
from ament_index_python.packages import get_package_prefix, get_package_share_directory
from sensor_msgs.msg import Image, CameraInfo

from racer_description.contact_world import element
from racer_description.sensor_world import add_odin_sensors, load_sensor_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/generated/fishpoly_render_validation.json'))
    parser.add_argument('--domain', type=int, default=90)
    parser.add_argument('--port', type=int, default=11389)
    args = parser.parse_args()
    # Never connect the test server to an existing Gazebo master.
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', args.port))
    os.environ['ROS_DOMAIN_ID'] = str(args.domain)
    env = dict(os.environ, GAZEBO_MASTER_URI=f'http://127.0.0.1:{args.port}')
    env['GAZEBO_PLUGIN_PATH'] = str(Path(get_package_prefix('racer_description'))/'lib')+os.pathsep+env.get('GAZEBO_PLUGIN_PATH', '')
    share = Path(get_package_share_directory('racer_description'))
    config = load_sensor_config(share/'config/odin_sensors.yaml')
    model = config['camera']['model']
    # Known angular directions cover the actual corners and both cube-face seams.
    uv = np.array([[12, 12], [1587, 12], [12, 1283], [1587, 1283],
                   [100, 648], [1499, 648], [800, 20], [800, 1275], [800, 648]], dtype=float)
    seam_rays = np.array([[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1]], dtype=float)
    uv = np.concatenate([uv, model.project(seam_rays)])
    # Inverse is tested separately against the vendor forward formula in unit tests.
    points = model.unproject(uv)*3
    root = ET.Element('sdf', version='1.6')
    world = element(root, 'world', name='fishpoly_angular_targets')
    scene = element(world, 'scene')
    element(scene, 'background', '0.2 0.2 0.2 1')
    element(scene, 'ambient', '1 1 1 1')
    physics = element(world, 'physics', type='ode')
    element(physics, 'max_step_size', .001)
    element(physics, 'real_time_update_rate', 1000)
    rig = element(world, 'model', name='rig')
    element(rig, 'static', 'true')
    link = element(rig, 'link', name='body')
    robot = ET.fromstring('<robot><link name="body"/>'+''.join(
        f'<joint name="{n}" type="fixed"><parent link="body"/><child link="odin_sim_{n}"/></joint>'
        for n in ('lidar', 'imu', 'camera_optical'))+'</robot>')
    add_odin_sensors(link, robot, 'body', config, '/sim/fishpoly_test')
    for sensor in list(link.findall('sensor')):
        if sensor.get('name') != 'odin_camera':
            link.remove(sensor)
    for index, point in enumerate(points):
        target = element(world, 'model', name=f'target_{index}')
        element(target, 'static', 'true')
        element(target, 'pose', ' '.join(map(str, point))+' 0 0 0')
        visual = element(element(target, 'link', name='body'), 'visual', name='target')
        element(element(element(visual, 'geometry'), 'sphere'), 'radius', .015)
        material = element(visual, 'material')
        element(material, 'ambient', '1 0 0 1')
        element(material, 'diffuse', '1 0 0 1')
        element(material, 'emissive', '1 0 0 1')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report = {'data_kind': 'simulation', 'expected_pixels': uv.tolist()}
    rclpy.init()
    node = rclpy.create_node('validate_fishpoly_render')
    latest = {}
    for key, kind in [('image', Image), ('camera_info', CameraInfo)]:
        node.create_subscription(kind, '/sim/fishpoly_test/'+key, lambda msg, k=key: latest.update({k: msg}), 5)
    with tempfile.TemporaryDirectory(prefix='fishpoly_render_') as directory:
        path = Path(directory)/'test.world'
        ET.ElementTree(root).write(path)
        with args.output.with_suffix('.log').open('w') as log:
            process = subprocess.Popen(['gzserver', str(path), '-slibgazebo_ros_init.so'],
                                       env=env, stdout=log, stderr=log, start_new_session=True)
            try:
                deadline = time.monotonic()+60
                while time.monotonic() < deadline:
                    rclpy.spin_once(node, timeout_sec=.1)
                    if len(latest) == 2 and latest['image'].header.stamp == latest['camera_info'].header.stamp:
                        break
                    if process.poll() is not None:
                        raise RuntimeError('gzserver exited; see log')
                else:
                    raise RuntimeError('No synchronized FishPoly image/info; see log')
                image, info = latest['image'], latest['camera_info']
                rgb = np.frombuffer(image.data, np.uint8).reshape(image.height, image.width, 3)
                mask = ((rgb[:, :, 0] > 120) & (rgb[:, :, 1] < 70) & (rgb[:, :, 2] < 70)).astype(np.uint8)
                count, _, stats, centers = cv2.connectedComponentsWithStats(mask)
                centers = centers[1:][stats[1:, cv2.CC_STAT_AREA] >= 4]
                if len(centers) != len(uv):
                    raise ValueError(f'Expected {len(uv)} angular targets, detected {len(centers)}')
                distances = np.linalg.norm(uv[:, None]-centers[None, :], axis=2)
                indices = distances.argmin(axis=1)
                errors = distances[np.arange(len(uv)), indices]
                report.update(observed_pixels=centers[indices].tolist(), errors_px=errors.tolist(),
                              max_error_px=float(errors.max()), checks={
                    'all_targets_unique': len(set(indices)) == len(uv),
                    'projection_within_2px': bool(np.all(errors < 2)),
                    'no_unrendered_black_pixels': not bool(np.any(np.max(rgb, axis=2) == 0)),
                    'device_metadata': info.distortion_model == 'fishpoly' and list(info.d) == list(model.d)
                        and np.array_equal(np.array(info.k).reshape(3, 3), model.k)
                        and image.width == info.width == model.width and image.height == info.height == model.height,
                    'same_stamp_and_frame': image.header == info.header,
                })
                cv2.imwrite(str(args.output.with_suffix('.png')), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
                report['passed'] = all(report['checks'].values())
            except (RuntimeError, ValueError) as exc:
                report.update(passed=False, error=str(exc))
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGINT)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
    node.destroy_node()
    rclpy.shutdown()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
