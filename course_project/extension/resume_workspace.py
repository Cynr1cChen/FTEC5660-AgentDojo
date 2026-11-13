"""Prospective budget-only continuation; retain successful original episodes."""
from copy import deepcopy
from course_project.extension import runner as r
from course_project.stage1 import read,write,sha,stamp

def main():
 original=read(r.HERE/'workspace_formal/protocol.json')
 d=sorted((r.ROOT/'runs/extension/workspace_formal').iterdir())[-1];s=read(d/'summary.json')
 assert s['completed']==151 and s['rows'][-1]['index']==151 and s['rows'][-1]['error_type']=='BudgetExceeded'
 cases=original['schedule'][151:];assert len(cases)==29
 # Scientific intervention/adapter/native code remains byte-identical.
 actor_files=['course_project/extension/pipelines.py','course_project/deepseek_adapter.py','course_project/run_pilot.py']
 actor_files += [f for f in original['source_hashes'] if f.startswith('src/')]
 for f in actor_files:assert sha(r.ROOT/f)==original['source_hashes'][f],f
 name='workspace_budget_continuation';target=r.HERE/name/'protocol.json';assert not target.exists()
 p=deepcopy(original);p.update(name=name,created_utc=stamp(),schedule=cases,expected_episodes=29,
  prior_upper_cny=r.prior_spending(),source_hashes={str(f.relative_to(r.ROOT)):sha(f) for f in r.source_files()},
  parent_protocol_sha256=sha(r.HERE/'workspace_formal/protocol.json'),original_index_offset=151,
  payloads={str(i):original['payloads'][str(i+151)] for i,c in enumerate(cases) if c['phase']=='attacked'},
  amendment='Budget-only continuation after local8CNY reservation cap. First151 completed cases retained; failed index151 reruns from a fresh environment. No outcome-based task/attack/prompt selection. Exact original remaining schedule and payloads; same actor code. Costs of incomplete work retained.')
 p['config']['run_budget_cny']=3;assert r.prior_spending()+3<=100
 write(target,p);print(dict(frozen=True,episodes=29,prior_upper_cny=p['prior_upper_cny'],reserve=3))
if __name__=='__main__':main()
