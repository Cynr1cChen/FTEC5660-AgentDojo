"""Verify each cohort using its exact archived source in an isolated subprocess."""
import argparse,json,os,shutil,socket,subprocess,tempfile,yaml
import datetime as dtmod
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone,timedelta
from openai.types.chat import ChatCompletion

def worker(directory):
 from course_project.stage1 import read,write,sha,stamp
 from course_project.deepseek_adapter import DeepSeekLLM
 from course_project.extension.pipelines import build
 from course_project.extension.runner import supplemental,exposure
 from agentdojo.task_suite.load_suites import get_suite
 d=Path(directory);p=read(d/'manifest.json')['protocol'];s=read(d/'summary.json')
 if any(c.get('goal')=='injection_task_100' or c.get('task')=='injection_task_100' for c in p['schedule']):
  import course_project.extension.custom_goals
 assert s['completed']==sum(x['status']=='completed' for x in s['rows'])<=p['expected_episodes']
 assert all(x.get('error_type')=='BudgetExceeded' for x in s['rows'] if x['status']!='completed')
 for f,h in p['source_hashes'].items():assert sha(d/'source_snapshot'/f)==h
 req=[read(f) for f in sorted((d/'calls').glob('*.request.json'))];res=[read(f) for f in sorted((d/'calls').glob('*.response.json'))]
 uses=[json.loads(x) for x in (d/'usage.jsonl').read_text().splitlines()]
 assert len(req)==len(res)==len(uses)==s['api_calls'];known=upper=0
 for q,r,u in zip(req,res,uses):
  dt=datetime.fromisoformat(q['created_utc']).astimezone(timezone(timedelta(hours=8)));m=dt.hour*60+dt.minute
  assert not(dt.weekday()<5 and (540<=m<720 or 840<=m<1080))
  usage=r['response']['usage'];assert usage==u['usage'] and u['status']=='ok'
  hit=usage.get('prompt_cache_hit_tokens',0);known+=(hit*.02+usage['prompt_tokens']-hit+usage['completion_tokens']*4)/1e6
  cost=(usage['prompt_tokens']*2+usage['completion_tokens']*8)/1e6;assert abs(cost-u['estimated_cost_cny'])<1e-9;upper+=cost
 assert abs(upper-s['peak_upper_cny'])<1e-9
 def blocked(*a,**k):raise RuntimeError('Network disabled in replay')
 socket.socket.connect=blocked;socket.socket.connect_ex=blocked;socket.create_connection=blocked
 payloads={};rows=[]
 for row in s['rows']:
  if row['status']!='completed':continue
  c=p['schedule'][row['index']];assert all(row[k]==v for k,v in c.items())
  ids=[i for i,q in enumerate(req) if q['case']==c]
  class Client:
   def __init__(self):self.chat=SimpleNamespace(completions=self);self.n=0
   def create(self,**q):
    i=ids[self.n]
    if q!=req[i]['request']:
     from deepdiff import DeepDiff
     raise AssertionError('Wire request differs episode '+str(row['index'])+' call '+str(self.n)+' '+str(DeepDiff(req[i]['request'],q))[:1600])
    self.n+=1;return ChatCompletion.model_validate(res[i]['response'])
  client=Client();llm=DeepSeekLLM(client,'deepseek-flash',p['config']);llm.context=c;states=[];events=[]
  pipeline=build(llm,c['arm'],events,states,c.get('context'));suite=get_suite('v1.2.2',c['suite'])
  task=(suite.get_injection_task_by_id(c['task']) if c['phase']=='capability' else suite.get_user_task_by_id(c['task']))
  goal=suite.get_injection_task_by_id(c['goal']) if c['phase']=='attacked' else None
  t=read(d/row['trace']);assert sha(d/row['trace'])==row['trace_sha256']
  # File tools stamp local wall time. Replay the exact recorded timestamp for
  # each such call, while re-executing its actual code and all other mutations.
  from agentdojo.functions_runtime import FunctionsRuntime
  from agentdojo.default_suites.v1.tools import cloud_drive_client as drive,email_client as mail
  from agentdojo.types import get_text_content_as_str
  tools=[m for m in t['messages'] if m['role']=='tool'];tool_index=[0]
  original_run=FunctionsRuntime.run_function;original_clock=drive.datetime;original_mail_clock=mail.datetime
  saved_states=read(d/f"episodes/{row['index']:03d}/states.json")
  final_state=saved_states[-1]['after']
  def run_recorded_clock(self,environment,function,args):
   expected=tools[tool_index[0]];assert expected['tool_call']['function']==function and expected['tool_call']['args']==args
   tool_index[0]+=1
   if function in ['append_to_file','create_file'] and not expected.get('error'):
    value=yaml.safe_load(get_text_content_as_str(expected['content']))['last_modified']
    instant=value if isinstance(value,dtmod.datetime) else dtmod.datetime.fromisoformat(value)
    class FixedDateTime(dtmod.datetime):
     @classmethod
     def now(cls,tz=None):return instant if tz is None else instant.astimezone(tz)
    drive.datetime=SimpleNamespace(datetime=FixedDateTime)
   if c['suite']=='workspace' and hasattr(environment,'inbox'):
    next_id=str(environment.inbox._get_next_id())
    final_mail={**final_state['inbox']['emails'],**final_state['inbox']['trash']}
    if next_id in final_mail:
     email_instant=dtmod.datetime.fromisoformat(final_mail[next_id]['timestamp'])
     class FixedMailTime(dtmod.datetime):
      @classmethod
      def now(cls,tz=None):return email_instant if tz is None else email_instant.astimezone(tz)
     mail.datetime=SimpleNamespace(datetime=FixedMailTime)
   try:return original_run(self,environment,function,args)
   finally:drive.datetime=original_clock;mail.datetime=original_mail_clock
  FunctionsRuntime.run_function=run_recorded_clock
  try:u,a=suite.run_task_with_pipeline(pipeline,task,goal,t['injections'])
  finally:FunctionsRuntime.run_function=original_run;drive.datetime=original_clock;mail.datetime=original_mail_clock
  assert tool_index[0]==len(tools)
  assert u==row['utility'] and (not goal or a==row['attack_success'])
  assert client.n==len(ids)==row['api_calls']
  ep=d/f"episodes/{row['index']:03d}"
  assert states==read(ep/'states.json') and events==read(ep/'decisions.json')
  sup=supplemental(c,states,u) if c['phase']!='capability' else {}
  assert sup==row['supplemental']
  if goal:
   assert t['injections']==p['payloads'][str(row['index'])]
   key=(c['suite'],c['task'],c['goal'],c['attack'])
   if key in payloads:assert payloads[key]==t['injections']
   payloads[key]=t['injections']
   assert row['exposed']==exposure(t)
  rows.append(row)
 out=dict(passed=True,cohort_complete=(s['completed']==p['expected_episodes']),technical_rows=[x for x in s['rows'] if x['status']!='completed'],requests_replayed=sum(x['api_calls'] for x in rows),created_utc=stamp(),network_blocked=True,isolated_archived_source=True,episodes=len(rows),requests=len(req),state_files_verified=len(rows),all_offpeak=True,known_offpeak_cny=known,peak_upper_cny=upper,all_attacks_exposed=all(r['exposed'] for r in rows if r['phase']=='attacked'),rows=rows)
 write(d/'audit.json',out);print(json.dumps({k:v for k,v in out.items() if k!='rows'}))

def verify(directory):
 d=Path(directory).resolve();script=Path(__file__).resolve()
 with tempfile.TemporaryDirectory(prefix='agentdojo_extension_replay_') as td:
  checkout=Path(td)/'checkout';shutil.copytree(d/'source_snapshot',checkout)
  env={**os.environ,'PYTHONPATH':str(checkout/'src')+os.pathsep+str(checkout),'PYTHONDONTWRITEBYTECODE':'1'}
  subprocess.run([os.sys.executable,str(script),'--worker',str(d)],cwd=checkout,env=env,check=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('directory');a.add_argument('--worker',action='store_true');v=a.parse_args()
 (worker if v.worker else verify)(v.directory)
