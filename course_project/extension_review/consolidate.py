"""Audited cohort aggregation; preserve incomplete attempts and original rows."""
import json,statistics as st
from pathlib import Path
from course_project.stage1 import ROOT,read,write,sha,stamp
HERE=ROOT/'course_project/extension_review'
def aggregate(name,dirs):
 rows=[];cost=0;calls=0
 for d in dirs:
  a=read(d/'audit.json');assert a['passed'];s=read(d/'summary.json');assert a['rows']==[r for r in s['rows'] if r['status']=='completed']
  rows.extend(a['rows']);cost+=s['peak_upper_cny'];calls+=s['api_calls']
 arms={}
 for arm in sorted({r['arm'] for r in rows}):
  metrics={}
  for phase in ['clean','attacked']:
   xs=[r for r in rows if r['arm']==arm and r['phase']==phase]
   if not xs:continue
   metrics[phase]={}
   for key,fn in [('native_utility',lambda r:r['utility']),('strict_safe',lambda r:r['supplemental']['strict_utility'] and not r['attack_success'] and not r['supplemental'].get('unauthorized')),('attack_success',lambda r:r['attack_success'] is True)]:
    vals=[st.mean(bool(fn(r)) for r in xs if r['trial']==t) for t in sorted({r['trial'] for r in xs})]
    metrics[phase][key]=dict(count=sum(bool(fn(r)) for r in xs),n=len(xs),trial_values=vals,mean=st.mean(vals),sample_sd=st.stdev(vals) if len(vals)>1 else None,sample_variance=st.variance(vals) if len(vals)>1 else None)
  rs=[r for r in rows if r['arm']==arm];arms[arm]=dict(metrics=metrics,mean_calls=st.mean(r['api_calls'] for r in rs))
 write(HERE/(name+'_results.json'),dict(created_utc=stamp(),runs=[str(d.relative_to(ROOT)) for d in dirs],audit_hashes=[sha(d/'audit.json') for d in dirs],episodes=len(rows),requests=calls,peak_upper_cny=cost,arms=arms,notes='Repeated API trials on fixed tasks, not independent task populations. Native utility and strict safe completion are separate. Development confirmation is not held-out.',rows=rows))
 return arms
if __name__=='__main__':
 import sys
 name=sys.argv[1];merged={'workspace_merged':['workspace_formal','workspace_budget_continuation'],'travel_merged':['travel_formal','travel_budget_continuation']};names=merged.get(name,[name])
 dirs=[sorted((ROOT/'runs/extension'/n).iterdir())[-1] for n in names]
 if name in merged:
  parent=read(ROOT/f'course_project/extension/{names[0]}/protocol.json');cont=read(ROOT/f'course_project/extension/{names[1]}/protocol.json')
  assert cont['parent_protocol_sha256']==sha(ROOT/f'course_project/extension/{names[0]}/protocol.json') and cont['schedule']==parent['schedule'][cont['original_index_offset']:]
  rs=[r for d in dirs for r in read(d/'audit.json')['rows']]
  keys=[tuple(r.get(k) for k in ['trial','task','phase','arm','attack','goal']) for r in rs]
  assert len(keys)==len(set(keys))==len(parent['schedule'])
  assert all(all(r[k]==v for k,v in c.items()) for r,c in zip(rs,parent['schedule']))
  assert all(parent['payloads'][str(int(i)+cont['original_index_offset'])]==v for i,v in cont['payloads'].items())
 print(json.dumps(aggregate(name,dirs),indent=2))
