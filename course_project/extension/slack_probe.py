"""Small additional attack-coverage probe after zero Workspace successes."""
import sys,inspect
from course_project.extension import runner as r
from course_project.stage1 import write,stamp
from agentdojo.task_suite.load_suites import get_suite
from agentdojo.agent_pipeline.ground_truth_pipeline import GroundTruthPipeline

def freeze():
 s=get_suite('v1.2.2','slack');checks=[]
 for n in [1,3,6]:
  t=s.get_user_task_by_id(f'user_task_{n}');ok,_=s.run_task_with_pipeline(GroundTruthPipeline(t),t,None,{})
  checks.append(dict(task=t.ID,reference=ok,utility_source=inspect.getsource(type(t).utility)));assert ok
 for n in [1,4]:
  t=s.get_injection_task_by_id(f'injection_task_{n}');ok,_=s.run_task_with_pipeline(GroundTruthPipeline(t),t,None,{})
  checks.append(dict(goal=t.ID,reference=ok,scorer=inspect.getsource(type(t).security)));assert ok
 write(r.HERE/'slack_audit.json',dict(created_utc=stamp(),checks=checks))
 cases=[dict(suite='slack',phase='capability',task=f'injection_task_{g}',arm='baseline',trial=0) for g in [1,4]]
 cases += [dict(suite='slack',phase='clean',task=f'user_task_{t}',arm='baseline',trial=0) for t in [1,3,6]]
 cases += [dict(suite='slack',phase='attacked',task=f'user_task_{t}',goal=f'injection_task_{g}',attack=a,arm='baseline',trial=0) for a in ['tool_knowledge','maintenance_dependency','role_delimiters'] for t in [1,3,6] for g in [1,4]]
 r.freeze('slack_development',cases,2,dict(development_only=True,reason='Bounded cross-environment attack search after zero Workspace successes. Not a formal cross-scene efficacy claim. All original facts retained except original author template replacement.'))
if __name__=='__main__':
 if sys.argv[1]=='freeze':freeze()
 elif sys.argv[1]=='run':r.run('slack_development')
