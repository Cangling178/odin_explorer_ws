"""Odin FishPoly geometry in ROS optical axes (X right, Y down, Z forward).

Reference: manifoldsdk/odin_ros_driver/include/polynomial_camera.hpp and
ManifoldTechLtd/wiki, Odin1 section 5.3. This is NOT OpenCV fisheye/KB4.
CameraInfo contract: distortion_model='fishpoly', D=[k2,...,k7],
K=[[A11,A12,u0],[0,A22,v0],[0,0,1]]. P is zero (no rectified output).
The renderer supports calibrated pixels in the forward hemisphere only.
"""
from pathlib import Path

import numpy as np
import yaml


class FishPoly:
    def __init__(self, width, height, k, d):
        self.width, self.height = int(width), int(height)
        self.k = np.asarray(k, dtype=float).reshape(3, 3)
        self.d = np.asarray(d, dtype=float)
        if (width != self.width or height != self.height or min(width, height) < 2
                or self.d.shape != (6,) or not np.isfinite(self.k).all()
                or not np.isfinite(self.d).all() or self.k[0, 0] <= 0 or self.k[1, 1] <= 0
                or not np.allclose(self.k[2], [0, 0, 1]) or self.k[1, 0] != 0):
            raise ValueError('Invalid FishPoly calibration')
        # Check derivative extrema analytically, not just on a sampled grid.
        polynomial = np.polynomial.Polynomial([0, 1, *self.d])
        derivative = polynomial.deriv()
        roots = derivative.deriv().roots()
        samples = [0., np.pi/2] + [r.real for r in roots
                    if abs(r.imag) < 1e-10 and 0 < r.real < np.pi/2]
        if np.min(derivative(np.asarray(samples))) <= 0:
            raise ValueError('FishPoly must be monotonic in the forward hemisphere')
        self.unproject(np.array([[0, 0], [width-1, 0], [0, height-1], [width-1, height-1]]))

    @classmethod
    def from_file(cls, path):
        cam = yaml.safe_load(Path(path).read_text())['cam_0']
        if cam['cam_model'] != 'FishPoly' or cam['p1'] != 0 or cam['p2'] != 0:
            raise ValueError('Expected FishPoly with zero tangential distortion')
        return cls(cam['image_width'], cam['image_height'],
                   [[cam['A11'], cam['A12'], cam['u0']],
                    [0, cam['A22'], cam['v0']], [0, 0, 1]],
                   [cam[f'k{i}'] for i in range(2, 8)])

    @classmethod
    def from_info(cls, info):
        if info.distortion_model != 'fishpoly':
            raise ValueError('Expected custom fishpoly CameraInfo')
        return cls(info.width, info.height, info.k, info.d)

    def radius(self, theta):
        return np.polynomial.polynomial.polyval(theta, [0., 1., *self.d])

    def project(self, xyz):
        xyz = np.asarray(xyz, dtype=float)
        if not np.isfinite(xyz).all() or np.any(xyz[..., 2] <= 0):
            raise ValueError('Expected finite points in front of camera')
        r = np.linalg.norm(xyz[..., :2], axis=-1)
        theta = np.arctan2(r, xyz[..., 2])
        scale = np.divide(self.radius(theta), r, out=np.zeros_like(r), where=r > 0)
        xy = xyz[..., :2]*scale[..., None]
        return xy @ self.k[:2, :2].T + self.k[:2, 2]

    def unproject(self, uv):
        uv = np.asarray(uv, dtype=float)
        xy = (uv-self.k[:2, 2]) @ np.linalg.inv(self.k[:2, :2]).T
        r = np.linalg.norm(xy, axis=-1)
        if not np.isfinite(r).all() or np.any(r >= self.radius(np.pi/2)):
            raise ValueError('FishPoly pixel outside supported forward hemisphere')
        lo, hi = np.zeros_like(r), np.full_like(r, np.pi/2)
        for _ in range(48):
            mid = (lo+hi)/2
            less = self.radius(mid) < r
            lo, hi = np.where(less, mid, lo), np.where(less, hi, mid)
        theta = (lo+hi)/2
        scale = np.divide(np.sin(theta), r, out=np.ones_like(r), where=r > 0)
        return np.concatenate([xy*scale[..., None], np.cos(theta)[..., None]], axis=-1)


def pixel_rays(info, uv):
    """Support the onboard FishPoly and the unchanged pinhole overview camera."""
    if info.distortion_model == 'fishpoly':
        return FishPoly.from_info(info).unproject(uv)
    if info.distortion_model != 'plumb_bob' or np.any(info.d):
        raise ValueError('Unsupported camera model')
    uv = np.asarray(uv)
    return np.concatenate([uv, np.ones((*uv.shape[:-1], 1))], axis=-1) @ np.linalg.inv(np.array(info.k).reshape(3, 3)).T
