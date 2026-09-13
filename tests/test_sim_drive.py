"""Verify simulated control interfaces and generated runtime configuration."""

from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

import xacro
import yaml

ROOT = Path(__file__).resolve().parents[1]
SHARE = ROOT/"src/odin_racer/racer_description"
CONFIG = ROOT/"src/odin_racer/racer_control/config/simulation_controllers.yaml"
sys.path.insert(0, str(SHARE))
from racer_description.drive_world import build_drive_resources


class SimDriveTests(unittest.TestCase):
    def test_passive_preview_has_no_control_interfaces(self):
        robot = ET.fromstring(xacro.process_file(str(SHARE/"urdf/robot.urdf.xacro")).toxml())
        self.assertIsNone(robot.find("ros2_control"))
        self.assertIsNone(robot.find("joint/limit"))

    def test_control_and_physics_joint_limits_agree(self):
        with tempfile.TemporaryDirectory() as directory:
            xml, world = build_drive_resources(SHARE, CONFIG, directory)
            robot = ET.fromstring(xml)
            model = ET.parse(world).find("world/model[@name='odin_racer']")
            interfaces = robot.findall("ros2_control/joint")
            self.assertEqual(len(interfaces), 2)
            for interface in interfaces:
                self.assertEqual(interface.find("command_interface").get("name"), "velocity")
                self.assertEqual({s.get("name") for s in interface.findall("state_interface")}, {"position", "velocity", "effort"})
                name = interface.get("name")
                urdf_limit = robot.find(f"joint[@name='{name}']/limit")
                sdf_limit = model.find(f"joint[@name='{name}']/axis/limit")
                for key in ("effort", "velocity"):
                    self.assertEqual(float(urdf_limit.get(key)), float(sdf_limit.findtext(key)))
                self.assertLess(float(interface.findtext("param[@name='vel_min_integral_error']")), 0)
            self.assertAlmostEqual(sum(float(m.text) for m in model.findall("link/inertial/mass")), .877)
            self.assertEqual(len(model.findall(".//collision")), 25)
            self.assertEqual(model.findtext("plugin/ros/namespace"), "/sim/racer")
            self.assertEqual(len(model.findall("plugin")), 1)
            config = yaml.safe_load((Path(directory)/"controllers.yaml").read_text())
            drive = config["/sim/racer/diff_drive_controller"]["ros__parameters"]
            self.assertAlmostEqual(drive["wheel_radius"], .03325)
            self.assertAlmostEqual(drive["wheel_separation"], .257)
            self.assertFalse(drive["open_loop"])
            self.assertTrue(drive["use_stamped_vel"])
            self.assertEqual(drive["cmd_vel_timeout"], .25)

    def test_reject_body_limits_that_exceed_wheel_limits(self):
        with tempfile.TemporaryDirectory() as directory:
            config = yaml.safe_load(CONFIG.read_text())
            config["/sim/racer/diff_drive_controller"]["ros__parameters"]["linear.x.max_velocity"] = 1.0
            source = Path(directory)/"excessive.yaml"
            source.write_text(yaml.safe_dump(config))
            with self.assertRaisesRegex(ValueError, "exceed wheel"):
                build_drive_resources(SHARE, source, directory)


if __name__ == "__main__":
    unittest.main()
