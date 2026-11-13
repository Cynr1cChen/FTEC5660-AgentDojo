"""Offline task/scorer inspection; author reference controls are not model scores."""
import inspect
from agentdojo.task_suite.load_suites import get_suite
from agentdojo.attacks.base_attacks import FixedJailbreakAttack
from types import SimpleNamespace
from course_project.stage1 import ROOT,write,stamp

def main():
 s=get_suite('v1.2.2','workspace');out=ROOT/'course_project/extension/workspace_audit.json'
 users=[]
 for t in s.user_tasks.values():
  e=t.init_environment(s.load_and_inject_default_environment({}))
  users.append(dict(id=t.ID,prompt=t.PROMPT,no_action_pass=t.utility('',e.model_copy(deep=True),e.model_copy(deep=True)),utility_source=inspect.getsource(type(t).utility),reference=[x.model_dump() for x in t.ground_truth(e)]))
 goals=[]
 for t in s.injection_tasks.values():
  e=s.load_and_inject_default_environment({})
  goals.append(dict(id=t.ID,goal=t.GOAL,no_action_pass=t.security('',e,e.model_copy(deep=True)),scorer=inspect.getsource(type(t).security)))
 ok,checks=s.check(check_injectable=True)
 write(out,dict(created_utc=stamp(),suite='workspace',benchmark='v1.2.2',users=users,goals=goals,reference_checks=checks,reference_passed=ok,
 development_tasks=[6,29,33],reserved_formal_tasks=[7,8,18,32],goals_for_extension=[0,1],selection='Clear original requests, state-changing tasks, no native no-op passes; goals send an unrelated email or delete an unrelated file. No outcome-based formal task selection.'))
 print(dict(reference_passed=ok,users=len(users),goals=len(goals),output=str(out)))
if __name__=='__main__':main()
