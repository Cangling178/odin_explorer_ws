#!/usr/bin/env python3
"""Validate a fresh course=competition, course_overview=true, sensors=true world.

Actively drives 0.08 m/s for 1.5 simulated seconds and stops. Use an isolated ROS
domain with no other command publisher. Needs python3-opencv and rendering.
Compares rendered pixels to the reconstructed texture, NOT to a surveyed course.
"""

import argparse
import hashlib
import json
from pathlib import Path
import time

import cv2
import numpy as np
import rclpy
from ament_index_python.packages import get_package_share_directory
from gazebo_msgs.msg import LinkStates
from geometry_msgs.msg import TwistStamped
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import Image, CameraInfo, Imu, PointCloud2
from tf2_ros import Buffer, TransformException, TransformListener
import yaml

from validate_sim_sensors import cloud_xyz, matrix, stamp
from racer_description.fishpoly import pixel_rays


def pixels(msg):
    if msg.encoding != 'rgb8':
        raise ValueError('Expected rgb8')
    return np.frombuffer(msg.data, np.uint8).reshape(msg.height, msg.step)[:, :msg.width*3].reshape(msg.height, msg.width, 3)


def compare_ground(image, info, world_from_camera, texture, config, base, overview):
    """Ray/plane projection; compare only board pixels with a useful view angle."""
    rows, cols = np.mgrid[0:image.height:2, 0:image.width:2]
    uv = np.stack([cols, rows], axis=-1)
    rays = pixel_rays(info, uv) @ world_from_camera[:3, :3].T
    origin = world_from_camera[:3, 3]
    distance = (config['visual_z_m']-origin[2])/np.where(np.abs(rays[:, :, 2]) > 1e-8, rays[:, :, 2], 1e-8)
    ground = origin+rays*distance[:, :, None]
    x, y = ground[:, :, 0], ground[:, :, 1]
    bx, by = config['board_size_m']
    valid = (distance > 0) & (np.abs(x) < bx/2-.015) & (np.abs(y) < by/2-.015)
    if overview:
        # Exclude vehicle and its shadow; do not exclude the rest of the course.
        valid &= ~((x > base[0]-.15) & (x < base[0]+.4) & (np.abs(y-base[1]) < .23))
    else:
        valid &= (x > base[0]+.25) & (np.hypot(x-origin[0], y-origin[1]) < 1.)
    tx = np.clip(((x/bx+.5)*texture.shape[1]).astype(int), 0, texture.shape[1]-1)
    ty = np.clip(((.5-y/by)*texture.shape[0]).astype(int), 0, texture.shape[0]-1)
    expected = texture[ty, tx] < 128
    gray = pixels(image)[::2, ::2].mean(axis=2)
    # Determine contrast from expected interiors, so lighting may vary without
    # accepting a missing texture, reversed polarity or a mirrored course.
    black = float(np.median(gray[valid & expected])) if np.any(valid & expected) else 255.
    white = float(np.median(gray[valid & ~expected])) if np.any(valid & ~expected) else 0.
    observed = gray < (black+white)/2
    intersection = int(np.count_nonzero(valid & expected & observed))
    union = int(np.count_nonzero(valid & (expected | observed)))
    return {'black_iou': intersection/max(union, 1), 'sampled_black_pixels': int(np.count_nonzero(valid & expected)),
            'sampled_board_pixels': int(np.count_nonzero(valid)), 'black_gray': black, 'white_gray': white}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('data/generated/competition_course_validation.json'))
    args = parser.parse_args()
    share = Path(get_package_share_directory('racer_description'))
    config = yaml.safe_load((share/'config/competition_course.yaml').read_text())
    texture_path = share/'meshes/competition_course/course.png'
    texture = cv2.imread(str(texture_path), cv2.IMREAD_GRAYSCALE)
    if texture is None:
        raise ValueError('Installed course texture missing')
    rclpy.init()
    node = rclpy.create_node('validate_competition_course', parameter_overrides=[Parameter('use_sim_time', value=True)],
                             cli_args=['--ros-args', '-r', '/tf:=/sim/racer/tf', '-r', '/tf_static:=/sim/racer/tf_static'])
    buffer = Buffer(node=node)
    listener = TransformListener(buffer, node)
    publisher = node.create_publisher(TwistStamped, '/sim/racer/diff_drive_controller/cmd_vel', 1)
    latest, times = {}, {}
    report = {'data_kind': 'simulation', 'course': config, 'checks': {}, 'snapshots': []}
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def now():
        return node.get_clock().now().nanoseconds*1e-9

    def receive(key, msg):
        latest[key] = msg
        times.setdefault(key, []).append(stamp(msg))

    for key, kind, topic, qos in (
            ('image', Image, '/sim/racer/odin1/image', 5),
            ('info', CameraInfo, '/sim/racer/odin1/camera_info', 5),
            ('cloud', PointCloud2, '/sim/racer/odin1/cloud_raw', qos_profile_sensor_data),
            ('imu', Imu, '/sim/racer/odin1/imu', qos_profile_sensor_data),
            ('overview', Image, '/sim/course/overview/image', 5),
            ('overview_info', CameraInfo, '/sim/course/overview/camera_info', 5)):
        node.create_subscription(kind, topic, lambda msg, k=key: receive(k, msg), qos)

    def truth(msg):
        if 'odin_racer::base_link' in msg.name:
            i = msg.name.index('odin_racer::base_link')
            latest['truth'] = (msg.pose[i], msg.twist[i])
    node.create_subscription(LinkStates, '/contact_test/link_states', truth, qos_profile_sensor_data)

    def command(speed=0.):
        msg = TwistStamped()
        msg.header.stamp = node.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.twist.linear.x = speed
        publisher.publish(msg)

    def run(duration, speed=0.):
        start, wall, last = now(), time.monotonic(), -1.
        while now()-start < duration:
            if time.monotonic()-wall > max(30., duration*15):
                raise RuntimeError('Simulation stalled')
            rclpy.spin_once(node, timeout_sec=.005)
            if now()-last > .02:
                command(speed)
                last = now()

    def snapshot(name):
        p, velocity = latest['truth']
        base = np.array([p.position.x, p.position.y, p.position.z])
        if np.linalg.norm([velocity.linear.x, velocity.linear.y, velocity.linear.z]) > .005:
            raise ValueError('Snapshot requires a stopped vehicle')
        world_from_base = matrix(p.position, p.orientation)
        def sensor_transform(msg):
            tf = buffer.lookup_transform('base_link', msg.header.frame_id, Time.from_msg(msg.header.stamp)).transform
            buffer.lookup_transform('odom', msg.header.frame_id, Time.from_msg(msg.header.stamp))
            return world_from_base @ matrix(tf.translation, tf.rotation)
        # Fixed overhead optical axes: right=+X, down=-Y, forward=-Z.
        observer = np.diag([1., -1., -1., 1.])
        observer[2, 3] = 3.
        overview = compare_ground(latest['overview'], latest['overview_info'], observer, texture, config, base, True)
        onboard = compare_ground(latest['image'], latest['info'], sensor_transform(latest['image']), texture, config, base, False)
        cloud = cloud_xyz(latest['cloud'])
        tf = sensor_transform(latest['cloud'])
        points = cloud @ tf[:3, :3].T+tf[:3, 3]
        ground = points[(np.abs(points[:, 0]) < .98) & (np.abs(points[:, 1]) < .73) & (points[:, 0] > base[0]+.3)]
        ground_error = float(np.percentile(np.abs(ground[:, 2]), 95)) if len(ground) else 1.
        imu = latest['imu']
        checks = {
            'overview_matches_texture': overview['black_iou'] > .85 and overview['sampled_black_pixels'] > 1000,
            'onboard_black_line_projection': onboard['black_iou'] > .70 and onboard['sampled_black_pixels'] > 1000,
            'visible_contrast': all(m['white_gray']-m['black_gray'] > 80 for m in (overview, onboard)),
            'cloud_sees_flat_floor': len(ground) > 100 and ground_error < .01,
            'imu_stationary_gravity': abs(imu.linear_acceleration.z-9.81) < .1 and abs(imu.angular_velocity.z) < .02,
            'fresh_sensors': all(abs(now()-stamp(latest[k])) < .7 for k in times),
            'image_info_agree': latest['image'].width == latest['info'].width == 1600
                                and latest['image'].height == latest['info'].height == 1296,
        }
        result = {'name': name, 'base_xyz_m': base.tolist(), 'overview': overview, 'onboard': onboard,
                  'cloud_ground_points': len(ground), 'cloud_ground_p95_error_m': ground_error,
                  'checks': {k: bool(v) for k, v in checks.items()}}
        for key in ('image', 'overview'):
            path = args.output.parent/(args.output.stem+'_'+name+'_'+key+'.png')
            if not cv2.imwrite(str(path), cv2.cvtColor(pixels(latest[key]), cv2.COLOR_RGB2BGR)):
                raise ValueError('Failed to save image')
            result[key+'_path'] = str(path)
        report['snapshots'].append(result)
        print(json.dumps(result), flush=True)

    try:
        deadline = time.monotonic()+45
        while len(latest) < 7 or now() == 0:
            if time.monotonic() > deadline:
                raise RuntimeError('Missing sensors/overview/clock/truth: check fresh competition launch and rendering')
            rclpy.spin_once(node, timeout_sec=.1)
        p = latest['truth'][0].position
        if np.hypot(p.x-config['spawn_x_m'], p.y-config['spawn_y_m']) > .03:
            raise ValueError('Restart at the configured competition spawn before validation')
        if node.count_publishers('/sim/racer/diff_drive_controller/cmd_vel') != 1:
            raise ValueError('Another command publisher is active')
        run(1.5)
        times.clear()
        wall_start, sim_start = time.monotonic(), now()
        run(1.)
        snapshot('stationary')
        run(1.5, .08)
        run(1.5)
        snapshot('after_forward')
        delta = np.array(report['snapshots'][1]['base_xyz_m'])-report['snapshots'][0]['base_xyz_m']
        # Measure reception without expensive image projection/PNG saving in the
        # callback thread; otherwise depth-5 IMU samples drop during offline work.
        run(.5)
        times.clear()
        run(3.)
        rates = {k: (len(ts)-1)/(ts[-1]-ts[0]) for k, ts in times.items() if len(ts) > 1}
        report['checks'] = {
            'installed_texture_hash': hashlib.sha256(texture_path.read_bytes()).hexdigest() == config['texture_sha256'],
            'short_forward_motion': bool(.07 < delta[0] < .16 and abs(delta[1]) < .01),
            'sensor_rates': len(rates) == 6 and all(.8*expected < rates.get(k, 0) < 1.2*expected
                           for k, expected in (('image', 10), ('info', 10), ('cloud', 10), ('imu', 400), ('overview', 2), ('overview_info', 2))),
            'increasing_stamps': all(all(b > a for a, b in zip(ts, ts[1:])) for ts in times.values()),
        }
        report.update(received_rates_per_sim_second=rates, forward_delta_m=delta.tolist(),
                      real_time_factor=(now()-sim_start)/(time.monotonic()-wall_start))
        report['passed'] = all(report['checks'].values()) and all(all(s['checks'].values()) for s in report['snapshots'])
    except (RuntimeError, ValueError, TransformException) as exc:
        report.update(passed=False, error=str(exc))
    finally:
        for _ in range(5):
            command()
            rclpy.spin_once(node, timeout_sec=.02)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
        node.destroy_node()
        rclpy.shutdown()
    print(json.dumps(report), flush=True)
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
