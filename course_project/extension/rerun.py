"""Fresh sampling from a published extension plan; dry-run is default."""
import argparse,copy
from datetime import datetime,timezone
from course_project.extension import runner as r
from course_project.stage1 import read,write,sha,stamp

def main():
 a=argparse.ArgumentParser();a.add_argument('phase');a.add_argument('--budget-cny',type=float,default=8);a.add_argument('--live',action='store_true');v=a.parse_args()
 p=copy.deepcopy(read(r.HERE/v.phase/'protocol.json'));assert 0<v.budget_cny<=10
 if not v.live:print(dict(dry_run=True,phase=v.phase,episodes=p['expected_episodes'],budget_cny=v.budget_cny));return
 if any(c.get('goal')=='injection_task_100' or c.get('task')=='injection_task_100' for c in p['schedule']):
  import course_project.extension.custom_goals
 name='rerun_'+v.phase+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 p.update(name=name,created_utc=stamp(),prior_upper_cny=r.prior_spending(),source_hashes={str(f.relative_to(r.ROOT)):sha(f) for f in r.source_files()},parent_protocol_sha256=sha(r.HERE/v.phase/'protocol.json'))
 p['config']['run_budget_cny']=v.budget_cny;assert r.prior_spending()+v.budget_cny<=100
 write(r.HERE/name/'protocol.json',p);r.run(name)
if __name__=='__main__':main()
