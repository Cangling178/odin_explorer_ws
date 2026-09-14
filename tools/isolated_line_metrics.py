"""Independent truth evaluator. Never imported by perception/control nodes."""
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial import cKDTree
from racer_description.contact_world import build_world, transform


def footprint(share):
    """Conservative filled XY envelope of ALL current collision primitives.

    Uses each SDF collision in the existing physical model. Bounding-box filling
    overestimates cutouts. Wheel rotation leaves cylindrical extents unchanged.
    Every point in the envelope is within sqrt(2)*5 mm of the 10 mm grid.
    """
    model = ET.fromstring(build_world(share)).find("world/model[@name='odin_racer']")
    corners = []
    def frame(node):
        values = (node.findtext('pose') or '0 0 0 0 0 0').split()
        return transform(ET.Element('origin', xyz=' '.join(values[:3]), rpy=' '.join(values[3:])))
    for link in model.findall('link'):
        for collision in link.findall('collision'):
            shape = list(collision.find('geometry'))[0]
            if shape.tag == 'box':
                half = np.fromstring(shape.findtext('size'), sep=' ')/2
            elif shape.tag == 'cylinder':
                r = float(shape.findtext('radius'))
                half = np.array([r, r, float(shape.findtext('length'))/2])
            elif shape.tag == 'sphere':
                half = np.full(3, float(shape.findtext('radius')))
            else:
                raise ValueError('Unsupported collision shape: '+shape.tag)
            tf = frame(link) @ frame(collision)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    for sz in (-1, 1):
                        corners.append((tf @ np.r_[half*[sx, sy, sz], 1])[:2])
    lo, hi = np.min(corners, axis=0), np.max(corners, axis=0)
    x, y = [np.linspace(a, b, math.ceil((b-a)/.01)+1) for a,b in zip(lo,hi)]
    xx, yy = np.meshgrid(x,y)
    return np.c_[xx.ravel(), yy.ravel()], dict(min=lo.tolist(), max=hi.tolist(), covering_radius_m=math.sqrt(2)*.005)


class Evaluator:
    def __init__(self, fixture, footprint_points):
        self.fixture = fixture
        self.path = np.array(fixture['reference'])
        self.delta = np.diff(self.path, axis=0)
        self.length = np.linalg.norm(self.delta, axis=1)
        self.s = np.r_[0, np.cumsum(self.length)]
        self.tree = cKDTree(self.path)
        self.footprint = footprint_points
        self.start_s = self.project([0,0])[1]
        self.end_s = self.project(fixture['end']['center'])[1]

    def project(self, xy):
        d = np.array(xy)-self.path[:-1]
        t = np.clip(np.sum(d*self.delta, axis=1)/np.maximum(self.length**2,1e-15), 0, 1)
        diff = d-t[:,None]*self.delta
        i = int(np.argmin(np.sum(diff**2,axis=1)))
        cross = self.delta[i,0]*diff[i,1]-self.delta[i,1]*diff[i,0]
        return float(np.linalg.norm(diff[i]))*(1 if cross>=0 else -1), float(self.s[i]+t[i]*self.length[i])

    def sample(self, x, y, yaw):
        error, progress = self.project([x,y])
        c,s=math.cos(yaw),math.sin(yaw)
        body = self.footprint @ np.array([[c,s],[-s,c]]) + [x,y]
        # Nearest discrete reference gives an upper bound on distance to the
        # continuous polyline; add grid covering radius to cover filled body.
        swept = float(np.max(self.tree.query(body)[0]))+math.sqrt(2)*.005
        end=self.fixture['end']
        heading_error=math.atan2(math.sin(yaw-end['yaw']),math.cos(yaw-end['yaw']))
        return dict(error=error, progress=progress-self.start_s, swept_distance=swept,
                    at_end=math.dist([x,y],end['center'])<=end['radius'] and abs(heading_error)<.25
                    and progress>=self.end_s-end['radius'])


def error_stats(samples):
    if len(samples)<2:
        return None
    t=np.array([s['time'] for s in samples]); e=np.abs([s['error'] for s in samples])
    dt=np.array([s.get('sample_dt', t[i]-t[i-1] if i else t[1]-t[0]) for i,s in enumerate(samples)])
    if np.any(dt<=0) or not np.isfinite(dt).all():
        return None
    order=np.argsort(e); cumulative=np.cumsum(dt[order])/np.sum(dt)
    return dict(rms_m=float(np.sqrt(np.sum(e**2*dt)/np.sum(dt))),
                p95_m=float(e[order[min(np.searchsorted(cumulative,.95),len(order)-1)]]),
                max_m=float(np.max(e)))


def summarize(samples, criteria, course, fixture=None):
    if len(samples)<3:
        return {}, {'enough_samples':False}
    full=error_stats(samples)
    tail=error_stats([s for s in samples if s['time']>=samples[-1]['time']*.7])
    max_gap=max(b['time']-a['time'] for a,b in zip(samples,samples[1:]))
    # Conservative between-sample translation + rotation cover, for a 0.30 m
    # radius enclosing the independently derived current vehicle envelope.
    motion_cover=max_gap*.5*(max(s.get('speed',criteria['speed_max_mps']) for s in samples)+.30*max(abs(s.get('yaw_rate',criteria['yaw_rate_max_radps'])) for s in samples))
    metrics=dict(full=full, tail=tail, phases={}, sampling_motion_cover_m=motion_cover,
                 max_swept_distance_m=max(s['swept_distance'] for s in samples)+motion_cover)
    for phase in ('initial','tracking','corner'):
        group=[s for s in samples if ('corner' if s['state'] in ('APPROACH','CORNER_STOP','TURN','REACQUIRE') else 'initial' if s['progress']<.3 else 'tracking')==phase]
        metrics['phases'][phase]=error_stats(group)
    ds=np.diff([s['progress'] for s in samples])
    checks=dict(reached_end=any(s['at_end'] for s in samples),
                no_fault_stop=not any(s['state'].startswith('STOPPED') for s in samples),
                ordered_progress=bool(np.min(ds)>-.01 and np.max(ds)<criteria['max_progress_jump_m']),
                full_rms=full['rms_m']<criteria['full_rms_max_m'],
                full_p95=full['p95_m']<criteria['full_p95_max_m'],
                full_max=full['max_m']<criteria['full_max_error_m'],
                corridor=metrics['max_swept_distance_m']<=criteria['corridor_half_width_m'],
                command_bounds=all(-1e-8<=s['cmd_v']<=criteria['speed_max_mps']+1e-6 and abs(s['cmd_w'])<=criteria['yaw_rate_max_radps']+1e-6 for s in samples))
    metrics['max_nearest_projection_jump_m']=float(np.max(np.abs(ds)))
    if fixture is not None and all('x' in s and 'y' in s for s in samples):
        # Nearest arc coordinates are discontinuous on the bisector of a sharp
        # L: a continuous 2 mm body movement can switch between two projections
        # 160 mm apart. Do not mistake that coordinate singularity for teleporting.
        # Validate route order independently with sequential geometric gates and
        # apply the frozen 50 mm jump limit to actual consecutive body positions.
        evaluator=Evaluator(fixture,np.array([[0.,0.]]))
        stations=np.arange(evaluator.start_s,evaluator.end_s,.10)
        gates=np.c_[np.interp(stations,evaluator.s,evaluator.path[:,0]),
                    np.interp(stations,evaluator.s,evaluator.path[:,1])]
        visited=0
        for sample in samples:
            while visited<len(gates) and math.dist([sample['x'],sample['y']],gates[visited])<=criteria['full_max_error_m']:
                visited+=1
        jumps=[math.dist([a['x'],a['y']],[b['x'],b['y']]) for a,b in zip(samples,samples[1:])]
        metrics['route_gates']=dict(visited=visited,total=len(gates),spacing_m=.10,radius_m=criteria['full_max_error_m'])
        metrics['max_body_position_step_m']=max(jumps)
        checks['ordered_progress']=visited==len(gates) and max(jumps)<criteria['max_progress_jump_m']
    if course in ('line_straight','line_arc','line_left','line_right'):
        checks['regression_tail']=tail is not None and tail['rms_m']<criteria['regression_tail_rms_max_m']
    return metrics,checks
