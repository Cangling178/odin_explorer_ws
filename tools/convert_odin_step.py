#!/usr/bin/env python3
"""Convert official Odin1 STEP (mm) to a metre mesh in bottom-hole-center frame.
Requires gmsh==4.15.2, trimesh==5.1.0. Front +X, left +Y, up +Z.
Official CAD: width X, bottom Y=31, front +Z; bottom hole midpoint Z=20.4.
"""
from pathlib import Path
import tempfile
import gmsh
import trimesh

def main():
    root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as tmp:
        raw=Path(tmp)/'odin.stl'
        gmsh.initialize()
        try:
            gmsh.option.setNumber('General.Terminal',0)
            gmsh.model.occ.importShapes(str(root/'hardware/mechanical/odin1/Odin1.stp'))
            gmsh.model.occ.synchronize()
            gmsh.option.setNumber('Mesh.MeshSizeMin',1)
            gmsh.option.setNumber('Mesh.MeshSizeMax',3)
            gmsh.option.setNumber('Mesh.MeshSizeFromCurvature',16)
            gmsh.model.mesh.generate(2)
            gmsh.option.setNumber('Mesh.Binary',1)
            gmsh.write(str(raw))
        finally:
            gmsh.finalize()
        mesh=trimesh.load_mesh(raw)
    mesh.apply_transform([[0,0,1,-20.4],[-1,0,0,0],[0,-1,0,31],[0,0,0,1]])
    mesh.apply_scale(.001)
    mesh.export(root/'src/odin_racer/racer_description/meshes/odin1.stl')
    print('Bounds (m):',mesh.bounds,'triangles:',len(mesh.faces))

if __name__=='__main__':main()
