"""Drop the undriven chassis onto a plane using the existing mass budget."""

from pathlib import Path
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction, RegisterEventHandler
from launch.event_handlers import OnShutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

from racer_description.contact_world import build_world


def start(context):
    share = Path(get_package_share_directory("racer_description"))
    config = LaunchConfiguration("contact_config").perform(context)
    # Temporary resources live as long as Gazebo; the source geometry stays intact.
    directory = tempfile.TemporaryDirectory(prefix="odin_ground_contact_")
    path = Path(directory.name)/"ground_contact.world"
    path.write_text(build_world(share, config))

    def cleanup(context):
        directory.cleanup()
        return []

    gazebo = Path(get_package_share_directory("gazebo_ros"))
    return [
        RegisterEventHandler(OnShutdown(on_shutdown=[OpaqueFunction(function=cleanup)])),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(gazebo/"launch/gazebo.launch.py")),
            launch_arguments={"world": str(path), "gui": LaunchConfiguration("gui"),
                              "verbose": "true"}.items()),
    ]


def generate_launch_description():
    share = Path(get_package_share_directory("racer_description"))
    return LaunchDescription([
        DeclareLaunchArgument("gui", default_value="true"),
        DeclareLaunchArgument("contact_config", default_value=str(share/"config/ground_contact.yaml")),
        OpaqueFunction(function=start),
    ])
