#!/usr/bin/env python3
"""Extract the supplied course drawing as a metric Gazebo visual surface.

Requires python3-opencv, python3-numpy and python3-yaml only for regeneration.
Runtime uses checked-in PNG/DAE/config assets and does not depend on OpenCV.
The source photograph and surveyed route templates are never changed.
"""

import argparse
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

import cv2
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
SHARE = ROOT/'src/odin_racer/racer_description'


def extract(image, spec):
    left, top, right, bottom = spec['board_crop_px']
    crop = image[top:bottom, left:right]
    maximum, minimum = crop.max(axis=2), crop.min(axis=2)
    mask = ((maximum < spec['black_max_channel']) &
            (maximum.astype(int)-minimum < spec['black_max_chroma'])).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if count < 2:
        raise ValueError('No track found in reference crop')
    mask = (labels == 1+np.argmax(stats[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    kernel = np.ones((spec['closing_kernel_px'],)*2, dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    for contour, entry in zip(contours, hierarchy[0]):
        if entry[3] != -1 and cv2.contourArea(contour) <= spec['max_annotation_hole_area_px']:
            cv2.drawContours(mask, [contour], -1, 1, cv2.FILLED)
    return mask


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec', type=Path, default=ROOT/'tracks/competition/reference_reconstruction.yaml')
    args = parser.parse_args()
    spec = yaml.safe_load(args.spec.read_text())
    source = ROOT/spec['source']
    image = cv2.imread(str(source))
    if image is None:
        raise ValueError('Cannot read reference image')
    mask = extract(image, spec)
    height, width = mask.shape
    board_x, board_y = spec['board_size_m']
    directory = SHARE/'meshes/competition_course'
    directory.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(directory/'course.png'), (255*(1-mask)).astype(np.uint8))
    # UV origin is bottom-left; row zero of the source image is world +Y.
    dae = f'''<?xml version="1.0" encoding="utf-8"?>
<COLLADA xmlns="http://www.collada.org/2005/11/COLLADASchema" version="1.4.1">
  <asset><created>2026-09-13T00:00:00Z</created><modified>2026-09-13T00:00:00Z</modified><unit name="meter" meter="1"/><up_axis>Z_UP</up_axis></asset>
  <library_images><image id="course_image"><init_from>course.png</init_from></image></library_images>
  <library_effects><effect id="course_effect"><profile_COMMON>
    <newparam sid="surface"><surface type="2D"><init_from>course_image</init_from></surface></newparam>
    <newparam sid="sampler"><sampler2D><source>surface</source></sampler2D></newparam>
    <technique sid="common"><lambert><ambient><color>1 1 1 1</color></ambient><diffuse><texture texture="sampler" texcoord="UVMap"/></diffuse></lambert></technique>
  </profile_COMMON></effect></library_effects>
  <library_materials><material id="course_material"><instance_effect url="#course_effect"/></material></library_materials>
  <library_geometries><geometry id="course_mesh"><mesh>
    <source id="positions"><float_array id="positions_array" count="12">{-board_x/2} {-board_y/2} 0 {board_x/2} {-board_y/2} 0 {board_x/2} {board_y/2} 0 {-board_x/2} {board_y/2} 0</float_array><technique_common><accessor source="#positions_array" count="4" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source>
    <source id="normals"><float_array id="normals_array" count="3">0 0 1</float_array><technique_common><accessor source="#normals_array" count="1" stride="3"><param name="X" type="float"/><param name="Y" type="float"/><param name="Z" type="float"/></accessor></technique_common></source>
    <source id="uv"><float_array id="uv_array" count="8">0 0 1 0 1 1 0 1</float_array><technique_common><accessor source="#uv_array" count="4" stride="2"><param name="S" type="float"/><param name="T" type="float"/></accessor></technique_common></source>
    <vertices id="vertices"><input semantic="POSITION" source="#positions"/></vertices>
    <triangles material="material" count="2"><input semantic="VERTEX" source="#vertices" offset="0"/><input semantic="NORMAL" source="#normals" offset="1"/><input semantic="TEXCOORD" source="#uv" offset="2" set="0"/><p>0 0 0 1 0 1 2 0 2 0 0 0 2 0 2 3 0 3</p></triangles>
  </mesh></geometry></library_geometries>
  <library_visual_scenes><visual_scene id="scene"><node id="board"><instance_geometry url="#course_mesh"><bind_material><technique_common><instance_material symbol="material" target="#course_material"><bind_vertex_input semantic="UVMap" input_semantic="TEXCOORD" input_set="0"/></instance_material></technique_common></bind_material></instance_geometry></node></visual_scene></library_visual_scenes>
  <scene><instance_visual_scene url="#scene"/></scene>
</COLLADA>
'''
    ET.fromstring(dae)
    (directory/'course.dae').write_text(dae)
    ys, xs = np.where(mask)
    left, top = spec['board_crop_px'][:2]
    pixel_x, pixel_y = spec['spawn_pixel']
    # Pixel-center mapping is identical to the texture-to-mesh mapping.
    config = {
        'schema_version': 1, 'status': spec['status'],
        'source': spec['source'], 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'texture_sha256': hashlib.sha256((directory/'course.png').read_bytes()).hexdigest(),
        'board_size_m': spec['board_size_m'], 'board_crop_px': spec['board_crop_px'],
        'texture_size_px': [width, height], 'meters_per_pixel': [board_x/width, board_y/height],
        'track_outer_extent_m': [(int(xs.max()-xs.min())+1)*board_x/width, (int(ys.max()-ys.min())+1)*board_y/height],
        'visual_z_m': .0002,
        'spawn_x_m': (pixel_x-left+.5)*board_x/width-board_x/2,
        'spawn_y_m': board_y/2-(pixel_y-top+.5)*board_y/height,
        'spawn_yaw_rad': spec['spawn_yaw_rad'],
        'spawn_is_official_start': False,
    }
    # Width of the upper run, not all track runs in the same column.
    column = mask[:, int(pixel_x-left)]
    center = int(pixel_y-top)
    a, b = center, center
    while a > 0 and column[a-1]:
        a -= 1
    while b+1 < height and column[b+1]:
        b += 1
    config['estimated_top_straight_width_m'] = (b-a+1)*board_y/height
    (SHARE/'config/competition_course.yaml').write_text('# Generated by tools/generate_competition_course.py; not surveyed route data.\n'+yaml.safe_dump(config, sort_keys=False))
    print(yaml.safe_dump(config, sort_keys=False))


if __name__ == '__main__':
    main()
