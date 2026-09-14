"""Device model checks independent of the rendering LUT implementation."""
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src/odin_racer/racer_description'))
from racer_description.fishpoly import FishPoly


class FishPolyTests(unittest.TestCase):
    def setUp(self):
        self.model = FishPoly.from_file(ROOT/'hardware/mechanical/odin1/calib_device.yaml')

    def test_optical_axis_and_equally_spaced_angles(self):
        m = self.model
        np.testing.assert_allclose(m.project([[0, 0, 1], [0, 0, 12]]), [m.k[:2, 2]]*2)
        np.testing.assert_allclose(m.unproject(m.k[:2, 2]), [0, 0, 1], atol=1e-12)
        # An all-zero polynomial remains equidistant, it must not become pinhole.
        ideal = FishPoly(100, 100, [[100, 0, 50], [0, 100, 50], [0, 0, 1]], np.zeros(6))
        theta = np.array([.1, .2, .3])
        np.testing.assert_allclose(ideal.project(np.c_[np.sin(theta), theta*0, np.cos(theta)])[:, 0], [60, 70, 80])

    def test_round_trip_full_frame_and_scale_invariance(self):
        m = self.model
        v, u = np.mgrid[0:1296:37, 0:1600:41]
        uv = np.concatenate([np.c_[u.ravel(), v.ravel()], [[0, 0], [1599, 0], [0, 1295], [1599, 1295]]])
        rays = m.unproject(uv)
        np.testing.assert_allclose(m.project(rays), uv, atol=1e-9)
        np.testing.assert_allclose(m.project(rays*17), uv, atol=1e-9)
        np.testing.assert_allclose(np.linalg.norm(rays, axis=1), 1, atol=1e-12)

    def test_vendor_forward_formula(self):
        # Direct acos/power formulation from the official PolynomialCamera,
        # avoiding optical-axis singularity in that reference implementation.
        m = self.model
        xyz = np.random.default_rng(10).uniform(-1, 1, (1000, 3))
        xyz[:, 2] = np.abs(xyz[:, 2])+.05
        r = np.linalg.norm(xyz[:, :2], axis=1)
        theta = np.arccos(xyz[:, 2]/np.linalg.norm(xyz, axis=1))
        rd = theta+sum(k*theta**i for i, k in enumerate(m.d, 2))
        distorted = xyz[:, :2]*(rd/r)[:, None]
        expected = distorted @ m.k[:2, :2].T+m.k[:2, 2]
        np.testing.assert_allclose(m.project(xyz), expected, atol=1e-9)

    def test_device_fov_and_corner_coverage(self):
        m = self.model
        def angle(a, b):
            return np.degrees(np.arccos(m.unproject(a) @ m.unproject(b)))
        self.assertAlmostEqual(angle([0, m.k[1, 2]], [1599, m.k[1, 2]]), 128.8504448, places=6)
        self.assertAlmostEqual(angle([m.k[0, 2], 0], [m.k[0, 2], 1295]), 103.2996322, places=6)
        corners = m.unproject([[0, 0], [1599, 0], [0, 1295], [1599, 1295]])
        self.assertLess(np.degrees(np.arccos(corners[:, 2])).max(), 86.2)

    def test_invalid_models_and_pixels_rejected(self):
        m = self.model
        with self.assertRaises(ValueError):
            FishPoly(m.width, m.height, m.k, [-1, 0, 0, 0, 0, 0])
        with self.assertRaises(ValueError):
            m.unproject([[10000, 10000]])
        with self.assertRaises(ValueError):
            m.project([[0, 0, -1]])


if __name__ == '__main__':
    unittest.main()
