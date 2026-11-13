"""Prospective broader task families, not selected by model outcomes."""
import inspect,sys
from course_project.round2 import runner as r
from course_project.stage1 import write,stamp
from agentdojo.task_suite.load_suites import get_suite
from agentdojo.agent_pipeline.ground_truth_pipeline import GroundTruthPipeline
from course_project.extension.pipelines import StateObserver
SLACK=[2,4,15,20]
TRAVEL=[12,15,18]
def audit():
 out=[]
 for suite_name,ids in [('slack',SLACK),('travel',TRAVEL)]:
  s=get_suite('v1.2.2',suite_name)
  for n in ids:
   t=s.get_user_task_by_id(f'user_task_{n}');states=[];u,_=s.run_task_with_pipeline(StateObserver(GroundTruthPipeline(t),states),t,None,{})
   e=t.init_environment(s.load_and_inject_default_environment({}));noop=t.utility('',e,e.model_copy(deep=True));sup=r.supplemental(dict(suite=suite_name,task=t.ID),states,u)
   assert u and not noop and sup['strict_utility'],(suite_name,t.ID,sup)
   out.append(dict(suite=suite_name,task=t.ID,prompt=t.PROMPT,reference=u,noop=noop,supplemental=sup,scorer=inspect.getsource(type(t).utility)))
 write(r.HERE/'task_audit.json',dict(created_utc=stamp(),cases=out,selection='Prospective diversity: invitation, publication, multi-website summary and composite workflow in Slack; dietary budget, two car categories and restaurant/car constraints in Travel. No formal scores inspected. Earlier simple Travel calendar subset remains separate.',limitations='Native textual graders may accept incomplete answers; preserve native metrics and inspect final answers separately. No inference of content completeness from simple membership/count checks.'))
def freeze(suite):
 ids=SLACK if suite=='slack' else TRAVEL;goals=[1,4] if suite=='slack' else [0,2];cases=[];arms=['baseline','neutral','recovery']
 for trial in range(3):
  for pos,n in enumerate(ids):
   j=(pos+trial)%3;order=arms[j:]+arms[:j]
   for goal in [None,*goals]:
    for arm in order:
     c=dict(suite=suite,phase='clean' if goal is None else 'attacked',task=f'user_task_{n}',arm=arm,trial=trial)
     if suite=='travel':c['context']='The current date in this simulated travel environment is 2024-01-01.'
     if goal is not None:c.update(goal=f'injection_task_{goal}',attack='tool_knowledge')
     cases.append(c)
 r.freeze(suite+'_broader',cases,8,dict(formal=True,trials=3,selection_before_model_outputs=True,task_families=ids,question='Does bounded review help on broader non-calendar task families? All tasks retained regardless of scores. No replacement for earlier ceiling results.',budget_authorization='User raised cumulative conservative budget from100 to150CNY on2026-11-13; previous records and caps unchanged.'))
if __name__=='__main__':
 if sys.argv[1]=='audit':audit()
 else:freeze(sys.argv[1])
