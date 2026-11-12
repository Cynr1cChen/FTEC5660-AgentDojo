"""Package, restore and verify recorded execution without paid API calls."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from dotenv import dotenv_values
from course_project.stage1 import ROOT,read,write,sha

PHASES=['stage1','supplement','comparison_dev','formal','date_followup']
ARCHIVE=ROOT/'course_project/evidence/recovery_evidence.zip'

def build():
    files=[]
    for phase in PHASES:
        d=sorted((ROOT/f'runs/{phase}').iterdir())[-1]
        assert (d/'audit.json').exists(),phase
        files.extend(p for p in d.rglob('*') if p.is_file())
    key=dotenv_values(ROOT/'.env').get('DEEPSEEK_API_KEY','')
    for p in files:
        if key:assert key.encode() not in p.read_bytes(),'Secret detected; packaging stopped'
    ARCHIVE.parent.mkdir(parents=True,exist_ok=True)
    assert not ARCHIVE.exists(),'Refuse to overwrite evidence archive'
    with zipfile.ZipFile(ARCHIVE,'w',zipfile.ZIP_DEFLATED) as z:
        for p in files:z.write(p,p.relative_to(ROOT))
    with zipfile.ZipFile(ARCHIVE) as z:assert z.testzip() is None
    write(ARCHIVE.with_suffix('.manifest.json'),dict(sha256=sha(ARCHIVE),bytes=ARCHIVE.stat().st_size,
        paths={str(p.relative_to(ROOT)):sha(p) for p in files},secret_scan_passed=True,
        use='Recorded public synthetic benchmark data; no API keys; verify does not generate model answers.'))
    print('Evidence bytes:',ARCHIVE.stat().st_size)

def restore(root=ROOT):
    manifest=read(ARCHIVE.with_suffix('.manifest.json'));assert sha(ARCHIVE)==manifest['sha256']
    with zipfile.ZipFile(ARCHIVE) as z:
        names=z.namelist();assert set(names)==set(manifest['paths'])
        for name in names:
            p=(root/name).resolve()
            assert p.is_relative_to(root.resolve()) and name.startswith('runs/')
            assert not p.exists(),'Refuse to overwrite: '+name
            assert hashlib.sha256(z.read(name)).hexdigest()==manifest['paths'][name]
        for name in names:
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(name))

def verify():
    # Separate directory, existing interpreter/dependencies. Not a clean reinstall.
    with tempfile.TemporaryDirectory(prefix='agentdojo_replay_') as td:
        target=Path(td)/'checkout';target.mkdir()
        shutil.copytree(ROOT/'src',target/'src',ignore=shutil.ignore_patterns('__pycache__'))
        for p in (ROOT/'course_project').rglob('*'):
            rel=p.relative_to(ROOT)
            if not p.is_file() or p.suffix not in ['.py','.json']:continue
            if any(x in rel.parts for x in ['tmp','local_reruns','__pycache__']):continue
            q=target/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
        restore(target)
        env={**os.environ,'PYTHONPATH':str(target/'src')+os.pathsep+str(target),'PYTHONDONTWRITEBYTECODE':'1'}
        commands=[['-c',"import runpy; runpy.run_path('course_project/stage1/verify_development.py',run_name='__main__')"],
                  ['-m','course_project.audit_controlled','supplement'],
                  ['-m','course_project.audit_controlled','comparison_dev'],
                  ['-m','course_project.formal_audit','formal'],
                  ['-m','course_project.formal_audit','date_followup'],
                  ['-m','course_project.results_formal','formal'],
                  ['-m','course_project.results_formal','date_followup']]
        for command in commands:
            subprocess.run([str(ROOT/'.venv/bin/python'),*command],cwd=target,env=env,check=True,
                           stdout=subprocess.DEVNULL)
        for phase in ['formal','date_followup']:
            a=read(ROOT/f'course_project/{phase}/results.json');b=read(target/f'course_project/{phase}/results.json')
            for x in [a,b]:
                for key in ['created_utc','audit_sha256']:x.pop(key,None)
            assert a==b,'Recomputed result mismatch: '+phase
        write(ROOT/'course_project/evidence/verification.json',dict(passed=True,
            isolated_directory=True,uses_existing_dependencies=True,fresh_dependency_install=False,
            phases=PHASES,all_requests_and_states_replayed=True,formal_aggregates_identical=True,
            archive_sha256=sha(ARCHIVE)))
        print('Isolated saved-evidence verification passed; no paid API calls.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['build','restore','verify'])
    a=p.parse_args();globals()[a.action]()
