"""Descriptive repeated-trial analysis; separate cohorts and event metrics."""
import argparse,statistics as st
from pathlib import Path
from course_project.stage1 import ROOT,read,write,sha,stamp

def stats(v):return dict(values=v,mean=st.mean(v) if v else None,sample_sd=st.stdev(v) if len(v)>1 else None,sample_variance=st.variance(v) if len(v)>1 else None,n=len(v))
def analyze(name):
 d=sorted((ROOT/'runs/extension'/name).iterdir())[-1];a=read(d/'audit.json');p=read(d/'manifest.json')['protocol'];rows=a['rows'];out={}
 for arm in sorted({r['arm'] for r in rows}):
  subset=[r for r in rows if r['arm']==arm];trials=sorted({r['trial'] for r in subset});metrics={}
  for metric,phase,fn in [('clean_utility','clean',lambda r:r['utility']),('clean_strict','clean',lambda r:r['supplemental']['strict_utility']),
   ('attacked_utility','attacked',lambda r:r['utility']),('attacked_safe','attacked',lambda r:r['utility'] and not r['attack_success'] and not r['supplemental'].get('unauthorized')),
   ('attacked_strict_safe','attacked',lambda r:r['supplemental']['strict_utility'] and not r['attack_success'] and not r['supplemental'].get('unauthorized')),
   ('native_ASR','attacked',lambda r:r['attack_success']),('unauthorized_events','attacked',lambda r:r['supplemental'].get('unauthorized') is True)]:
   if metric=='unauthorized_events' and not any(r.get('supplemental',{}).get('unauthorized') is not None for r in subset):continue
   values=[]
   for trial in trials:
    sub=[r for r in subset if r['trial']==trial and r['phase']==phase]
    if sub:values.append(sum(bool(fn(r)) for r in sub)/len(sub))
   if values:metrics[metric]=stats(values)
  out[arm]=dict(episodes=len(subset),metrics=metrics,mean_calls=st.mean(r['api_calls'] for r in subset),peak_upper_cny=sum(r['peak_upper_cny'] for r in subset))
 bytask={}
 for suite,task in sorted({(r['suite'],r['task']) for r in rows if r['phase']!='capability'}):
  bytask[suite+'/'+task]={}
  for arm in out:
   x=[r for r in rows if r['suite']==suite and r['task']==task and r['arm']==arm and r['phase']=='attacked']
   if x:bytask[suite+'/'+task][arm]=dict(n=len(x),utility=sum(r['utility'] for r in x),native_attack_success=sum(r['attack_success'] for r in x),unauthorized=sum(r['supplemental'].get('unauthorized') is True for r in x))
 result=dict(created_utc=stamp(),name=name,completed=True,run=str(d.relative_to(ROOT)),protocol_sha256=sha(ROOT/f'course_project/extension/{name}/protocol.json'),audit_sha256=sha(d/'audit.json'),arms=out,by_task=bytask,
  cost={k:a[k] for k in ['known_offpeak_cny','peak_upper_cny']},all_attacks_exposed=a['all_attacks_exposed'],scope='Fixed task IDs, repeated API draws. Trials are not independent tasks. Development attack selection is not formal efficacy.',rows=rows)
 write(ROOT/f'course_project/extension/{name}/results.json',result)
 print({k:v for k,v in result.items() if k not in ['rows','by_task']})
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('name');v=a.parse_args();analyze(v.name)
