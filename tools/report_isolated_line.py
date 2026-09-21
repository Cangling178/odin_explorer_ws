#!/usr/bin/env python3
"""Render independent charts, inspectable camera overlays and a bilingual index."""
import argparse
import html
import json
import math
from pathlib import Path
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle


def render_turn_sweep(report, folder):
    """Add the recorded corner envelope to the shared report output."""
    if (report['course'] not in ('line_corner_left', 'line_corner_right')
            or not report.get('samples')
            or report.get('metrics', {}).get('max_swept_distance_m') is None):
        return
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
    output=folder/'turn_sweep.png';fig.savefig(output,dpi=170);plt.close(fig);print(output)


def render(path):
    report=json.loads(path.read_text());folder=path.parent;samples=report.get('samples',[])
    if samples:
        ref=np.array(report['fixture']['reference']);trajectory=np.array([[s['x'],s['y']] for s in samples])
        fig,axes=plt.subplots(2,2,figsize=(11,8),constrained_layout=True)
        a=axes[0,0];a.plot(ref[:,0],ref[:,1],color='.7',label='Reference (evaluation only)')
        phases={'CURVE_ALIGN':'#bb5566','RUNNING':'#1368a5','APPROACH':'#e69f00','CORNER_STOP':'#777777','TURN':'#9b4f96','REACQUIRE':'#009e73'}
        for phase,color in phases.items():
            rows=np.array([[s['x'],s['y']] for s in samples if s['state']==phase])
            if len(rows):a.scatter(rows[:,0],rows[:,1],s=5,color=color,label=phase)
        end=report['fixture']['end'];a.add_patch(plt.Circle(end['center'],end['radius'],fill=False,color='green'))
        a.set_aspect('equal');a.legend(fontsize=7);a.set(xlabel='x [m]',ylabel='y [m]',title='Ground-truth trajectory and end region')
        t=np.array([s['time'] for s in samples]);a=axes[0,1]
        a.plot(t,[s['error']*1000 for s in samples]);a.set(xlabel='Time [s]',ylabel='Lateral error [mm]',title='Full-run error, including initial correction')
        a=axes[1,0];a.plot(t,[s['cmd_v'] for s in samples],label='v command [m/s]');a.plot(t,[s['cmd_w'] for s in samples],label='yaw command [rad/s]');a.legend();a.set(xlabel='Time [s]',title='Command history')
        a=axes[1,1];a.plot(t,[s['swept_distance'] for s in samples],label='Filled chassis envelope upper bound')
        a.axhline(report['criteria']['corridor_half_width_m'],color='red',ls='--',label='Engineering corridor half width')
        a.set(xlabel='Time [s]',ylabel='Distance from reference [m]',title='Physical envelope (not only axle center)');a.legend(fontsize=8)
        fig.suptitle(report['course']+' — '+('PASS' if report['passed'] else 'FAIL'))
        fig.savefig(folder/'evaluation.png',dpi=160);plt.close(fig)
    grid=report.get('ground_grid',dict(near_x=.25,half_width=.30,grid_step=.005))
    for entry in report.get('captures',[]):
        name=entry['files'].get('ground')
        if not name:continue
        source=cv2.imread(str(folder/name));height,width=source.shape[:2]
        scale=4;debug=cv2.resize(source,(width*scale,height*scale),interpolation=cv2.INTER_NEAREST)
        canvas=np.full((height*scale+100,width*scale,3),245,np.uint8);canvas[100:]=debug
        try:telemetry=json.loads(entry.get('telemetry') or '{}')
        except ValueError:telemetry={}
        target=telemetry.get('target')
        if target:
            col=int((grid['half_width']-target[1])/grid['grid_step']*scale);row=int((target[0]-grid['near_x'])/grid['grid_step']*scale)+100
            if 0<=col<width*scale and 100<=row<canvas.shape[0]:cv2.drawMarker(canvas,(col,row),(255,150,0),cv2.MARKER_CROSS,14,2)
        lines=[f"t={entry['time']:.2f}s  {telemetry.get('state','no control telemetry')}",
               f"age={telemetry.get('observation_age','?')}  L={telemetry.get('lookahead','?')}",
               f"v={telemetry.get('cmd_v','?')}  w={telemetry.get('cmd_w','?')}",
               'red: centerline   yellow: corner   blue: target']
        for i,line in enumerate(lines):cv2.putText(canvas,line[:75],(8,20+i*23),cv2.FONT_HERSHEY_SIMPLEX,.40,(30,30,30),1,cv2.LINE_AA)
        cv2.imwrite(str(folder/name.replace('_ground.png','_annotated.png')),canvas)
    render_turn_sweep(report, folder)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);args=p.parse_args()
    rows=[];summary=[]
    for path in sorted(args.root.rglob('report.json')):
        report=render(path);relative=path.relative_to(args.root);failed=[k for k,v in report.get('checks',{}).items() if not v]
        full=report.get('metrics',{}).get('full') or {};tail=report.get('metrics',{}).get('tail') or {}
        entry=dict(report=str(relative),course=report['course'],passed=report['passed'],failed_checks=failed,error=report.get('error'),termination=report.get('termination'),full=full,tail=tail)
        summary.append(entry)
        metric=lambda key: f"{full[key]*1000:.2f}" if key in full else '—'
        chart=relative.parent/'evaluation.png'
        sweep=relative.parent/'turn_sweep.png'
        rows.append('<tr>'+''.join('<td>'+cell+'</td>' for cell in [html.escape(str(relative.parent)), 'PASS' if report['passed'] else 'FAIL',metric('rms_m'),metric('p95_m'),metric('max_m'),html.escape(', '.join(failed) or report.get('error') or '—'),f'<a href="{relative}">JSON</a>'+(f' / <a href="{chart}">plot</a>' if (args.root/chart).exists() else '')+(f' / <a href="{sweep}">turn sweep</a>' if (args.root/sweep).exists() else '')])+'</tr>')
    (args.root/'summary.json').write_text(json.dumps(dict(runs=summary,total=len(summary),passed=sum(r['passed'] for r in summary)),indent=2)+'\n')
    page='''<!doctype html><meta charset="utf-8"><title>Isolated visual line validation</title>
<style>body{font:15px system-ui;margin:30px;color:#17222b}table{border-collapse:collapse}td,th{border:1px solid #ccd4db;padding:8px;text-align:left}th{background:#edf3f7}a{color:#1466a0}</style>
<h1>\u72ec\u7acb\u4f4e\u901f\u89c6\u89c9\u5faa\u7ebf / Isolated visual line validation</h1>
<p>\u5de5\u7a0b\u6d4b\u8bd5\u6761\u4ef6，\u975e\u6b63\u5f0f\u6bd4\u8d5b\u8d70\u5eca。Reference geometry is evaluation-only. All successes and failures are retained.</p>
<p>RMS and P95 are time-weighted; full-run errors include initial correction and corner phases. JSON includes phase metrics, observations, commands, stop reasons, captures and source/binary hashes.</p>
<table><tr><th>Run</th><th>Result</th><th>RMS mm</th><th>P95 mm</th><th>Max mm</th><th>Failed checks</th><th>Evidence</th></tr>'''+''.join(rows)+'</table>'
    (args.root/'index.html').write_text(page)
    print(f'{len(summary)} reports rendered in {args.root}')

if __name__=='__main__':main()
