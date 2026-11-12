import copy
from course_project.deepseek_adapter import DeepSeekLLM
from course_project.interventions import build, RECOVERY
from course_project.tests.test_protocol_and_evaluation import FakeClient, completion
from course_project.stage1 import CONFIG
from agentdojo.task_suite.load_suites import get_suite

def test_guard_blocks_wrong_value_then_allows_correct_value():
    client=FakeClient([
        completion(tool=('update_password',{'password':'654321'},'bad')),
        completion('{"decision":"deny","reason":"Wrong password value"}'),
        completion(tool=('update_password',{'password':'1j1l-2k3j'},'good')),
        completion('{"decision":"allow","reason":"Matches user request"}'),
        completion('Done.')])
    llm=DeepSeekLLM(client,'deepseek-flash',{**CONFIG,'run_budget_cny':3})
    events=[];pipeline=build(llm,'guard',events)
    suite=get_suite('v1.2.2','banking');env=suite.load_and_inject_default_environment({})
    _,_,env,messages,_=pipeline.query('Set password to 1j1l-2k3j.',__import__('agentdojo.functions_runtime',fromlist=['FunctionsRuntime']).FunctionsRuntime(suite.tools),env)
    assert env.user_account.password=='1j1l-2k3j'
    assert [x['decision'] for x in events]==['deny','allow']
    assert messages[3]['role']=='tool' and messages[3]['tool_call_id']=='bad'
    assert messages[3]['error'].startswith('Action not executed')
    assert '654321' in client.requests[1]['messages'][-1]['content']
    assert 'tools' not in client.requests[1]

def test_recovery_runs_once_without_repeating_completed_write():
    client=FakeClient([
        completion(tool=('update_password',{'password':'1j1l-2k3j'},'once')),
        completion('Done.'),completion('Already complete.')])
    llm=DeepSeekLLM(client,'deepseek-flash',{**CONFIG,'run_budget_cny':3})
    suite=get_suite('v1.2.2','banking');pipeline=build(llm,'recovery',[])
    utility,_=suite.run_task_with_pipeline(pipeline,suite.get_user_task_by_id('user_task_14'),None,{})
    assert utility
    assert len(client.requests)==3
    assert client.requests[-1]['messages'][-1]=={'role':'system','content':RECOVERY}
    assert sum('tool_calls' in x for x in client.requests[-1]['messages'])==1

def test_guard_format_error_does_not_execute_write():
    import pytest
    client=FakeClient([completion(tool=('update_password',{'password':'wrong'},'bad')),completion('invalid json')])
    llm=DeepSeekLLM(client,'deepseek-flash',{**CONFIG,'run_budget_cny':3})
    suite=get_suite('v1.2.2','banking');env=suite.load_and_inject_default_environment({});original=env.user_account.password
    from agentdojo.functions_runtime import FunctionsRuntime
    with pytest.raises(ValueError):build(llm,'guard',[]).query('Update address.',FunctionsRuntime(suite.tools),env)
    assert env.user_account.password==original
