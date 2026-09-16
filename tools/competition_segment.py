"""Extract the right straight and lower waves for independent evaluation only."""
from collections import deque
from pathlib import Path
import math
import cv2
import numpy as np
from racer_description.course_texture import skeleton


def competition_segment(share):
    image = cv2.imread(str(Path(share)/'meshes/competition_course/course.png'), cv2.IMREAD_GRAYSCALE)
    center = skeleton(image < 128)
    height, width = center.shape
    # Exclude the crossing and upper loops. This region contains only the right
    # straight and bottom waves, and never enters the runtime control nodes.
    yy, xx = np.indices(center.shape)
    pixels = set(zip(*np.where(center & ((xx > 740) | (yy > 475)))))
    def nearest(x, y):
        return min(pixels, key=lambda p: (p[1]-x)**2+(p[0]-y)**2)
    start, end = nearest(767, 45), nearest(83, 490)
    finish = nearest(90, 520)
    parent = {start: None}
    queue = deque([start])
    while queue and end not in parent:
        y, x = queue.popleft()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                p = (y+dy, x+dx)
                if p in pixels and p not in parent:
                    parent[p] = (y, x)
                    queue.append(p)
    path = [end]
    while path[-1] != start:
        path.append(parent[path[-1]])
    path.reverse()
    points = [[(x+.5)/width*4-2, 1.5-(y+.5)/height*3] for y,x in path]
    # Finish on the left end of the wave section, before the source-image gap.
    finish_index = path.index(finish)
    a, b = points[finish_index-12], points[finish_index]
    # The axle starts just before the visible straight; extend its tangent for
    # error/footprint measurement, without adding any line to the scene.
    first = points[0]
    points = [[first[0], first[1]+.6-i*.005] for i in range(120)] + points
    spawn = [1.614118, 1.284377, -math.pi/2]
    return dict(kind='competition', parameters=dict(scale=2.0, line_width=.02116),
                spawn=spawn, evaluation_start=spawn[:2], reference=points,
                end=dict(center=b, radius=.06, yaw=math.atan2(b[1]-a[1], b[0]-a[0])),
                conditions='right_straight_lower_waves_engineering_segment')
