"""Engineering controls use fake responses and native tools, not model evidence."""
import pytest
from agentdojo.task_suite.load_suites import get_suite
from course_project.tests.test_protocol_and_evaluation import FakeClient,completion
from course_project.deepseek_adapter import DeepSeekLLM
from course_project.stage1 import CONFIG
from course_project.closure.pipelines import build,SHARED_POLICY

@pytest.mark.parametrize('arm',['anchored','aligned'])
def test_hard_guard_survives_checker_allow_and_amount_retry_preserves_fields(arm):
    client=FakeClient([
        completion(tool=('update_scheduled_transaction',{'id':7,'amount':1200,'recipient':'US133000000121212121212','recurring':True},'bad')),
        completion('{"decision":"allow","reason":"Synthetic reviewer allows"}'),
        completion(tool=('update_scheduled_transaction',{'id':7,'amount':1200},'retry')),
        completion('{"decision":"allow","reason":"Amount supported"}'),
        completion('Amount updated; recipient unchanged.')])
    llm=DeepSeekLLM(client,'deepseek-flash',{**CONFIG,'run_budget_cny':3});events=[];states=[]
    s=get_suite('v1.2.2','banking')
    u,a=s.run_task_with_pipeline(build(llm,arm,events,states),s.get_user_task_by_id('user_task_12'),s.get_injection_task_by_id('injection_task_4'),{})
    assert u and not a
    b=next(t for t in states[0]['before']['bank_account']['scheduled_transactions'] if t['id']==7)
    z=next(t for t in states[-1]['after']['bank_account']['scheduled_transactions'] if t['id']==7)
    assert {k:v for k,v in z.items() if k!='amount'}=={k:v for k,v in b.items() if k!='amount'}
    assert [e['decision'] for e in events if e.get('stage')=='anchored_rule']==['deny','allow']
    actor=client.requests[0]['messages'][0]['content'];checker=client.requests[1]['messages'][0]['content']
    assert (SHARED_POLICY in actor)==(arm=='aligned')
    assert (SHARED_POLICY in checker)==(arm=='aligned')
    assert llm.context.get('component') is None

def test_one_normal_answer_has_no_added_review_or_hidden_second_call():
    client=FakeClient([completion('Need confirmation.')]);llm=DeepSeekLLM(client,'deepseek-flash',{**CONFIG,'run_budget_cny':3})
    s=get_suite('v1.2.2','banking');events=[];states=[]
    s.run_task_with_pipeline(build(llm,'aligned',events,states),s.get_user_task_by_id('user_task_12'),None,{})
    assert len(client.requests)==1
    assert len([e for e in events if e.get('stage')=='shared_policy'])==1

@pytest.mark.parametrize('bad_field',['date','recipient'])
def test_strict_metric_catches_unrequested_fields_even_if_native_task_passes(bad_field):
    from course_project.closure.rubrics import evaluate
    from agentdojo.functions_runtime import FunctionsRuntime
    s=get_suite('v1.2.2','banking');env=s.load_and_inject_default_environment({})
    before=env.model_dump(mode='json');runtime=FunctionsRuntime(s.tools)
    _,error=runtime.run_function(env,'update_scheduled_transaction',{'id':7,'amount':1200})
    assert error is None
    states=[dict(before=before,after=env.model_dump(mode='json'))]
    case=dict(suite='banking',task='user_task_12')
    assert evaluate(case,states,True)['strict_utility']
    value='2099-01-01' if bad_field=='date' else 'US133000000121212121212'
    _,error=runtime.run_function(env,'update_scheduled_transaction',{'id':7,bad_field:value})
    assert error is None
    assert s.get_user_task_by_id('user_task_12').utility('',s.load_and_inject_default_environment({}),env)
    z=evaluate(case,[dict(before=before,after=env.model_dump(mode='json'))],True)
    assert not z['strict_utility']
    if bad_field=='date':assert z['historical_strict_utility'] and not z['timing_preserved']
    else:
        assert z['unauthorized']
        assert not s.get_injection_task_by_id('injection_task_4').security('',s.load_and_inject_default_environment({}),env)
