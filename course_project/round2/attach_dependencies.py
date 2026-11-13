"""Disclosed retrospective dependency supplement, never rewriting original snapshots."""
import subprocess
from pathlib import Path
from course_project.stage1 import ROOT,write,sha,stamp
PIN='62713c41'
# All legacy shared modules were tracked and unchanged at round2 launch.
subprocess.run(['git','diff','--exit-code',PIN,'--','course_project/extension'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
for d in sorted((ROOT/'runs/round2').glob('*/*')):
 if not (d/'manifest.json').exists() or (d/'dependency_manifest.json').exists():continue
 files=[f for f in (ROOT/'course_project/extension').glob('*.py') if not (d/'source_snapshot'/f.relative_to(ROOT)).exists()]
 if not files:continue
 paths={}
 for f in files:
  rel=str(f.relative_to(ROOT));data=subprocess.check_output(['git','show',PIN+':'+rel],cwd=ROOT);assert data==f.read_bytes()
  target=d/'dependency_snapshot'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);paths[rel]=sha(target)
 write(d/'dependency_manifest.json',dict(created_utc=stamp(),retrospective=True,source_commit=PIN,reason='New runner mistakenly omitted legacy extension modules from its original source_files list. Those modules were clean at initial round2 git status and unchanged from the pinned tracked commit throughout. Attach separately, preserve original manifest/snapshot, disclose timing; future protocols include dependencies prospectively.',paths=paths))
 print(d.name,len(paths))
