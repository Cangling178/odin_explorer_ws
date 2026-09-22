"""电脑端：只启动 RViz；交互直接使用开源 Nav2 面板和目标工具。"""
from pathlib import Path
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    nav = Path(get_package_share_directory('explorer_navigation'))
    return LaunchDescription([
        DeclareLaunchArgument('config', default_value=str(nav / 'rviz/navigation_real.rviz')),
        Node(package='rviz2', executable='rviz2', name='navigation_rviz', output='screen',
             arguments=['-d', LaunchConfiguration('config')], parameters=[{'use_sim_time': False}]),
    ])
