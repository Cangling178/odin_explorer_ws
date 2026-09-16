#!/usr/bin/env python3
"""Prepare the explicitly ordered image-derived lap; never reads simulator truth."""
from collections import deque
from pathlib import Path
import sys, json, hashlib
import cv2
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src/odin_racer/racer_description'))
from racer_description.course_texture import skeleton


def route():
    source=ROOT/'src/odin_racer/racer_description/meshes/competition_course/course.png'
    im=cv2.imread(str(source),0)
    pixels=set(zip(*np.where(skeleton(im<128))))
    # Direction: right straight down, waves left, left lobe, upper-left
    # rectangle, central loop, straight through crossing again, upper-right.
    anchors=[(767,160),(767,510),(590,493),(454,570),(311,488),(166,566),
             (84,485),(81,324),(218,414),(286,348),(202,258),(93,201),
             (92,64),(455,64),(455,147),(247,153),(260,178),(453,269),
             (522,340),(468,400),(406,349),(453,270),(641,64),(767,64),(767,160)]
    anchors=[min(pixels,key=lambda p:(p[1]-x)**2+(p[0]-y)**2) for x,y in anchors]
    ordered=[]
    for start,end in zip(anchors,anchors[1:]):
        parent={start:None};queue=deque([start])
        while queue and end not in parent:
            y,x=queue.popleft()
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    p=(y+dy,x+dx)
                    if p in pixels and p not in parent:
                        parent[p]=(y,x);queue.append(p)
        if end not in parent:raise ValueError('Disconnected course anchors')
        part=[end]
        while part[-1]!=start:part.append(parent[part[-1]])
        ordered.extend(part[::-1][:-1])
    ordered.append(anchors[-1])
    xy=np.array([[(x+.5)/im.shape[1]*4-2,1.5-(y+.5)/im.shape[0]*3] for y,x in ordered])
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(xy,axis=0),axis=1))]
    stations=np.linspace(0,arc[-1],int(np.ceil(arc[-1]/.005))+1)
    xy=np.c_[np.interp(stations,arc,xy[:,0]),np.interp(stations,arc,xy[:,1])]
    return xy,dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),raw_skeleton_length_m=float(arc[-1]),length_m=float(np.linalg.norm(np.diff(xy,axis=0),axis=1).sum()),
        spawn=[*xy[0],-np.pi/2],map_size_m=[4,3],route='right_down_waves_left_lobe_rectangle_center_loop_upper_right',
        source='image reconstruction, not surveyed',gap_policy='Retain original texture; use mapped continuity through its small damaged stroke.')

if __name__=='__main__':
    xy,meta=route()
    dest=ROOT/'src/odin_racer/racer_control/config/competition_lap.csv'
    np.savetxt(dest,xy,delimiter=',',header='x_m,y_m',comments='# ',fmt='%.7f')
    dest.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.figure(figsize=(9,7));plt.plot(xy[:,0],xy[:,1]);plt.scatter(*xy[0],c='red')
    for i in range(30,len(xy),140):
        d=xy[i+5]-xy[i];plt.arrow(*xy[i],*(d*3),head_width=.035,color='orange')
    plt.axis('equal');plt.grid();plt.savefig(ROOT/'data/generated/competition_lap/route.png');print(meta)
