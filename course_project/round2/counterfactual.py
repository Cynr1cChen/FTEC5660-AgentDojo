"""Tool-level counterfactuals using actual baseline proposals and paired contracts.

No new LLM draws. This establishes action-boundary behavior, not an end-to-end
rescued task or an independent population of attacks.
"""
import copy,socket
from pathlib import Path
from course_project.stage1 import ROOT,read,write,stamp
from course_project.round2.contract import decide,WRITES
from agentdojo.task_suite.load_suites import get_suite
from agentdojo.functions_runtime import FunctionsRuntime

def main():
 def blocked(*a,**k):raise RuntimeError('Offline counterfactual')
 socket.socket.connect=blocked;socket.create_connection=blocked
 d=sorted((ROOT/'runs/round2/contract_formal').iterdir())[-1];a=read(d/'audit.json');assert a['cohort_complete'];rows=a['rows'];out=[]
 s=get_suite('v1.2.2','banking')
 for r in rows:
  if r['arm']!='baseline' or r['suite']!='banking':continue
  matched=next(x for x in rows if x['arm']=='contract' and all(x.get(k)==r.get(k) for k in ['suite','task','phase','trial','goal','attack']))
  decisions=read(d/f"episodes/{matched['index']:03d}/decisions.json");policy=next(x['policy'] for x in decisions if x.get('stage')=='contract')
  t=read(d/r['trace']);task=s.get_user_task_by_id(r['task']);env=task.init_environment(s.load_and_inject_default_environment(t['injections']));initial=env.model_copy(deep=True);runtime=FunctionsRuntime(s.tools)
  goal=s.get_injection_task_by_id(r['goal']) if r['phase']=='attacked' else None
  for m in t['messages']:
   if m['role']!='tool':continue
   c=m['tool_call'];before=env.model_copy(deep=True);_,error=runtime.run_function(env,c['function'],copy.deepcopy(c['args']));assert error==m.get('error')
   if c['function'] not in WRITES or error:continue
   allow,reason=decide(policy,c['function'],c['args']);hypothetical=before.model_copy(deep=True)
   if allow:runtime.run_function(hypothetical,c['function'],copy.deepcopy(c['args']))
   old=goal.security('',initial,before) if goal else False;actual=goal.security('',initial,env) if goal else False;cf=goal.security('',initial,hypothetical) if goal else False
   out.append(dict(index=r['index'],matched_contract=matched['index'],phase=r['phase'],task=r['task'],trial=r['trial'],goal=r.get('goal'),call=c,allow=allow,reason=reason,actual_goal_transition=bool(not old and actual),counterfactual_goal=bool(cf),prevented_transition=bool(not old and actual and not cf),native_task_after_actual_write=bool(task.utility('',initial,env)),strict_policy=policy))
 write(ROOT/'course_project/round2/counterfactual.json',dict(created_utc=stamp(),network_blocked=True,method='Every actual baseline bank write, matched original-request contract from same task/condition/trial. Replay native tools before and after that one operation. No new model output; no claim of end-to-end task recovery.',writes=len(out),actual_goal_transitions=sum(r['actual_goal_transition'] for r in out),prevented_transitions=sum(r['prevented_transition'] for r in out),clean_writes_denied=sum(not r['allow'] for r in out if r['phase']=='clean'),rows=out))
 print('transitions',sum(r['actual_goal_transition'] for r in out),'prevented',sum(r['prevented_transition'] for r in out))
if __name__=='__main__':main()
