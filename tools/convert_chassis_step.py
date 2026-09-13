#!/usr/bin/env python3
"""Convert the supplied millimetre STEP to a metre STL for visual preview.

Requires gmsh==4.15.2 and trimesh==5.1.0 in a separate Python environment.
Usage: python tools/convert_chassis_step.py INPUT.STEP OUTPUT.stl
CAD axes -> preview axes: (x, y, z) -> (-z, x, y).
The mesh is centered in XY with its lowest surface at Z=0.
This rotation is a preview convention, not a measured installation transform.
"""
import argparse
import json
from pathlib import Path
import tempfile

import gmsh
import trimesh


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / 'raw.stl'
        gmsh.initialize()
        try:
            gmsh.option.setNumber('General.Terminal', 0)
            gmsh.model.occ.importShapes(str(args.source.resolve()))
            gmsh.model.occ.synchronize()
            gmsh.option.setNumber('Mesh.MeshSizeMin', 0.8)
            gmsh.option.setNumber('Mesh.MeshSizeMax', 3)
            gmsh.option.setNumber('Mesh.MeshSizeFromCurvature', 24)
            gmsh.model.mesh.generate(2)
            gmsh.option.setNumber('Mesh.Binary', 1)
            gmsh.write(str(raw))
        finally:
            gmsh.finalize()
        mesh = trimesh.load_mesh(raw)
    mesh.apply_transform([[0, 0, -1, 0], [1, 0, 0, 0],
                          [0, 1, 0, 0], [0, 0, 0, 1]])
    bounds = mesh.bounds
    mesh.apply_translation([-(bounds[0, 0]+bounds[1, 0])/2,
                            -(bounds[0, 1]+bounds[1, 1])/2, -bounds[0, 2]])
    mesh.apply_scale(0.001)
    if not mesh.is_watertight or not mesh.is_winding_consistent:
        raise RuntimeError('Export failed mesh topology validation')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(args.output)
    print(json.dumps({'bounds_m': mesh.bounds.tolist(), 'triangles': len(mesh.faces),
                      'watertight': mesh.is_watertight}, indent=2))


if __name__ == '__main__':
    main()
