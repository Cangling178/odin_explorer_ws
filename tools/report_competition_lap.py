#!/usr/bin/env python3
"""Render an existing lap result without changing samples or acceptance criteria."""
import argparse,html,json
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',type=Path);args=parser.parse_args()
    report=json.loads((args.directory/'report.json').read_text())
    rows=''.join(f'<tr><td>{html.escape(key)}</td><td>{html.escape(str(value))}</td></tr>' for key,value in report['checks'].items())
    metrics=report.get('metrics',{})
    states=[event for event in report['events'] if event['state']=='RUNNING' or event['state']=='FINISHED' or event['state'].startswith('STOPPED')]
    content=f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>Competition lap acceptance</title>
<style>body{{font:16px system-ui;max-width:1100px;margin:36px auto;padding:0 20px;color:#182331;background:#f8fafc}}h1{{font-size:30px}}table{{border-collapse:collapse;width:100%;background:white}}td{{padding:9px;border-bottom:1px solid #ddd}}img{{width:100%;background:white}}pre{{white-space:pre-wrap;background:#eef2f6;padding:18px}}a{{color:#1665ac}}</style>
<h1>Continuous competition lap: {'PASS' if report['passed'] else 'FAIL'}</h1>
<p>Gazebo simulation. Ordered image-derived map, onboard vision and wheel odometry. C++ runtime; independent Python evaluator.</p>
<img src="trajectory.png" alt="Map line, independently measured axle trajectory, physical speed and line error">
<h2>Measured result</h2><pre>{html.escape(json.dumps(metrics,indent=2))}</pre>
<h2>Acceptance checks</h2><table>{rows}</table>
<h2>Criteria fixed before the run</h2><pre>{html.escape(json.dumps(report['criteria'],indent=2))}</pre>
<p>Startup exclusion: first 1 s. Finish braking is separate. The maximum 100 mm axle error limit is an engineering criterion, not an assertion that the axle stays inside the 21 mm stroke.</p>
<h2>Run state transitions</h2><pre>{html.escape(json.dumps(states,indent=2))}</pre>
<p><a href="report.json">Full measurements, commands and hashes</a> · <a href="launch.log">Launch log</a></p>
</html>'''
    (args.directory/'index.html').write_text(content)
    print(args.directory/'index.html')
if __name__=='__main__':main()
