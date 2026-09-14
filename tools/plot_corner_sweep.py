#!/usr/bin/env python3
"""Plot recorded chassis envelopes against the unchanged engineering corridor."""
import argparse
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Circle
import numpy as np


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('report',type=Path);args=parser.parse_args()
    report=json.loads(args.report.read_text())
    if report['course'] not in ('line_corner_left','line_corner_right'):parser.error('A single-corner report is required')
    sign=-1 if report['course'].endswith('right') else 1
    cfg=report['fixture']['parameters'];cx=cfg['corner_x'];width=report['criteria']['corridor_half_width_m']
    fig,ax=plt.subplots(figsize=(8,6),constrained_layout=True)
    ax.add_patch(Polygon([[-.5,-width],[cx,-width],[cx,width],[-.5,width]],color='#e7eef3',zorder=0))
    ax.add_patch(Polygon([[cx-width,0],[cx+width,0],[cx+width,sign*1.6],[cx-width,sign*1.6]],color='#e7eef3',zorder=0))
    ax.add_patch(Circle((cx,0),width,color='#e7eef3',zorder=0))
    reference=np.array(report['fixture']['reference']);ax.plot(reference[:,0],reference[:,1],color='black',lw=1.2,label='Unchanged reference')
    lo,hi=np.array(report['footprint']['min']),np.array(report['footprint']['max'])
    corners=np.array([[lo[0],lo[1]],[hi[0],lo[1]],[hi[0],hi[1]],[lo[0],hi[1]]])
    selected=[s for s in report['samples'] if s['state'] in ('CORNER_STOP','TURN','REACQUIRE')]
    shown=set()
    for index,sample in enumerate(selected):
        if index%10 and index!=len(selected)-1:continue
        c,s=math.cos(sample['yaw']),math.sin(sample['yaw']);body=corners@np.array([[c,s],[-s,c]])+[sample['x'],sample['y']]
        bad=sample['swept_distance']>width;color='#ce413b' if bad else '#276aa0'
        label='Envelope outside corridor' if bad else 'Recorded chassis envelope'
        ax.add_patch(Polygon(body,fill=False,edgecolor=color,alpha=.35,lw=.9,label=label if label not in shown else None));shown.add(label)
    trajectory=np.array([[s['x'],s['y']] for s in report['samples']]);ax.plot(trajectory[:,0],trajectory[:,1],color='#009b76',lw=2,label='Actual axle trajectory')
    if selected:
        parked=selected[0];ax.scatter([parked['x']],[parked['y']],color='#db9900',s=45,zorder=5,label='Stop request')
        ax.annotate(f"Stop-request setback: {cx-parked['x']:.3f} m",(parked['x'],parked['y']),xytext=(cx-.32,sign*.37),arrowprops=dict(arrowstyle='->'),fontsize=10)
    bound=report.get('metrics',{}).get('max_swept_distance_m')
    ax.set_title(f"{report['course']}: full-body turn sweep\nEngineering half width {width:.3f} m; recorded upper bound {bound:.3f} m")
    ax.set_xlim(cx-.4,cx+.38);ax.set_ylim(-.35,.6) if sign>0 else ax.set_ylim(-.6,.35)
    ax.set_aspect('equal');ax.set_xlabel('Ground-truth x [m]');ax.set_ylabel('Ground-truth y [m]');ax.legend(fontsize=8,loc='upper left')
    output=args.report.with_name('turn_sweep.png');fig.savefig(output,dpi=170);plt.close(fig);print(output)

if __name__=='__main__':main()
