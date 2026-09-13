"""Prepare a three-body contact test from the source URDF without invented mass.

Fixed descendants are explicitly lumped into their nearest moving ancestor.
This keeps massless CAD/pillar/shaft collision geometry, transforms each tensor
to its body axes, and uses the parallel-axis theorem about the combined COM.
The output is simulation-only SDF; the source URDF and its TF tree are untouched.
"""

from copy import deepcopy
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import xacro
import yaml


def element(parent, tag, value=None, **attributes):
    node = ET.SubElement(parent, tag, attributes)
    if value is not None:
        node.text = str(value)
    return node


def numbers(values):
    return " ".join(f"{v:.16g}" for v in values)


def transform(origin):
    result = np.eye(4)
    if origin is None:
        return result
    result[:3, 3] = [float(v) for v in origin.get("xyz", "0 0 0").split()]
    r, p, y = [float(v) for v in origin.get("rpy", "0 0 0").split()]
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    result[:3, :3] = [[cy*cp, cy*sp*sr-sy*cr, cy*sp*cr+sy*sr],
                       [sy*cp, sy*sp*sr+cy*cr, sy*sp*cr-cy*sr],
                       [-sp, cp*sr, cp*cr]]
    return result


def pose(matrix):
    rotation = matrix[:3, :3]
    pitch = math.atan2(-rotation[2, 0], math.hypot(rotation[0, 0], rotation[1, 0]))
    if abs(math.cos(pitch)) > 1e-10:
        roll = math.atan2(rotation[2, 1], rotation[2, 2])
        yaw = math.atan2(rotation[1, 0], rotation[0, 0])
    else:
        roll = math.atan2(-rotation[1, 2], rotation[1, 1])
        yaw = 0.0
    return numbers([*matrix[:3, 3], roll, pitch, yaw])


def load_config(path):
    config = yaml.safe_load(Path(path).read_text())
    def check(node):
        for key, value in node.items():
            if isinstance(value, dict):
                check(value)
            elif isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"Invalid nonnegative contact setting: {key}")
    check(config)
    for key in ("step_size_s", "update_rate_hz", "solver_iterations"):
        if config["physics"][key] <= 0:
            raise ValueError(f"{key} must be positive")
    for value in (config["physics"]["solver_iterations"], config["contact"]["max_contacts"]):
        if int(value) != value or value < 1:
            raise ValueError("Solver iterations and max_contacts must be positive integers")
    if config["contact"]["stiffness_n_per_m"] <= 0:
        raise ValueError("Contact stiffness must be positive")
    return config


def surface(collision, config, mu):
    contact = config["contact"]
    element(collision, "max_contacts", contact["max_contacts"])
    node = element(collision, "surface")
    element(element(node, "bounce"), "restitution_coefficient", 0)
    friction = element(element(node, "friction"), "ode")
    for key in ("mu", "mu2"):
        element(friction, key, mu)
    for key in ("slip1", "slip2"):
        element(friction, key, 0)
    ode = element(element(node, "contact"), "ode")
    for key, value in {"kp": contact["stiffness_n_per_m"], "kd": contact["damping_ns_per_m"],
                       "min_depth": contact["min_depth_m"], "max_vel": contact["max_correcting_velocity_mps"]}.items():
        element(ode, key, value)


def aggregate(entries):
    """Return mass, COM, and tensor about COM from (mass, COM, tensor) entries."""
    mass = sum(entry[0] for entry in entries)
    if mass <= 0:
        raise ValueError("Every dynamic body requires existing positive mass")
    center = sum(m*c for m, c, _ in entries) / mass
    tensor = np.zeros((3, 3))
    for m, c, inertia in entries:
        delta = c-center
        tensor += inertia + m*(np.dot(delta, delta)*np.eye(3)-np.outer(delta, delta))
    moments = np.linalg.eigvalsh(tensor)
    if not np.isfinite(tensor).all() or moments[0] <= 0 or moments[2] > moments[0]+moments[1]+1e-12:
        raise ValueError("Invalid aggregated inertia")
    return mass, center, tensor


def build_world(share, config_path=None, robot_xml=None):
    share = Path(share)
    config = load_config(config_path or share/"config/ground_contact.yaml")
    robot = ET.fromstring(robot_xml or xacro.process_file(str(share/"urdf/robot.urdf.xacro")).toxml())
    links = {link.get("name"): link for link in robot.findall("link")}
    joints = robot.findall("joint")
    roots = set(links)-{j.find("child").get("link") for j in joints}
    if roots != {"base_link"}:
        raise ValueError("Expected a single base_link root")
    # Link transforms in model coordinates and rigid-body ownership.
    transforms = {"base_link": np.eye(4)}
    owners = {"base_link": "base_link"}
    pending = list(joints)
    while pending:
        count = len(pending)
        for joint in pending[:]:
            parent, child = joint.find("parent").get("link"), joint.find("child").get("link")
            if parent not in transforms:
                continue
            kind = joint.get("type")
            if kind not in ("fixed", "continuous"):
                raise ValueError(f"Unsupported joint: {joint.get('name')} ({kind})")
            transforms[child] = transforms[parent] @ transform(joint.find("origin"))
            owners[child] = owners[parent] if kind == "fixed" else child
            pending.remove(joint)
        if len(pending) == count:
            raise ValueError("Invalid joint tree")
    sdf = ET.Element("sdf", version="1.6")
    world = element(sdf, "world", name="ground_contact")
    element(world, "gravity", "0 0 -9.81")
    physics = element(world, "physics", name="contact_ode", type="ode")
    element(physics, "max_step_size", config["physics"]["step_size_s"])
    element(physics, "real_time_update_rate", config["physics"]["update_rate_hz"])
    ode = element(physics, "ode")
    solver = element(ode, "solver")
    for key, value in {"type": "quick", "iters": config["physics"]["solver_iterations"],
                       "sor": config["physics"]["sor"], "friction_model": "pyramid_model"}.items():
        element(solver, key, value)
    constraints = element(ode, "constraints")
    element(constraints, "contact_surface_layer", config["contact"]["min_depth_m"])
    element(constraints, "contact_max_correcting_vel", config["contact"]["max_correcting_velocity_mps"])
    light = element(world, "light", name="sun", type="directional")
    element(light, "pose", "0 0 10 0 0 0")
    element(light, "diffuse", "0.8 0.8 0.8 1")
    element(light, "direction", "-0.5 0 -1")
    floor = element(world, "model", name="floor")
    element(floor, "static", "true")
    floor_link = element(floor, "link", name="floor")
    for kind in ("collision", "visual"):
        node = element(floor_link, kind, name="floor")
        plane = element(element(node, "geometry"), "plane")
        element(plane, "normal", "0 0 1")
        element(plane, "size", "20 20")
        if kind == "collision":
            surface(node, config, config["friction"]["ground"])
    plugin = element(world, "plugin", name="contact_state", filename="libgazebo_ros_state.so")
    element(element(plugin, "ros"), "namespace", "/contact_test")
    element(plugin, "update_rate", 100)
    model = element(world, "model", name="odin_racer")
    element(model, "static", "false")
    element(model, "self_collide", "false")
    bodies, entries = {}, {}
    for owner in dict.fromkeys(owners.values()):
        bodies[owner] = element(model, "link", name=owner)
        element(bodies[owner], "pose", pose(transforms[owner]))
        entries[owner] = []
    materials = {m.get("name"): m.find("color").get("rgba") for m in robot.findall("material")}
    lowest = math.inf
    for name, link in links.items():
        owner = owners[name]
        relative = np.linalg.inv(transforms[owner]) @ transforms[name]
        inertial = link.find("inertial")
        if inertial is not None:
            frame = relative @ transform(inertial.find("origin"))
            mass = float(inertial.find("mass").get("value"))
            if not math.isfinite(mass) or mass <= 0:
                raise ValueError(f"Invalid mass in {name}")
            a = {k: float(v) for k, v in inertial.find("inertia").attrib.items()}
            tensor = np.array([[a['ixx'], a['ixy'], a['ixz']], [a['ixy'], a['iyy'], a['iyz']], [a['ixz'], a['iyz'], a['izz']]])
            entries[owner].append((mass, frame[:3, 3], frame[:3, :3] @ tensor @ frame[:3, :3].T))
        for kind in ("visual", "collision"):
            for index, source in enumerate(link.findall(kind)):
                target = element(bodies[owner], kind, name=f"{name}_{source.get('name', kind+str(index))}")
                local = transform(source.find("origin"))
                element(target, "pose", pose(relative @ local))
                geometry = deepcopy(source.find("geometry"))
                target.append(geometry)
                shape = list(geometry)[0]
                attributes = dict(shape.attrib)
                shape.attrib.clear()
                for key, value in attributes.items():
                    if key == "filename":
                        prefix = "package://racer_description/"
                        if not value.startswith(prefix):
                            raise ValueError(f"Unsupported mesh URI: {value}")
                        key, value = "uri", (share/value[len(prefix):]).resolve().as_uri()
                    element(shape, key, value)
                if kind == "visual":
                    material = source.find("material")
                    if material is not None:
                        color = material.find("color")
                        rgba = color.get("rgba") if color is not None else materials.get(material.get("name"))
                        if rgba:
                            target_material = element(target, "material")
                            element(target_material, "ambient", rgba)
                            element(target_material, "diffuse", rgba)
                else:
                    # Friction is assigned BEFORE lumping so balls keep their own surface.
                    friction = "tire" if name in ("left_wheel_link", "right_wheel_link") else "body"
                    if source.get("name") in ("left_ball_collision", "right_ball_collision"):
                        friction = "ball"
                    surface(target, config, config["friction"][friction])
                    frame = transforms[name] @ local
                    zrow = frame[2, :3]
                    if shape.tag == "box":
                        extent = np.abs(zrow) @ np.array([float(v) for v in attributes["size"].split()])/2
                    elif shape.tag == "sphere":
                        extent = float(attributes["radius"])
                    elif shape.tag == "cylinder":
                        extent = abs(zrow[2])*float(attributes["length"])/2 + math.hypot(*zrow[:2])*float(attributes["radius"])
                    else:
                        raise ValueError("Contact world requires primitive collision geometry")
                    lowest = min(lowest, frame[2, 3]-extent)
    for owner, body in bodies.items():
        mass, center, tensor = aggregate(entries[owner])
        inertial = element(body, "inertial")
        element(inertial, "mass", mass)
        element(inertial, "pose", numbers([*center, 0, 0, 0]))
        inertia = element(inertial, "inertia")
        for key, i, j in (("ixx", 0, 0), ("iyy", 1, 1), ("izz", 2, 2), ("ixy", 0, 1), ("ixz", 0, 2), ("iyz", 1, 2)):
            element(inertia, key, tensor[i, j])
    for joint in joints:
        if joint.get("type") == "fixed":
            continue
        node = element(model, "joint", name=joint.get("name"), type="revolute")
        element(node, "parent", owners[joint.find("parent").get("link")])
        element(node, "child", joint.find("child").get("link"))
        # SDF joint frame defaults to the child link frame, matching this URDF.
        axis = element(node, "axis")
        element(axis, "xyz", joint.find("axis").get("xyz"))
        source_limit = joint.find("limit")
        if source_limit is not None:
            limit = element(axis, "limit")
            for key in ("effort", "velocity"):
                element(limit, key, source_limit.get(key))
        element(element(axis, "dynamics"), "damping", config["wheel_joint_damping_nms_per_rad"])
    element(model, "pose", numbers([0, 0, -lowest+config["initial_clearance_m"], 0, 0, 0]))
    ET.indent(sdf)
    return ET.tostring(sdf, encoding="unicode")
