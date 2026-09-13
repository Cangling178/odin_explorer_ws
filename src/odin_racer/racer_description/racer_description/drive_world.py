"""Generate ros2_control resources from the same geometry as the contact model."""

from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import xacro
import yaml

from .contact_world import build_world, element
from .sensor_world import add_odin_sensors, add_sensor_targets, load_sensor_config


def build_drive_resources(share, controller_config, output_directory, contact_config=None,
                          sensors=True, sensor_targets=False, sensor_config=None):
    share, output = Path(share), Path(output_directory)
    robot_xml = xacro.process_file(str(share/"urdf/robot.urdf.xacro"), mappings={"sim_control": "true"}).toxml()
    robot = ET.fromstring(robot_xml)
    params = yaml.safe_load(Path(controller_config).read_text())
    drive = params["/sim/racer/diff_drive_controller"]["ros__parameters"]
    origins, radii = [], []
    for side in ("left", "right"):
        joint = robot.find(f"joint[@name='{side}_wheel_joint']")
        origins.append(np.array([float(v) for v in joint.find("origin").get("xyz").split()]))
        wheel = robot.find(f"link[@name='{side}_wheel_link']/collision/geometry/cylinder")
        radii.append(float(wheel.get("radius")))
    if not np.isclose(radii[0], radii[1]) or not np.allclose((origins[0]-origins[1])[[0, 2]], 0):
        raise ValueError("Expected equal-radius, coaxial rear wheels")
    drive["wheel_separation"] = float(origins[0][1]-origins[1][1])
    drive["wheel_radius"] = radii[0]
    if drive["wheel_separation"] <= 0:
        raise ValueError("Left wheel must be on positive Y")
    # Worst-case simultaneous v/w commands must fit both joint speed limits.
    max_v = max(abs(drive["linear.x.max_velocity"]), abs(drive["linear.x.min_velocity"]))
    max_w = max(abs(drive["angular.z.max_velocity"]), abs(drive["angular.z.min_velocity"]))
    required = (max_v+max_w*drive["wheel_separation"]*drive.get("wheel_separation_multiplier", 1.)/2)/radii[0]
    for side in ("left", "right"):
        limit = float(robot.find(f"joint[@name='{side}_wheel_joint']/limit").get("velocity"))
        if required > limit:
            raise ValueError("Configured body speed limits exceed wheel velocity limits")
    config_file = output/"controllers.yaml"
    config_file.write_text(yaml.safe_dump(params))
    sdf = ET.fromstring(build_world(share, contact_config, robot_xml))
    model = sdf.find("world/model[@name='odin_racer']")
    if sensors:
        add_odin_sensors(model.find("link[@name='base_link']"), robot, "base_link",
                         load_sensor_config(sensor_config or share/"config/odin_sensors.yaml"),
                         "/sim/racer/odin1")
    if sensor_targets:
        add_sensor_targets(sdf.find("world"))
    plugin = element(model, "plugin", name="gazebo_ros2_control", filename="libgazebo_ros2_control.so")
    element(plugin, "robot_param", "robot_description")
    element(plugin, "robot_param_node", "/sim/racer/robot_state_publisher")
    element(plugin, "parameters", str(config_file))
    ros = element(plugin, "ros")
    element(ros, "namespace", "/sim/racer")
    element(ros, "remapping", "/tf:=/sim/racer/tf")
    element(ros, "remapping", "/tf_static:=/sim/racer/tf_static")
    ET.indent(sdf)
    world_file = output/"drive.world"
    world_file.write_text(ET.tostring(sdf, encoding="unicode"))
    return robot_xml, world_file
