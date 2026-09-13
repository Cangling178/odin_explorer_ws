"""Publish a stationary illustrative model without any actuator connection."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    model = Path(get_package_share_directory("racer_description")) / "urdf" / "robot.urdf.xacro"
    description = xacro.process_file(str(model)).toxml()
    use_sim_time = LaunchConfiguration("use_sim_time")
    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="false"),
        DeclareLaunchArgument("rviz", default_value="true"),
        Node(package="rviz2", executable="rviz2",
             arguments=["-d", str(model.parent.parent / "config" / "preview.rviz")],
             condition=IfCondition(LaunchConfiguration("rviz")),
             parameters=[{"use_sim_time": use_sim_time}], output="screen"),
        Node(package="robot_state_publisher", executable="robot_state_publisher",
             parameters=[{"robot_description": description, "use_sim_time": use_sim_time}],
             output="screen"),
        Node(package="joint_state_publisher", executable="joint_state_publisher",
             parameters=[{"robot_description": description, "use_sim_time": use_sim_time}],
             output="screen"),
    ])
