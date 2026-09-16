"""Continuous image-map assisted lap; explicit enable, wheel odometry, onboard vision."""
from pathlib import Path
import json
import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    bringup=Path(get_package_share_directory('racer_bringup'))
    control=Path(get_package_share_directory('racer_control'))
    perception=Path(get_package_share_directory('racer_perception'))
    spawn=json.loads((control/'config/competition_lap.json').read_text())['spawn']
    grid=yaml.safe_load((perception/'config/line_perception.yaml').read_text())['/**']['ros__parameters']
    tf=[('/tf','/sim/racer/tf'),('/tf_static','/sim/racer/tf_static')]
    return LaunchDescription([
        DeclareLaunchArgument('gui',default_value='true'),
        DeclareLaunchArgument('speed',default_value='0.05'),
        DeclareLaunchArgument('lookahead',default_value='0.10'),
        SetEnvironmentVariable('FASTRTPS_DEFAULT_PROFILES_FILE',str(bringup/'config/line_fastdds.xml')),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(bringup/'launch/simulation.launch.py')),
            launch_arguments={'gui':LaunchConfiguration('gui'),'lockstep':'true','course':'competition',
                'course_parameters':json.dumps(dict(scale=2.,line_width=.02116,spawn_x=spawn[0],spawn_y=spawn[1],spawn_yaw=spawn[2])),
                'gazebo_params':str(control/'config/line_sim_clock.yaml')}.items()),
        Node(package='racer_perception',executable='line_perception',namespace='/sim/racer/line',output='screen',
            parameters=[str(perception/'config/line_perception.yaml'),{'use_sim_time':True}],
            remappings=tf+[('image','/sim/racer/odin1/image'),('camera_info','/sim/racer/odin1/camera_info')]),
        Node(package='racer_control',executable='lap_controller',namespace='/sim/racer/line',output='screen',
            parameters=[{key:grid[key] for key in ('near_x','far_x','half_width','grid_step')}, {'use_sim_time':True,'route_file':str(control/'config/competition_lap.csv'),
                'start_x':spawn[0],'start_y':spawn[1],'start_yaw':spawn[2],
                'speed':LaunchConfiguration('speed'),'lookahead':LaunchConfiguration('lookahead')}],
            remappings=tf+[('odom','/sim/racer/diff_drive_controller/odom'),('cmd_vel','/sim/racer/diff_drive_controller/cmd_vel')]),
    ])
