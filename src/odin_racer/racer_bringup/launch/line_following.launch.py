"""C++ single-branch visual tracking in simulation; explicit enable required."""
from pathlib import Path
from racer_description.course_world import LINE_SCENES
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, EnvironmentVariable
from launch_ros.actions import Node


def generate_launch_description():
    share = Path(get_package_share_directory('racer_bringup'))
    perception = Path(get_package_share_directory('racer_perception'))
    control = Path(get_package_share_directory('racer_control'))
    tf = [('/tf', LaunchConfiguration('tf_topic')), ('/tf_static', '/sim/racer/tf_static')]
    return LaunchDescription([
        DeclareLaunchArgument('gui', default_value='true'),
        DeclareLaunchArgument('lockstep', default_value='true'),
        DeclareLaunchArgument('dds_profile', default_value=EnvironmentVariable(
            'FASTRTPS_DEFAULT_PROFILES_FILE', default_value=str(share/'config/line_fastdds.xml'))),
        SetEnvironmentVariable('FASTRTPS_DEFAULT_PROFILES_FILE', LaunchConfiguration('dds_profile')),
        DeclareLaunchArgument('perception_config', default_value=str(perception/'config/line_perception.yaml')),
        DeclareLaunchArgument('controller_config', default_value=str(control/'config/line_controller.yaml')),
        DeclareLaunchArgument('odom_topic', default_value='/sim/racer/diff_drive_controller/odom'),
        DeclareLaunchArgument('tf_topic', default_value='/sim/racer/tf'),
        DeclareLaunchArgument('image_topic', default_value='/sim/racer/odin1/image'),
        DeclareLaunchArgument('course_parameters', default_value='{}'),
        DeclareLaunchArgument('course', default_value='competition',
                              choices=['competition', *LINE_SCENES]),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(share/'launch/simulation.launch.py')),
                                 launch_arguments={'gui': LaunchConfiguration('gui'),
                                                   'lockstep': LaunchConfiguration('lockstep'),
                                                   'course': LaunchConfiguration('course'),
                                                   'course_parameters': LaunchConfiguration('course_parameters'),
                                                   'gazebo_params': str(control/'config/line_sim_clock.yaml')}.items()),
        Node(package='racer_perception', executable='line_perception', namespace='/sim/racer/line',
             parameters=[LaunchConfiguration('perception_config'), {'use_sim_time': True}], output='screen',
             remappings=tf+[('image', LaunchConfiguration('image_topic')),
                            ('camera_info', '/sim/racer/odin1/camera_info')]),
        Node(package='racer_control', executable='line_controller', namespace='/sim/racer/line',
             parameters=[LaunchConfiguration('controller_config'), {'use_sim_time': True}], output='screen',
             remappings=tf+[('odom', LaunchConfiguration('odom_topic')),
                            ('cmd_vel', '/sim/racer/diff_drive_controller/cmd_vel')]),
    ])
