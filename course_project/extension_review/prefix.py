"""Bank-only native tool prefix replay, no LLM or socket access."""
import socket,copy
from collections import Counter
from course_project.stage1 import ROOT,read,write,stamp
from course_project.interventions import RECOVERY
from course_project.extension.pipelines import NEUTRAL
from agentdojo.task_suite.load_suites import get_suite
from agentdojo.functions_runtime import FunctionsRuntime
from agentdojo.types import get_text_content_as_str
from course_project.results_formal import strict

def blocked(*a,**k):raise RuntimeError('Offline prefix replay')
socket.socket.connect=blocked;socket.create_connection=blocked
p=sorted((ROOT/'runs/extension/banking_control').iterdir())[-1];rows=read(p/'audit.json')['rows'];out=[];s=get_suite('v1.2.2','banking')
for r in rows:
 if r['arm'] not in ['neutral','recovery']:continue
 trace=read(p/r['trace']);ms=trace['messages'];indices=[i for i,m in enumerate(ms) if m['role']=='system' and get_text_content_as_str(m['content']) in [RECOVERY,NEUTRAL]]
 if not indices:continue
 stop=indices[0];task=s.get_user_task_by_id(r['task']);env=task.init_environment(s.load_and_inject_default_environment(trace['injections']));before=env.model_copy(deep=True);runtime=FunctionsRuntime(s.tools)
 for m in ms[:stop]:
  if m['role']=='tool':
   _,err=runtime.run_function(env,m['tool_call']['function'],copy.deepcopy(m['tool_call']['args']));assert err==m.get('error')
 answer=next(get_text_content_as_str(m['content']) for m in reversed(ms[:stop]) if m['role']=='assistant')
 u=task.utility(answer,before,env);ok,flags=strict({**r,'utility':u},before.model_dump(mode='json'),env.model_dump(mode='json'))
 out.append(dict(index=r['index'],arm=r['arm'],task=r['task'],phase=r['phase'],trial=r['trial'],goal=r.get('goal'),reviews=len(indices),before=u,after=r['utility'],strict_before=ok,strict_after=r['supplemental']['strict_utility'],initial_answer=answer,new_calls=[c for m in ms[stop:] if m['role']=='assistant' for c in (m.get('tool_calls') or [])]))
summary={}
for arm in ['neutral','recovery']:
 for phase in ['clean','attacked']:
  xs=[r for r in out if r['arm']==arm and r['phase']==phase]
  summary[arm+'/'+phase]=dict(n=len(xs),before=sum(r['before'] for r in xs),after=sum(r['after'] for r in xs),rescued=sum(not r['before'] and r['after'] for r in xs),lost=sum(r['before'] and not r['after'] for r in xs))
write(ROOT/'course_project/extension_review/banking_prefix.json',dict(network_blocked=True,method='Native bank tools replayed up to first added review in each saved trajectory. No new model draws. Independent arms must not be treated as identical-prefix counterfactuals.',summary=summary,rows=out));print(summary)
