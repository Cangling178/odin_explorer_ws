#!/usr/bin/env python3
"""Repeat complete laps in independently started Gazebo instances, preserving every attempt."""
import argparse
import hashlib
import html
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def audit_commands(report):
    """Inspect every received command, including commands between pose samples."""
    events = report.get('events', [])
    starts = [event['time'] for event in events if event['state'] == 'RUNNING']
    finishes = [event['time'] for event in events if event['state'] == 'FINISHED']
    if not starts or not finishes:
        return dict(passed=False, count=0, reason='Missing running/finished interval')
    begin = starts[0] + report['criteria'].get('startup_exclusion_s', 1.)
    end = finishes[-1]
    commands = [command for command in report.get('commands', []) if begin < command['time'] < end]
    bad = [command for command in commands if not math.isfinite(command['v']) or command['v'] <= 0]
    return dict(passed=bool(commands) and not bad, count=len(commands), nonpositive_or_invalid=len(bad))


def summarize(reports, requested):
    completed = [item for item in reports if item.get('report') is not None]
    passed = sum(item.get('exit_code') == 0 and item['report'].get('passed') is True
                 for item in completed)
    signatures = [dict(binary=item['report'].get('binary_sha256'),
                       source=item['report'].get('source_sha256'),
                       criteria=item['report'].get('criteria')) for item in completed]
    same = bool(signatures) and all(all(signature.values()) and signature == signatures[0] for signature in signatures)
    complete = len(reports) == requested
    return dict(requested=requested, attempted=len(reports), reports=len(completed),
                passed_runs=passed, identical_version_and_criteria=same,
                complete=complete, passed=complete and len(completed) == requested and passed == requested and same
                and all(audit_commands(item['report'])['passed'] for item in completed),
                runs=[dict(run=item['run'], exit_code=item['exit_code'],
                           passed=item.get('report', {}).get('passed', False) if item.get('report') else False,
                           termination=item.get('report', {}).get('termination') if item.get('report') else None,
                           error=item.get('error') or (item.get('report') or {}).get('error'),
                           metrics=(item.get('report') or {}).get('metrics'),
                           command_audit=audit_commands(item['report']) if item.get('report') else None) for item in reports],
                signature=signatures[0] if signatures else None)


def write_summary(directory, reports, requested):
    summary = summarize(reports, requested)
    (directory/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    rows = []
    for run in summary['runs']:
        metrics = run['metrics'] or {}
        rows.append('<tr><td><a href="{0}/index.html">{0}</a></td><td>{1}</td>'
                    '<td>{2}</td><td>{3}</td><td>{4}</td><td>{5}</td></tr>'.format(
                        html.escape(run['run']), 'PASS' if run['passed'] and run['exit_code'] == 0 and run['command_audit']['passed'] else 'FAIL',
                        metrics.get('duration_s', '—'),
                        round(metrics.get('rms_error_m', 0)*1000, 2) if metrics else '—',
                        round(metrics.get('max_error_m', 0)*1000, 2) if metrics else '—',
                        round(metrics.get('min_moving_speed_mps', 0)*1000, 2) if metrics else '—'))
    state = 'PASS' if summary['passed'] else 'FAIL' if summary['complete'] else 'IN PROGRESS'
    (directory/'index.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<title>Repeated competition laps</title><style>body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 20px;color:#182331}table{border-collapse:collapse;width:100%}td,th{padding:12px;text-align:left;border-bottom:1px solid #ddd}a{color:#1665ac}</style>
<h1>Repeated independent laps: '''+state+'''</h1><p>Fixed map, route, parameters and acceptance limits; each trial starts a new simulator. Every received mid-lap forward command is also audited for a positive value.</p>
<p>Passing trials: '''+str(summary['passed_runs'])+'/'+str(requested)+'''. This measures repeatability at the nominal start, not robustness to arbitrary disturbances.</p>
<table><tr><th>Run</th><th>Result</th><th>Time (s)</th><th>RMS (mm)</th><th>Max error (mm)</th><th>Min moving speed (mm/s)</th></tr>'''+''.join(rows)+'''</table>
<p><a href="summary.json">Summary and version signatures</a> · <a href="manifest.json">Frozen inputs</a></p></html>''')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--runs', type=int, default=3)
    parser.add_argument('--domain', type=int, default=101)
    parser.add_argument('--port', type=int, default=11401)
    args = parser.parse_args()
    if not 1 <= args.runs <= 10 or args.domain + args.runs > 230:
        parser.error('Use 1–10 trials within the ROS domain range')
    if args.output.exists():
        parser.error('Output already exists; preserve prior attempts with a new directory')
    args.output.mkdir(parents=True)
    paths = list((ROOT/'src/odin_racer/racer_control').rglob('*.cpp'))
    paths += list((ROOT/'src/odin_racer/racer_control').rglob('*.hpp'))
    paths += list((ROOT/'src/odin_racer/racer_control/config').glob('competition_lap.*'))
    paths += [ROOT/'src/odin_racer/racer_bringup/launch/competition_lap.launch.py',
              ROOT/'src/odin_racer/racer_perception/src/line_perception.cpp',
              ROOT/'src/odin_racer/racer_perception/include/racer_perception/line_geometry.hpp',
              ROOT/'src/odin_racer/racer_perception/config/line_perception.yaml',
              ROOT/'src/odin_racer/racer_bringup/config/line_fastdds.xml',
              ROOT/'install/racer_control/lib/racer_control/lap_controller',
              ROOT/'install/racer_perception/lib/racer_perception/line_perception']
    fingerprint = lambda: {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    frozen = fingerprint()
    (args.output/'manifest.json').write_text(json.dumps(frozen, indent=2)+'\n')
    reports = []
    write_summary(args.output, reports, args.runs)
    for i in range(args.runs):
        if fingerprint() != frozen:
            raise RuntimeError('Runtime inputs changed during the repeat matrix')
        name = f'run_{i+1:02d}'
        directory = args.output/name
        print(f'Starting {name}/{args.runs}', flush=True)
        command = [sys.executable, str(ROOT/'tools/validate_competition_lap.py'),
                   '--output', str(directory), '--domain', str(args.domain+i), '--port', str(args.port+i)]
        with (args.output/(name+'.log')).open('w') as log:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                log.write(line);log.flush();print(name+': '+line, end='', flush=True)
            code = process.wait()
        report_file = directory/'report.json'
        item = dict(run=name, exit_code=code, report=None)
        if report_file.exists():
            item['report'] = json.loads(report_file.read_text())
            subprocess.run([sys.executable, str(ROOT/'tools/report_competition_lap.py'), str(directory)], check=True)
        else:
            item['error'] = 'No completed report; inspect the retained trial log'
        reports.append(item)
        summary = write_summary(args.output, reports, args.runs)
        print(f'Completed {name}: {summary["passed_runs"]}/{len(reports)} passed so far', flush=True)
    if fingerprint() != frozen:
        raise RuntimeError('Runtime inputs changed during the repeat matrix')
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
