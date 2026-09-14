"""Repaint the reconstructed map at a physical stroke width, for rendering only."""
from pathlib import Path
import xml.etree.ElementTree as ET

import cv2
import numpy as np


def skeleton(mask):
    """Connectivity-preserving Zhang-Suen thinning; keep all route branches."""
    work = np.pad(mask.astype(np.uint8), 1)
    while True:
        changed = False
        for phase in range(2):
            p = [work[:-2, 1:-1], work[:-2, 2:], work[1:-1, 2:],
                 work[2:, 2:], work[2:, 1:-1], work[2:, :-2],
                 work[1:-1, :-2], work[:-2, :-2]]
            count = sum(p)
            transitions = sum(((p[i] == 0) & (p[(i+1) % 8] != 0)).astype(np.uint8)
                              for i in range(8))
            clear = ((p[0]*p[2]*p[4] == 0) & (p[2]*p[4]*p[6] == 0)
                     if phase == 0 else
                     (p[0]*p[2]*p[6] == 0) & (p[0]*p[4]*p[6] == 0))
            remove = ((work[1:-1, 1:-1] != 0) & (count >= 2) & (count <= 6)
                      & (transitions == 1) & clear)
            changed |= bool(remove.any())
            work[1:-1, 1:-1][remove] = 0
        if not changed:
            return work[1:-1, 1:-1]


def fixed_width_mesh(asset_directory, output_directory, board_size, line_width):
    """Keep texture centerline topology; redraw at approximately line_width metres.

    Four-times texture sampling bounds stroke rasterization error. This is map
    preparation, not onboard perception, and publishes no route observations.
    """
    asset_directory, output = Path(asset_directory), Path(output_directory)
    source = cv2.imread(str(asset_directory/'course.png'), cv2.IMREAD_GRAYSCALE)
    if source is None:
        raise ValueError('Missing competition texture')
    center = skeleton(source < 128)
    height, width = source.shape
    factor = 4
    ink = np.zeros((height*factor, width*factor), np.uint8)
    for y, x in zip(*np.where(center)):
        start = (int(x*factor+factor//2), int(y*factor+factor//2))
        ink[start[1], start[0]] = 255
        for dy, dx in ((0, 1), (1, -1), (1, 0), (1, 1)):
            ny, nx = y+dy, x+dx
            if 0 <= ny < height and 0 <= nx < width and center[ny, nx]:
                cv2.line(ink, start, (int(nx*factor+factor//2),
                                     int(ny*factor+factor//2)), 255, 1)
    # The supplied board's X/Y pixel pitches agree to better than 0.1 percent.
    pitch = sum((board_size[0]/width, board_size[1]/height))/(2*factor)
    distance = cv2.distanceTransform(255-ink, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    texture = np.where(distance <= line_width/(2*pitch), 0, 255).astype(np.uint8)
    output.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output/'course_fixed_width.png'), texture):
        raise RuntimeError('Cannot write competition texture')
    tree = ET.parse(asset_directory/'course.dae')
    ns = {'c': 'http://www.collada.org/2005/11/COLLADASchema'}
    ET.register_namespace('', ns['c'])
    tree.find('.//c:image/c:init_from', ns).text = 'course_fixed_width.png'
    path = output/'course_fixed_width.dae'
    tree.write(path, encoding='utf-8', xml_declaration=True)
    return path
