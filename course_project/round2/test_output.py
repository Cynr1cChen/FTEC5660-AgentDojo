from course_project.tests.test_protocol_and_evaluation import FakeClient,completion
from course_project.deepseek_adapter import DeepSeekLLM
from course_project.stage1 import CONFIG
from course_project.round2.pipelines import build
from agentdojo.task_suite.load_suites import get_suite

def test_information_answer_not_replaced_by_meta_confirmation():
 c=FakeClient([completion('The gift cost200.'),completion('Already answered.')]);llm=DeepSeekLLM(c,'deepseek-flash',{**CONFIG,'run_budget_cny':3});s=get_suite('v1.2.2','banking');states=[];events=[]
 p=build(llm,'preserve',events,states);q,r,e,m,x=p.query('How much?',__import__('agentdojo.functions_runtime',fromlist=['FunctionsRuntime']).FunctionsRuntime(s.tools),s.load_and_inject_default_environment({}))
 assert m[-1]['content'][0]['content']=='The gift cost200.' and events[-1]['retain_native_answer']
 assert len(c.requests)==2

def test_added_real_tool_operation_keeps_review_answer():
 c=FakeClient([completion('Not yet complete.'),completion(tool=('update_password',{'password':'1j1l-2k3j'},'good')),completion('Password updated.')]);llm=DeepSeekLLM(c,'deepseek-flash',{**CONFIG,'run_budget_cny':3});s=get_suite('v1.2.2','banking');states=[];events=[]
 u,_=s.run_task_with_pipeline(build(llm,'preserve',events,states),s.get_user_task_by_id('user_task_14'),None,{})
 assert u and not events[-1]['retain_native_answer']
