"""Budget-only continuation; never drop or quality-retry a scheduled case."""
from copy import deepcopy
from course_project.extension import runner as r
from course_project.stage1 import read,write,sha,stamp
def main():
 name='travel_formal';d=sorted((r.ROOT/'runs/extension'/name).iterdir())[-1];s=read(d/'summary.json');original=read(d/'manifest.json')['protocol']
 assert s['completed']<s['expected_episodes']
 assert len(s['rows'])==s['completed']+1 and s['rows'][-1]['error_type']=='BudgetExceeded'
 offset=s['completed'];assert s['rows'][-1]['index']==offset
 for f,h in original['source_hashes'].items():
  if f.startswith('src/') or f in ['course_project/extension/runner.py','course_project/extension/pipelines.py','course_project/extension_review/travel.py','course_project/deepseek_adapter.py','course_project/interventions.py','course_project/run_pilot.py']:assert sha(r.ROOT/f)==h,f
 p=deepcopy(original);reserve=min(1.,round(100-r.prior_spending()-.02,6));assert reserve>0
 p.update(name='travel_budget_continuation',created_utc=stamp(),schedule=original['schedule'][offset:],expected_episodes=len(original['schedule'])-offset,original_index_offset=offset,parent_protocol_sha256=sha(r.HERE/name/'protocol.json'),prior_upper_cny=r.prior_spending(),source_hashes={str(f.relative_to(r.ROOT)):sha(f) for f in r.source_files()},payloads={str(int(i)-offset):v for i,v in original['payloads'].items() if int(i)>=offset},amendment='Budget-only continuation. Preserve all completed original cases and incomplete request cost. Retry budget-interrupted case in a fresh environment and then exact remaining frozen schedule. No changes to tasks, payloads, actor, model, metrics or trial count. Original local cap4.5CNY was below aggregate observed cost; cumulative cap100CNY unchanged.')
 p['config']['run_budget_cny']=reserve;target=r.HERE/p['name']/'protocol.json';assert not target.exists();write(target,p);print('Continuation frozen',p['expected_episodes'],'reserve',reserve);r.run(p['name'])
if __name__=='__main__':main()
