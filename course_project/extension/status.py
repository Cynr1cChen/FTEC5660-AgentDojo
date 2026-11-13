"""Compact read-only progress and cumulative conservative accounting."""
from pathlib import Path
import json
from course_project.stage1 import ROOT
from course_project.extension.runner import prior_spending
for p in sorted((ROOT/'runs/extension').glob('*/*/manifest.json')):
 d=p.parent;m=json.loads(p.read_text());rows=[json.loads(f.read_text()) for f in sorted((d/'episodes').glob('*/result.json'))]
 attacked=[r for r in rows if r['phase']=='attacked' and r['status']=='completed']
 print(dict(name=m['protocol']['name'],run=d.name,completed=sum(r['status']=='completed' for r in rows),planned=m['protocol']['expected_episodes'],errors=[r['error_type'] for r in rows if r['status']!='completed'],attack_success=sum(r['attack_success'] for r in attacked),unauthorized=sum(r.get('supplemental',{}).get('unauthorized') is True for r in attacked),finished=(d/'summary.json').exists()))
print('PROJECT CONSERVATIVE UPPER CNY',prior_spending())
