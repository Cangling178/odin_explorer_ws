"""Standalone stationary Odin sensor test; simulated topics use /sim/odin1."""
from pathlib import Path
import tempfile
import os
import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from racer_description.sensor_world import build_sensor_bench


def generate_launch_description():
    share = Path(get_package_share_directory('racer_description'))
    gazebo = Path(get_package_share_directory('gazebo_ros'))
    # Match the standalone SDF model pose. No duplicate base_link or full-robot TF.
    frames = f'''<robot xmlns:xacro="http://www.ros.org/wiki/xacro" name="odin_bench">
      <xacro:include filename="{share}/urdf/odin1_sensors.xacro"/>
      <link name="odin_sim_world"/><link name="odin_bench_mount"/>
      <joint name="bench_mount" type="fixed"><parent link="odin_sim_world"/>
        <child link="odin_bench_mount"/><origin xyz="0 0 0.5"/></joint>
      <xacro:odin_sensor_frames parent="odin_bench_mount"/>
    </robot>'''
    doc = xacro.parse(frames)
    xacro.process_doc(doc)
    fd, path = tempfile.mkstemp(prefix='odin_sensors_', suffix='.world')
    with os.fdopen(fd, 'w') as f:
        f.write(build_sensor_bench(share, doc.toxml()))
    def cleanup(context):
        Path(path).unlink(missing_ok=True)
        return []
    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(gazebo/'launch/gazebo.launch.py')),
            launch_arguments={'world': path, 'gui': LaunchConfiguration('gui'), 'verbose': 'false'}.items()),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             name='odin_bench_state_publisher', parameters=[{'robot_description': doc.toxml(), 'use_sim_time': True}]),
        RegisterEventHandler(OnShutdown(on_shutdown=[OpaqueFunction(function=cleanup)])),
    ])
