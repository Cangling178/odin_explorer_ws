"""Check mass conservation, transformed geometry, and per-contact surfaces."""

from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

import numpy as np
import xacro

SHARE = Path(__file__).resolve().parents[1]/"src/odin_racer/racer_description"
sys.path.insert(0, str(SHARE))
from racer_description.contact_world import aggregate, build_world, transform


class ContactWorldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = ET.fromstring(build_world(SHARE)).find("world")
        cls.model = cls.world.find("model[@name='odin_racer']")

    def test_parallel_axis_and_translation(self):
        # Two unit bodies, offset along x=y. Includes a nonzero product of inertia.
        entries = [(1., np.array([1., 1., 0.]), np.eye(3)),
                   (1., np.array([-1., -1., 0.]), np.eye(3))]
        mass, center, tensor = aggregate(entries)
        self.assertEqual(mass, 2.)
        np.testing.assert_allclose(center, 0.)
        np.testing.assert_allclose(tensor, [[4., -2., 0.], [-2., 4., 0.], [0., 0., 6.]])
        shifted = [(m, c+np.array([3., 7., -4.]), i) for m, c, i in entries]
        np.testing.assert_allclose(aggregate(shifted)[2], tensor)

    def test_bodies_and_mass(self):
        links = self.model.findall("link")
        self.assertEqual({l.get("name") for l in links}, {"base_link", "left_wheel_link", "right_wheel_link"})
        self.assertEqual(len(self.model.findall("joint")), 2)
        masses = {l.get("name"): float(l.findtext("inertial/mass")) for l in links}
        self.assertAlmostEqual(masses["base_link"], .785)
        self.assertAlmostEqual(sum(masses.values()), .877)
        self.assertEqual(len(self.model.findall(".//collision")), 25)
        self.assertEqual(len(self.model.findall(".//visual")), 24)

    def test_fixed_geometry_transforms_preserved(self):
        source = ET.fromstring(xacro.process_file(str(SHARE/"urdf/robot.urdf.xacro")).toxml())
        transforms = {"base_link": np.eye(4)}
        pending = source.findall("joint")
        while pending:
            for joint in pending[:]:
                parent = joint.find("parent").get("link")
                if parent in transforms:
                    transforms[joint.find("child").get("link")] = transforms[parent] @ transform(joint.find("origin"))
                    pending.remove(joint)
        def sdf_transform(text):
            values = text.split()
            return transform(ET.Element("origin", xyz=" ".join(values[:3]), rpy=" ".join(values[3:])))
        actual = {}
        for body in self.model.findall("link"):
            base = sdf_transform(body.findtext("pose"))
            for collision in body.findall("collision"):
                actual[collision.get("name")] = base @ sdf_transform(collision.findtext("pose"))
        for link in source.findall("link"):
            for collision in link.findall("collision"):
                key = link.get("name")+"_"+collision.get("name")
                np.testing.assert_allclose(actual[key], transforms[link.get("name")] @ transform(collision.find("origin")), atol=1e-12)

    def test_contact_surfaces_survive_lumping(self):
        coefficients = {}
        for collision in self.model.findall(".//collision"):
            coefficients[collision.get("name")] = float(collision.findtext("surface/friction/ode/mu"))
            self.assertEqual(collision.findtext("surface/friction/ode/mu"), collision.findtext("surface/friction/ode/mu2"))
            self.assertEqual(float(collision.findtext("surface/contact/ode/kp")), 100000.)
        self.assertEqual(sum(v == .02 for v in coefficients.values()), 2)
        self.assertEqual(sum(v == .8 for v in coefficients.values()), 2)
        self.assertEqual(sum(v == .5 for v in coefficients.values()), 21)
        self.assertAlmostEqual(float(self.model.findtext("pose").split()[2]), .05325)


if __name__ == "__main__":
    unittest.main()
