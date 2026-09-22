"""ODIN sensor-frame clouds to an online occupancy grid; no TF publication."""
import math
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def mapping_nodes(context):
    def value(name):
        return LaunchConfiguration(name).perform(context)

    floor = float(value('floor_z'))
    height = float(value('obstacle_height'))
    clearance = float(value('ground_clearance'))
    resolution = float(value('resolution'))
    if not all(math.isfinite(v) for v in (floor, height, clearance, resolution)):
        raise ValueError('Mapping heights and resolution must be finite')
    if not 0.0 <= clearance < height or resolution <= 0.0:
        raise ValueError('Require 0 <= ground_clearance < obstacle_height and resolution > 0')
    simulated = value('use_sim_time').lower() == 'true'
    config = value('params_file')
    gate = Node(
        package='explorer_localization', executable='odin_cloud_gate', name='odin_cloud_gate',
        output='screen', parameters=[config, {'use_sim_time': simulated, 'map_frame': value('mapping_frame')}],
        remappings=[('cloud_in', value('cloud_topic')),
                    ('points', '/sensors/odin/points'), ('status', '/mapping/status')])
    server = Node(
        package='octomap_server', executable='octomap_server_node', name='octomap_server',
        output='screen', parameters=[config, {
            'use_sim_time': simulated, 'resolution': resolution,
            'frame_id': value('mapping_frame'),
            'point_cloud_min_z': floor - resolution,
            'point_cloud_max_z': floor + height + resolution,
            'occupancy_min_z': floor + clearance,
            'occupancy_max_z': floor + height,
        }], remappings=[('cloud_in', '/sensors/odin/points'), ('projected_map', '/map')])
    # An exited mapper/gateway must not leave the other half running unnoticed.
    handlers = [RegisterEventHandler(OnProcessExit(
        target_action=node, on_exit=[EmitEvent(event=Shutdown(reason='Mapping process exited'))]))
        for node in (gate, server)]
    return [*handlers, gate, server]


def generate_launch_description():
    share = Path(get_package_share_directory('explorer_localization'))
    return LaunchDescription([
        DeclareLaunchArgument('floor_z', description='Measured floor Z in mapping_frame, metres'),
        DeclareLaunchArgument('mapping_frame', default_value='odom',
                              description='Fixed occupancy frame; vendor mapping mode supplies odom'),
        DeclareLaunchArgument('obstacle_height', default_value='1.0',
                              description='Maximum obstacle height above floor; set to robot envelope'),
        DeclareLaunchArgument('ground_clearance', default_value='0.08',
                              description='Exclude the floor band from 2D projection (metres)'),
        DeclareLaunchArgument('resolution', default_value='0.05'),
        DeclareLaunchArgument('cloud_topic', default_value='/odin1/cloud_raw',
                              description='Current-frame PointCloud2 expressed in lidar frame'),
        DeclareLaunchArgument('params_file', default_value=str(share / 'config/octomap.yaml')),
        DeclareLaunchArgument('use_sim_time', default_value='false', choices=['true', 'false']),
        OpaqueFunction(function=mapping_nodes),
    ])
