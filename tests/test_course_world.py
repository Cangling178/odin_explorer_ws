"""Check scale/provenance and keep the printed track separate from contact physics."""

import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
SHARE = ROOT/'src/odin_racer/racer_description'
CONTROL = ROOT/'src/odin_racer/racer_control/config/simulation_controllers.yaml'
sys.path.insert(0, str(SHARE))
from racer_description.drive_world import build_drive_resources


class CourseWorldTests(unittest.TestCase):
    def build(self, **options):
        with tempfile.TemporaryDirectory() as directory:
            _, path = build_drive_resources(SHARE, CONTROL, directory, **options)
            return ET.parse(path).find('world')

    def test_print_preserves_contact_and_sensors(self):
        empty = self.build()
        course = self.build(course='competition')
        for selector in ("model[@name='floor']/link/collision", 'physics'):
            self.assertEqual(ET.tostring(empty.find(selector)), ET.tostring(course.find(selector)))
        a, b = [w.find("model[@name='odin_racer']") for w in (empty, course)]
        for tag in ('link', 'joint'):
            self.assertEqual([ET.tostring(n) for n in a.findall(tag)], [ET.tostring(n) for n in b.findall(tag)])
        board = course.find("model[@name='competition_course']")
        self.assertEqual(board.findtext('static'), 'true')
        self.assertEqual(board.findall('.//collision'), [])
        self.assertEqual(len(course.findall('.//collision')), len(empty.findall('.//collision')))
        self.assertIsNone(empty.find("model[@name='competition_course']"))
        self.assertIsNone(course.find("model[@name='course_overview']"))
        self.assertAlmostEqual(float(a.findtext('pose').split()[2]), float(b.findtext('pose').split()[2]))

    def test_asset_scale_orientation_and_provenance(self):
        config = yaml.safe_load((SHARE/'config/competition_course.yaml').read_text())
        spec = yaml.safe_load((ROOT/'tracks/competition/reference_reconstruction.yaml').read_text())
        asset = SHARE/'meshes/competition_course'
        for key, path in (('source', ROOT/config['source']), ('texture', asset/'course.png')):
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), config[key+'_sha256'])
        png = (asset/'course.png').read_bytes()
        self.assertEqual(list(struct.unpack('>II', png[16:24])), config['texture_size_px'])
        ns = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}
        dae = ET.parse(asset/'course.dae')
        vertices = np.fromstring(dae.findtext('.//c:float_array[@id="positions_array"]', namespaces=ns), sep=' ').reshape(-1, 3)
        np.testing.assert_allclose(np.ptp(vertices, axis=0), [*spec['board_size_m'], 0])
        self.assertEqual(dae.findtext('.//c:up_axis', namespaces=ns), 'Z_UP')
        self.assertEqual(dae.findtext('.//c:image/c:init_from', namespaces=ns), 'course.png')
        width, height = config['texture_size_px']
        left, top = spec['board_crop_px'][:2]
        px, py = spec['spawn_pixel']
        self.assertAlmostEqual(config['spawn_x_m'], (px-left+.5)/width*2-1)
        self.assertAlmostEqual(config['spawn_y_m'], .75-(py-top+.5)/height*1.5)
        self.assertFalse(config['spawn_is_official_start'])
        self.assertEqual(config['status'], 'image_reconstruction_not_surveyed')

    def test_course_without_onboard_sensors_and_optional_overview(self):
        world = self.build(course='competition', sensors=False, course_overview=True)
        self.assertEqual(world.find("model[@name='odin_racer']").findall('.//sensor'), [])
        self.assertEqual(len(world.findall('.//sensor')), 1)
        config = yaml.safe_load((SHARE/'config/competition_course.yaml').read_text())
        xyzrpy = np.fromstring(world.findtext("model[@name='odin_racer']/pose"), sep=' ')
        np.testing.assert_allclose(xyzrpy[[0, 1, 5]], [config[k] for k in ('spawn_x_m', 'spawn_y_m', 'spawn_yaw_rad')])

    def test_reject_mixed_scenes(self):
        for options in ({'course': 'unknown'}, {'course': 'competition', 'sensor_targets': True}, {'course_overview': True}):
            with self.subTest(options=options), self.assertRaises(ValueError):
                self.build(**options)


if __name__ == '__main__':
    unittest.main()
