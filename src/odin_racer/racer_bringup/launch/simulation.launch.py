"""Simulation-only differential drive using ros2_control and the contact model."""

from pathlib import Path
import tempfile
import yaml
from racer_description.course_world import LINE_SCENES

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, EmitEvent, IncludeLaunchDescription, LogInfo, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node

from racer_description.drive_world import build_drive_resources


def start(context):
    share = Path(get_package_share_directory("racer_description"))
    directory = tempfile.TemporaryDirectory(prefix="odin_drive_")
    description, world = build_drive_resources(
        share, LaunchConfiguration("controllers").perform(context), directory.name,
        LaunchConfiguration("contact_config").perform(context),
        sensors=IfCondition(LaunchConfiguration("sensors")).evaluate(context),
        sensor_targets=IfCondition(LaunchConfiguration("sensor_targets")).evaluate(context),
        sensor_config=LaunchConfiguration("sensor_config").perform(context),
        course=LaunchConfiguration("course").perform(context),
        course_parameters=yaml.safe_load(LaunchConfiguration("course_parameters").perform(context)),
        course_overview=IfCondition(LaunchConfiguration("course_overview")).evaluate(context))

    def cleanup(context):
        directory.cleanup()
        return []

    def check_spawner(event, context):
        if event.returncode:
            return [EmitEvent(event=Shutdown(reason="Simulation controller activation failed"))]
        return [LogInfo(msg="Simulation controllers are active; waiting for stamped velocity commands.")]

    spawner = Node(package="controller_manager", executable="spawner",
                   arguments=["joint_state_broadcaster", "diff_drive_controller",
                              "--controller-manager", "/sim/racer/controller_manager",
                              "--controller-manager-timeout", "60", "--activate-as-group"],
                   output="screen")
    gazebo = Path(get_package_share_directory("gazebo_ros"))
    return [
        RegisterEventHandler(OnShutdown(on_shutdown=[OpaqueFunction(function=cleanup)])),
        Node(package="robot_state_publisher", executable="robot_state_publisher",
             namespace="/sim/racer", name="robot_state_publisher",
             parameters=[{"robot_description": description, "use_sim_time": True}],
             remappings=[("/tf", "/sim/racer/tf"), ("/tf_static", "/sim/racer/tf_static")], output="screen"),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(str(gazebo/"launch/gazebo.launch.py")),
                                 launch_arguments={"world": str(world), "gui": LaunchConfiguration("gui"),
                                                   "params_file": LaunchConfiguration("gazebo_params")}.items()),
        RegisterEventHandler(OnProcessExit(target_action=spawner, on_exit=check_spawner)),
        spawner,
    ]


def generate_launch_description():
    share = Path(get_package_share_directory("racer_description"))
    control = Path(get_package_share_directory("racer_control"))
    return LaunchDescription([
        DeclareLaunchArgument("gui", default_value="true"),
        DeclareLaunchArgument("gazebo_params", default_value=""),
        DeclareLaunchArgument("sensors", default_value="true", description="Enable onboard Odin sensor output"),
        DeclareLaunchArgument("sensor_targets", default_value="false", description="Add known sensor test fixtures"),
        DeclareLaunchArgument("sensor_config", default_value=str(share/"config/odin_sensors.yaml")),
        DeclareLaunchArgument("course", default_value="empty", choices=["empty", "competition", *LINE_SCENES],
                              description="Flat test world or competition drawing reconstruction"),
        DeclareLaunchArgument("course_parameters", default_value="{}"),
        DeclareLaunchArgument("course_overview", default_value="false",
                              description="Enable a fixed overhead inspection camera in the competition world"),
        DeclareLaunchArgument("controllers", default_value=str(control/"config/simulation_controllers.yaml")),
        DeclareLaunchArgument("contact_config", default_value=str(share/"config/ground_contact.yaml")),
        OpaqueFunction(function=start),
    ])
