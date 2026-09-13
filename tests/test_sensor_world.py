"""Check sensor frame composition, shared bench settings, and opt-out behavior."""

from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

import numpy as np
import xacro
import yaml

ROOT = Path(__file__).resolve().parents[1]
SHARE = ROOT/"src/odin_racer/racer_description"
sys.path.insert(0, str(SHARE))
from racer_description.contact_world import transform
from racer_description.drive_world import build_drive_resources
from racer_description.sensor_world import add_odin_sensors, build_sensor_bench, fixed_transform, load_sensor_config


def sensor_pose(sensor):
    xyzrpy = sensor.findtext("pose").split()
    return transform(ET.Element("origin", xyz=" ".join(xyzrpy[:3]), rpy=" ".join(xyzrpy[3:])))


class SensorWorldTests(unittest.TestCase):
    def test_mount_rotation_and_optical_axes(self):
        robot = ET.fromstring(xacro.process_file(str(SHARE/"urdf/robot.urdf.xacro")).toxml())
        # A tilted mount detects naive addition of translations and hardcoded world poses.
        mount = robot.find("joint[@name='odin_mount']/origin")
        mount.set("rpy", "0.2 -0.3 0.4")
        body = ET.Element("link")
        add_odin_sensors(body, robot, "base_link", load_sensor_config(SHARE/"config/odin_sensors.yaml"), "/test")
        for name, chain in (("lidar", ["odin_mount", "odin_sim_lidar_mount"]),
                            ("imu", ["odin_mount", "odin_sim_lidar_mount", "odin_sim_imu_mount"]),
                            ("camera", ["odin_mount", "odin_sim_lidar_mount", "odin_sim_camera_mount"])):
            expected = np.eye(4)
            for joint in chain:
                expected = expected @ transform(robot.find(f"joint[@name='{joint}']/origin"))
            actual = sensor_pose(body.find(f"sensor[@name='odin_{name}']"))
            np.testing.assert_allclose(actual[:3, 3], expected[:3, 3], atol=1e-12)
            if name == "camera":
                # Render forward/left/up must be optical forward/left/up.
                np.testing.assert_allclose(actual[:3, 0], expected[:3, 2], atol=1e-12)
                np.testing.assert_allclose(actual[:3, 1], -expected[:3, 0], atol=1e-12)
                np.testing.assert_allclose(actual[:3, 2], -expected[:3, 1], atol=1e-12)
            else:
                np.testing.assert_allclose(actual, expected, atol=1e-12)

    def test_bench_and_vehicle_share_sensor_settings_and_relative_mounts(self):
        with tempfile.TemporaryDirectory() as directory:
            xml, world = build_drive_resources(SHARE, ROOT/"src/odin_racer/racer_control/config/simulation_controllers.yaml", directory)
            robot = ET.fromstring(xml)
            # Use the same fixed sensor subtree with a different ancestor name.
            robot.find("joint[@name='odin_sim_lidar_mount']/parent").set("link", "odin_bench_mount")
            bench = ET.fromstring(build_sensor_bench(SHARE, ET.tostring(robot, encoding="unicode")))
            original = ET.fromstring(xml)
            base_from_odin = fixed_transform(original, "base_link", "odin_link")
            drive = ET.parse(world)
            for name in ("lidar", "camera", "imu"):
                a = bench.find(f".//sensor[@name='odin_{name}']")
                b = drive.find(f".//sensor[@name='odin_{name}']")
                np.testing.assert_allclose(base_from_odin @ sensor_pose(a), sensor_pose(b), atol=1e-12)
                for sensor in (a, b):
                    sensor.remove(sensor.find("pose"))
                    ros = sensor.find("plugin/ros")
                    sensor.find("plugin").remove(ros)
                # Compare structure without indentation introduced by SDF serialization.
                signature = lambda s: [(e.tag, e.attrib, (e.text or "").strip()) for e in s.iter()]
                self.assertEqual(signature(a), signature(b))

    def test_sensor_option_preserves_physics_and_fixtures_are_optional(self):
        with tempfile.TemporaryDirectory() as directory:
            config = ROOT/"src/odin_racer/racer_control/config/simulation_controllers.yaml"
            for enabled in (False, True):
                _, path = build_drive_resources(SHARE, config, directory, sensors=enabled, sensor_targets=enabled)
                world = ET.parse(path)
                model = world.find("world/model[@name='odin_racer']")
                self.assertEqual(len(model.findall("link")), 3)
                self.assertEqual(len(model.findall(".//collision")), 25)
                self.assertAlmostEqual(sum(float(e.text) for e in model.findall("link/inertial/mass")), .877)
                self.assertEqual(len(model.findall("link[@name='base_link']/sensor")), 3 if enabled else 0)
                self.assertEqual(world.find("world/model[@name='sensor_target']") is not None, enabled)

    def test_bad_config_and_moving_mount_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            data = yaml.safe_load((SHARE/"config/odin_sensors.yaml").read_text())
            data["camera"]["near_m"] = data["camera"]["far_m"]
            path = Path(directory)/"bad.yaml"
            path.write_text(yaml.safe_dump(data))
            with self.assertRaises(ValueError):
                load_sensor_config(path)
        robot = ET.fromstring(xacro.process_file(str(SHARE/"urdf/robot.urdf.xacro")).toxml())
        robot.find("joint[@name='odin_mount']").set("type", "continuous")
        with self.assertRaisesRegex(ValueError, "fixed"):
            fixed_transform(robot, "base_link", "odin_sim_imu")


if __name__ == "__main__":
    unittest.main()
