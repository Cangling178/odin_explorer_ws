#!/usr/bin/env python3
"""Fixed-parameter acceptance matrix. Every attempt gets a unique directory."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
SCENES=['line_straight','line_arc','line_left','line_right','line_s','line_corner_left','line_corner_right']

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--domain',type=int,default=94);p.add_argument('--port',type=int,default=11394)
    p.add_argument('--scenes',nargs='+',choices=SCENES,default=SCENES)
    p.add_argument('--faults',action='store_true')
    p.add_argument('--center-repeat',type=int,default=2)
    args=p.parse_args()
    if args.center_repeat<1:p.error('center-repeat must be at least one')
    args.output.mkdir(parents=True,exist_ok=True)
    config_path=ROOT/'experiments/isolated_line/acceptance.json';criteria=json.loads(config_path.read_text())
    files=[config_path,ROOT/'tools/validate_isolated_line.py',ROOT/'tools/isolated_line_metrics.py',ROOT/'src/odin_racer/racer_description/racer_description/course_world.py',ROOT/'src/odin_racer/racer_description/racer_description/drive_world.py']+[f for package in ('racer_control','racer_perception') for f in (ROOT/'src/odin_racer'/package).rglob('*') if f.is_file() and f.suffix in ('.hpp','.cpp','.yaml')]
    frozen={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
    manifest=dict(started=time.strftime('%Y-%m-%dT%H:%M:%S%z'),frozen_sha256=frozen,runs=[])
    jobs=[]
    if args.faults:
        jobs=[dict(scene='line_corner_left',name=phase+'_'+fault,pose={'spawn_y':0,'spawn_yaw':0},extra=['--fault',fault,'--fault-phase',phase]) for phase in ('RUNNING','APPROACH','TURN') for fault in ('drop','blank','tf','odom')]
    else:
        for scene in args.scenes:
            for pose in criteria['initial_conditions']:
                for repeat in range(args.center_repeat if pose['name']=='center' else 1):
                    jobs.append(dict(scene=scene,name=pose['name']+f'_{repeat+1}',pose=pose,extra=[]))
    for job in jobs:
        for relative,digest in frozen.items():
            if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=digest:
                raise RuntimeError('Parameters/source changed during fixed acceptance: '+relative)
        directory=args.output/job['scene']/job['name']
        command=[sys.executable,str(ROOT/'tools/validate_isolated_line.py'),'--course',job['scene'],'--output',str(directory),
                 '--spawn-y',str(job['pose']['spawn_y']),'--spawn-yaw',str(job['pose']['spawn_yaw']),
                 '--domain',str(args.domain),'--port',str(args.port),*job['extra']]
        with (args.output/(job['scene']+'_'+job['name']+'.log')).open('x') as log:
            result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
        path=directory/'report.json';report=json.loads(path.read_text()) if path.exists() else {}
        entry=dict(scene=job['scene'],case=job['name'],exit_code=result.returncode,report=str(path),passed=report.get('passed',False),error=report.get('error'),failed_checks=[k for k,v in report.get('checks',{}).items() if not v])
        manifest['runs'].append(entry);(args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print(json.dumps(entry),flush=True)
    manifest['passed']=bool(manifest['runs']) and all(r['passed'] for r in manifest['runs'])
    (args.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return 0 if manifest['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
