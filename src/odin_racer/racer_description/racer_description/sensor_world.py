"""Shared Odin sensors, positioned from the URDF TF tree after fixed-link lumping."""

from pathlib import Path
import math
import xml.etree.ElementTree as ET

import numpy as np
import yaml

from .contact_world import element, pose, transform
from .fishpoly import FishPoly


def fixed_transform(robot, parent, child):
    """Transform a fixed descendant into parent coordinates; reject moving mounts."""
    joints = {j.find("child").get("link"): j for j in robot.findall("joint")}
    result, visited = np.eye(4), set()
    while child != parent:
        if child in visited or child not in joints:
            raise ValueError(f"No fixed path from {parent} to {child}")
        visited.add(child)
        joint = joints[child]
        if joint.get("type") != "fixed":
            raise ValueError("Sensor mount must be fixed to its physical body")
        result = transform(joint.find("origin")) @ result
        child = joint.find("parent").get("link")
    return result


def load_sensor_config(path):
    config = yaml.safe_load(Path(path).read_text())
    required = {
        "camera": {"calibration_file", "render_size", "env_texture_size", "rate_hz", "near_m", "far_m"},
        "lidar": {"horizontal_samples", "vertical_samples", "horizontal_fov_rad",
                  "vertical_fov_rad", "rate_hz", "near_m", "far_m", "resolution_m"},
        "imu": {"rate_hz"},
    }
    if not isinstance(config, dict) or set(config) != set(required):
        raise ValueError("Expected camera, lidar and imu sensor settings")
    for name, keys in required.items():
        values = config[name]
        if not isinstance(values, dict) or set(values) != keys:
            raise ValueError(f"Invalid {name} setting names")
        for key, value in values.items():
            if key == "calibration_file":
                if not isinstance(value, str) or not value:
                    raise ValueError("Expected calibration_file path")
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"Invalid positive sensor setting: {name}.{key}")
            if key in {"render_size", "env_texture_size", "horizontal_samples", "vertical_samples"} and (int(value) != value or value < 2):
                raise ValueError(f"Sensor dimension must be an integer >= 2: {key}")
        if "near_m" in values and values["far_m"] <= values["near_m"]:
            raise ValueError("Sensor far range must exceed near range")
    calibration = Path(path).resolve().parent/config["camera"]["calibration_file"]
    if not calibration.exists() and config["camera"]["calibration_file"] == "calib_device.yaml":
        # Source-tree use; CMake installs this exact canonical file beside config.
        calibration = Path(__file__).resolve().parents[4]/"hardware/mechanical/odin1/calib_device.yaml"
    config["camera"]["model"] = FishPoly.from_file(calibration)
    config["camera"]["calibration_file"] = str(calibration)
    for key in ("horizontal_fov_rad", "vertical_fov_rad"):
        if config["lidar"][key] > math.pi:
            raise ValueError("This forward ray model requires FOV <= pi")
    return config


def add_odin_sensors(link, robot, parent, config, namespace):
    """Attach three SDF sensors, with poses relative to the surviving body link."""
    for name, kind, frame, library in (
        ("lidar", "ray", "odin_sim_lidar", "ray_sensor"),
        ("camera", "wideanglecamera", "odin_sim_camera_optical", "camera"),
        ("imu", "imu", "odin_sim_imu", "imu_sensor"),
    ):
        params = config[name]
        sensor = element(link, "sensor", name="odin_"+name, type=kind)
        mount = fixed_transform(robot, parent, frame)
        if name == "camera":
            # Gazebo camera: X forward/Y left/Z up. ROS optical: Z forward/X right/Y down.
            optical_from_render = np.eye(4)
            optical_from_render[:3, :3] = [[0, -1, 0], [0, 0, -1], [1, 0, 0]]
            mount = mount @ optical_from_render
        element(sensor, "pose", pose(mount))
        element(sensor, "always_on", "true")
        element(sensor, "update_rate", params["rate_hz"])
        if name == "camera":
            camera = element(sensor, "camera")
            element(camera, "horizontal_fov", math.pi)
            image = element(camera, "image")
            for key in ("width", "height"):
                element(image, key, int(params["render_size"]))
            element(image, "format", "R8G8B8")
            clip = element(camera, "clip")
            element(clip, "near", params["near_m"])
            element(clip, "far", params["far_m"])
            lens = element(camera, "lens")
            element(lens, "type", "equidistant")
            element(lens, "scale_to_hfov", "true")
            element(lens, "cutoff_angle", math.pi/2)
            element(lens, "env_texture_size", int(params["env_texture_size"]))
        elif name == "lidar":
            ray = element(sensor, "ray")
            scan = element(ray, "scan")
            for direction in ("horizontal", "vertical"):
                axis = element(scan, direction)
                element(axis, "samples", int(params[direction+"_samples"]))
                element(axis, "resolution", 1)
                for key, sign in (("min_angle", -1), ("max_angle", 1)):
                    element(axis, key, sign*params[direction+"_fov_rad"]/2)
            limits = element(ray, "range")
            for key, setting in (("min", "near_m"), ("max", "far_m"), ("resolution", "resolution_m")):
                element(limits, key, params[setting])
        filename = "libodin_fishpoly_camera.so" if name == "camera" else f"libgazebo_ros_{library}.so"
        plugin = element(sensor, "plugin", name="odin_"+name, filename=filename)
        ros = element(plugin, "ros")
        element(ros, "namespace", namespace)
        element(plugin, "frame_name", frame)
        if name == "camera":
            model = params["model"]
            element(plugin, "width", model.width)
            element(plugin, "height", model.height)
            element(plugin, "intrinsics", " ".join(map(str, model.k.ravel())))
            element(plugin, "coefficients", " ".join(map(str, model.d)))
        else:
            element(ros, "remapping", "~/out:="+("cloud_raw" if name == "lidar" else "imu"))
        if name == "lidar":
            element(plugin, "output_type", "sensor_msgs/PointCloud2")
        if name == "imu":
            element(plugin, "initial_orientation_as_reference", "false")


def add_sensor_targets(world):
    """Optional known fixtures for sensor validation, not a competition course."""
    for name, location, size, color, collision in (
        ("sensor_target", "2 0 0.2 0 0 0", "0.1 0.3 0.4", "0.9 0.05 0.03 1", True),
        ("ground_marker", "0.8 0 0.001 0 0 0", "0.3 0.12 0.001", "0.02 0.02 0.9 1", False),
    ):
        model = element(world, "model", name=name)
        element(model, "static", "true")
        element(model, "pose", location)
        body = element(model, "link", name=name)
        for kind in (("visual", "collision") if collision else ("visual",)):
            shape = element(body, kind, name=name)
            element(element(element(shape, "geometry"), "box"), "size", size)
            if kind == "visual":
                material = element(shape, "material")
                element(material, "ambient", color)
                element(material, "diffuse", color)


def build_sensor_bench(share, robot_xml, sensor_config=None):
    """Populate the static bench template using the same URDF frames and settings."""
    share = Path(share)
    world = ET.parse(share/"worlds/odin_sensors.world").getroot()
    link = world.find("world/model[@name='odin_sensor_bench']/link")
    link.find("visual/geometry/mesh/uri").text = (share/"meshes/odin1.stl").resolve().as_uri()
    add_odin_sensors(link, ET.fromstring(robot_xml), "odin_bench_mount",
                     load_sensor_config(sensor_config or share/"config/odin_sensors.yaml"), "/sim/odin1")
    ET.indent(world)
    return ET.tostring(world, encoding="unicode")
