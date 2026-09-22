"""Manually moved ODIN mapping, optionally starting only the vendor SDK node."""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def vendor_node(context):
    if LaunchConfiguration('start_driver').perform(context) != 'true':
        return []
    if LaunchConfiguration('use_sim_time').perform(context) == 'true':
        raise ValueError('start_driver=true cannot be combined with use_sim_time=true')
    config = LaunchConfiguration('driver_config').perform(context)
    if not config:
        config = str(Path(get_package_share_directory('odin_ros_driver')) /
                     'config/control_command.yaml')
    return [Node(package='odin_ros_driver', executable='host_sdk_sample',
                 name='host_sdk_sample', output='screen', parameters=[{'config_file': config}])]


def generate_launch_description():
    share = Path(get_package_share_directory('explorer_bringup'))
    localization = Path(get_package_share_directory('explorer_localization'))
    return LaunchDescription([
        DeclareLaunchArgument('floor_z', description='Measured floor Z in mapping_frame, metres'),
        DeclareLaunchArgument('mapping_frame', default_value='odom'),
        DeclareLaunchArgument('start_driver', default_value='false', choices=['true', 'false']),
        DeclareLaunchArgument('driver_config', default_value='',
                              description='Optional vendor control_command.yaml path'),
        DeclareLaunchArgument('rviz', default_value='true', choices=['true', 'false']),
        DeclareLaunchArgument('use_sim_time', default_value='false', choices=['true', 'false']),
        OpaqueFunction(function=vendor_node),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(
            str(localization / 'launch/octomap.launch.py')),
            launch_arguments={'floor_z': LaunchConfiguration('floor_z'),
                              'mapping_frame': LaunchConfiguration('mapping_frame'),
                              'use_sim_time': LaunchConfiguration('use_sim_time')}.items()),
        Node(package='rviz2', executable='rviz2', name='mapping_rviz',
             condition=IfCondition(LaunchConfiguration('rviz')),
             parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
             arguments=['-d', str(share / 'rviz/mapping.rviz'),
                        '-f', LaunchConfiguration('mapping_frame')]),
    ])
