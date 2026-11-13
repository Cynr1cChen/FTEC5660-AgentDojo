import pytest
from course_project.deepseek_adapter import DeepSeekLLM,BudgetExceeded
from course_project.stage1 import CONFIG
from course_project.tests.test_protocol_and_evaluation import FakeClient,completion
from agentdojo.functions_runtime import FunctionsRuntime

def test_explicit_authorized150_limit_and_default100_limit():
 messages=[{'role':'user','content':[{'type':'text','content':'Hello'}]}]
 allowed=DeepSeekLLM(FakeClient([completion('ok')]),'deepseek-flash',{**CONFIG,'project_budget_cny':150},previous_cost_cny=120)
 allowed.query('Hello',FunctionsRuntime([]),messages=messages)
 blocked=DeepSeekLLM(FakeClient([]),'deepseek-flash',CONFIG,previous_cost_cny=120)
 with pytest.raises(BudgetExceeded):blocked.query('Hello',FunctionsRuntime([]),messages=messages)
 exhausted=DeepSeekLLM(FakeClient([]),'deepseek-flash',{**CONFIG,'project_budget_cny':150},previous_cost_cny=150)
 with pytest.raises(BudgetExceeded):exhausted.query('Hello',FunctionsRuntime([]),messages=messages)
