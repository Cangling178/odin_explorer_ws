#!/usr/bin/env python3
"""Generate a unit hex prism: across flats 1, Z from -1 to 0.
URDF scales it to the selected standoff width and effective length.
"""
import math
from pathlib import Path
import struct

def main():
    radius = 1 / math.sqrt(3)
    ring = [(radius*math.cos(i*math.pi/3), radius*math.sin(i*math.pi/3)) for i in range(6)]
    bottom = [(x,y,-1.) for x,y in ring]
    top = [(x,y,0.) for x,y in ring]
    faces=[]
    for i in range(6):
        j=(i+1)%6
        faces.extend([(bottom[i],bottom[j],top[j]),(bottom[i],top[j],top[i]),
                      ((0.,0.,0.),top[i],top[j]),((0.,0.,-1.),bottom[j],bottom[i])])
    out=Path(__file__).resolve().parents[1]/'src/odin_racer/racer_description/meshes/standoff_unit_hex.stl'
    with out.open('wb') as f:
        f.write(b'Unit hex standoff; across flats=1; z=-1..0'.ljust(80,b' '))
        f.write(struct.pack('<I',len(faces)))
        for a,b,c in faces:
            u=[b[i]-a[i] for i in range(3)]; v=[c[i]-a[i] for i in range(3)]
            n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
            length=math.sqrt(sum(t*t for t in n));n=[t/length for t in n]
            f.write(struct.pack('<12fH',*n,*a,*b,*c,0))
    print(out)

if __name__=='__main__':main()
