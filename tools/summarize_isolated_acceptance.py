#!/usr/bin/env python3
"""Summarize completed frozen trials; never infer a pass from partial coverage."""
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    args=parser.parse_args()
    tracking=[];faults=[];missing=[];by_scene={}
    for name,expected in [('final_curves',24),('final_turns',18),('final_faults',12)]:
        path=args.root/name/'manifest.json'
        if not path.exists():missing.append(dict(suite=name,completed=0,expected=expected));continue
        manifest=json.loads(path.read_text())
        if len(manifest['runs'])!=expected:missing.append(dict(suite=name,completed=len(manifest['runs']),expected=expected))
        for run in manifest['runs']:
            report_path=Path(run['report']);report=json.loads(report_path.read_text())
            entry=dict(suite=name,case=run['case'],course=run['scene'],passed=report['passed'],
                report=str(report_path),failed_checks=[k for k,v in report['checks'].items() if not v],
                error=report.get('error'),termination=report.get('termination'),metrics=report.get('metrics'),
                fault=report.get('fault'),binary_sha256=report.get('binary_sha256'),
                observation_age=report.get('max_observation_age_s'),acceleration=report.get('command_acceleration'))
            if name=='final_faults':faults.append(entry)
            else:tracking.append(entry);by_scene.setdefault(run['scene'],[]).append(entry)
    scenes={}
    for name,runs in by_scene.items():
        usable=[r for r in runs if r.get('metrics') and r['metrics'].get('full')]
        scenes[name]=dict(passed=sum(r['passed'] for r in runs),total=len(runs),
            worst_full_rms_mm=max((r['metrics']['full']['rms_m']*1000 for r in usable),default=None),
            worst_full_p95_mm=max((r['metrics']['full']['p95_m']*1000 for r in usable),default=None),
            worst_full_max_mm=max((r['metrics']['full']['max_m']*1000 for r in usable),default=None),
            worst_tail_rms_mm=max((r['metrics']['tail']['rms_m']*1000 for r in usable if r['metrics'].get('tail')),default=None),
            worst_swept_bound_mm=max((r['metrics']['max_swept_distance_m']*1000 for r in usable),default=None))
    binaries=[json.dumps(r['binary_sha256'],sort_keys=True) for r in tracking+faults]
    source_path=args.root/'final_source/manifest.json'
    source=json.loads(source_path.read_text()) if source_path.exists() else {}
    source_matches=all(Path(p).exists() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in source.items())
    summary=dict(complete=not missing and len(tracking)==42 and len(faults)==12,
        passed=not missing and len(tracking)==42 and len(faults)==12 and all(r['passed'] for r in tracking+faults),
        tracking=dict(passed=sum(r['passed'] for r in tracking),total=len(tracking)),
        faults=dict(passed=sum(r['passed'] for r in faults),total=len(faults)),
        one_binary_version=bool(binaries) and len(set(binaries))==1,
        source_snapshot_matches_workspace=bool(source) and source_matches,
        missing=missing,scenes=scenes,trials=tracking,fault_trials=faults,
        failed_trials=[r for r in tracking+faults if not r['passed']])
    (args.root/'final_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('trials','fault_trials','failed_trials')},indent=2))
    return 0 if summary['complete'] else 1

if __name__=='__main__':raise SystemExit(main())
