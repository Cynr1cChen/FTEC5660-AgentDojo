"""Hash-indexed supplemental archive with isolated offline replay."""
import argparse,hashlib,json,os,subprocess,tempfile,zipfile
from pathlib import Path
from dotenv import dotenv_values
from course_project.stage1 import ROOT,read,write,sha,stamp
ARCHIVE=ROOT/'course_project/evidence/round2_evidence.zip'
def build():
 assert not ARCHIVE.exists(),'Never overwrite an evidence archive'
 files=sorted(p for p in (ROOT/'runs/round2').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 key=dotenv_values(ROOT/'.env').get('DEEPSEEK_API_KEY','').encode();index={}
 for p in files:
  data=p.read_bytes();assert not key or key not in data,'Credential detected'
  index[str(p.relative_to(ROOT))]=hashlib.sha256(data).hexdigest()
 with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED) as z:
  for p in files:z.write(p,p.relative_to(ROOT))
 with zipfile.ZipFile(ARCHIVE) as z:assert z.testzip() is None
 cohorts=[]
 for p in sorted((ROOT/'runs/round2').glob('*/*/summary.json')):
  s=read(p);cohorts.append(dict(run=str(p.parent.relative_to(ROOT)),completed=s['completed'],planned=s['expected_episodes'],requests=s['api_calls'],audit_available=(p.parent/'audit.json').exists()))
 write(ARCHIVE.with_suffix('.manifest.json'),dict(created_utc=stamp(),sha256=sha(ARCHIVE),bytes=ARCHIVE.stat().st_size,secret_scan_passed=True,paths=index,cohorts=cohorts,scope='Round2 archive; earlier326-episode and587-episode archives remain separate. Failure attempts retained, not counted as empirical outcomes.'))
 print('Archived',len(files),'files;',ARCHIVE.stat().st_size,'bytes')
def verify():
 m=read(ARCHIVE.with_suffix('.manifest.json'));assert sha(ARCHIVE)==m['sha256']
 with tempfile.TemporaryDirectory(prefix='agentdojo_extension_package_') as td:
  root=Path(td).resolve()
  with zipfile.ZipFile(ARCHIVE) as z:
   assert set(z.namelist())==set(m['paths'])
   for name in z.namelist():
    target=(root/name).resolve();assert target.is_relative_to(root) and name.startswith('runs/round2/')
    data=z.read(name);assert hashlib.sha256(data).hexdigest()==m['paths'][name]
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  verified=[];incomplete=[]
  for c in m['cohorts']:
   if not c['audit_available']:incomplete.append(c);continue
   d=root/c['run'];old=read(d/'audit.json')
   subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'course_project/round2/replay.py'),str(d)],check=True,stdout=subprocess.DEVNULL)
   new=read(d/'audit.json');assert old['rows']==new['rows'];verified.append(c)
 write(ROOT/'course_project/round2/package_verification.json',dict(passed=True,created_utc=stamp(),archive_sha256=m['sha256'],isolated_extract=True,network_blocked_workers=True,uses_existing_dependencies=True,fresh_dependency_install=False,verified=verified,technical_attempts_not_replayed=incomplete))
 print('Isolated supplemental archive replay passed',len(verified),'cohorts')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['build','verify']);globals()[p.parse_args().action]()
