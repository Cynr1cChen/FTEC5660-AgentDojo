"""Negative controls for newly used Travel side-effect evaluation."""
from copy import deepcopy
from agentdojo.task_suite.load_suites import get_suite
from agentdojo.agent_pipeline.ground_truth_pipeline import GroundTruthPipeline
from course_project.extension.pipelines import StateObserver
from course_project.extension_review.travel import rubric

def test_travel_reference_and_unrequested_recipient():
 s=get_suite('v1.2.2','travel');t=s.get_user_task_by_id('user_task_4');states=[]
 u,_=s.run_task_with_pipeline(StateObserver(GroundTruthPipeline(t),states),t,None,{})
 c=dict(task=t.ID);assert rubric(c,states,u)['strict_utility']
 bad=deepcopy(states);initial=bad[0]['before']['calendar']['events'];new=next(v for k,v in bad[-1]['after']['calendar']['events'].items() if k not in initial)
 new['participants'].append('outsider@example.com')
 assert not rubric(c,bad,u)['strict_utility']

def test_travel_unrequested_reservation_is_not_clean_success():
 s=get_suite('v1.2.2','travel');t=s.get_user_task_by_id('user_task_4');states=[]
 u,_=s.run_task_with_pipeline(StateObserver(GroundTruthPipeline(t),states),t,None,{})
 bad=deepcopy(states);bad[-1]['after']['reservation']['title']='Unrequested hotel'
 assert not rubric(dict(task=t.ID),bad,u)['strict_utility']
