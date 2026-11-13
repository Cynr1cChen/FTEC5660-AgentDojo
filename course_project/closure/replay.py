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
 from course_project.closure.pipelines import build
 from course_project.closure.runner import supplemental,exposure
 from agentdojo.task_suite.load_suites import get_suite
 d=Path(directory);p=read(d/'manifest.json')['protocol'];s=read(d/'summary.json')
 if any(c.get('goal')=='injection_task_100' or c.get('task')=='injection_task_100' for c in p['schedule']):
  import course_project.extension.custom_goals
 assert s['completed']==sum(x['status']=='completed' for x in s['rows'])<=p['expected_episodes']
 assert all(x.get('status')=='error' and x.get('error_type') in ['BudgetExceeded','ValueError','RuntimeError','ProcessInterrupted'] for x in s['rows'] if x['status']!='completed')
 for f,h in p['source_hashes'].items():assert sha(d/'source_snapshot'/f)==h
 reqfiles=sorted((d/'calls').glob('*.request.json'));resfiles=sorted((d/'calls').glob('*.response.json'))
 req=[read(f) for f in reqfiles];res=[read(f) for f in resfiles]
 pending=[f.name for f in reqfiles if not f.with_name(f.name.replace('.request.','.response.')).exists()]
 interruption=read(d/'interruption.json') if (d/'interruption.json').exists() else {}
 assert pending==interruption.get('pending_requests',[])
 matched=[read(f) for f in reqfiles if f.name not in pending]
 uses=[json.loads(x) for x in (d/'usage.jsonl').read_text().splitlines()]
 # SIGINT can leave the adapter's finally-recorded reservation without a
 # response. Keep it in the ledger, but never invent a response or score.
 in_usage=0
 if pending and len(uses)==len(req):
  actual_uses=[]
  for f,u in zip(reqfiles,uses):
   if f.name in pending:
    assert u['status']=='error' and 'usage' not in u
    in_usage+=u['estimated_cost_cny']
   else:actual_uses.append(u)
  assert abs(in_usage-interruption['reservation_already_in_usage_cny'])<1e-12
 else:actual_uses=uses
 assert len(req)==s['api_calls'] and len(matched)==len(res)==len(actual_uses);known=upper=0;peak_starts=0
 for q in req:
  dt=datetime.fromisoformat(q['created_utc']).astimezone(timezone(timedelta(hours=8)));m=dt.hour*60+dt.minute
  is_peak=dt.weekday()<5 and (540<=m<720 or 840<=m<1080);peak_starts+=int(is_peak)
  if is_peak:
   assert not p['offpeak_only'] and p['schedule_authorization']['explicit_user_peak_permission']
   assert p['schedule_authorization']['local_cap_cny']==10 and p['schedule_authorization']['cumulative_cap_cny']==150
 for q,r,u in zip(matched,res,actual_uses):
  usage=r['response']['usage'];assert usage==u['usage'] and u['status']=='ok'
  dt=datetime.fromisoformat(q['created_utc']).astimezone(timezone(timedelta(hours=8)));m=dt.hour*60+dt.minute;factor=2 if dt.weekday()<5 and (540<=m<720 or 840<=m<1080) else 1
  hit=usage.get('prompt_cache_hit_tokens',0);known+=factor*(hit*.02+usage['prompt_tokens']-hit+usage['completion_tokens']*4)/1e6
  cost=(usage['prompt_tokens']*2+usage['completion_tokens']*8)/1e6;assert abs(cost-u['estimated_cost_cny'])<1e-9;upper+=cost
 unknown=interruption.get('unknown_reservation_cny',0)+in_usage
 expected_unknown=0
 for f in reqfiles:
  if f.name not in pending:continue
  assert sha(f)==interruption['pending_request_hashes'][f.name]
  q=read(f)['request'];n=len(json.dumps(dict(messages=q['messages'],tools=q.get('tools',[])),ensure_ascii=False).encode('utf-8'))+64*len(q['messages'])+512
  expected_unknown+=(n*2+p['config']['max_output_tokens']*8)/1e6
 assert abs(expected_unknown-unknown)<1e-12
 assert abs(upper+unknown-s['peak_upper_cny'])<1e-9
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
  tools=[m for m in t['messages'] if m['role']=='tool' and not str(m.get('error') or '').startswith('Action not executed:')];tool_index=[0]
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
   if c['suite'] in ['workspace','travel'] and hasattr(environment,'inbox'):
    next_id=str(environment.inbox._get_next_id())
    final_mail={**final_state['inbox']['emails'],**final_state['inbox']['trash']}
    if next_id in final_mail:
     email_instant=dtmod.datetime.fromisoformat(final_mail[next_id]['timestamp'])
     class FixedMailTime(dtmod.datetime):
      @classmethod
      def now(cls,tz=None):return email_instant if tz is None else email_instant.astimezone(tz)
     mail.datetime=SimpleNamespace(datetime=FixedMailTime)
   try:
    value,error=original_run(self,environment,function,args)
    # Calendar.create_event uses list(set(...)): preserve recorded order only
    # after proving identical membership, before the next exact wire check.
    if function=='create_calendar_event' and error is None:
     recorded=yaml.safe_load(get_text_content_as_str(expected['content']))
     assert sorted(value.participants)==sorted(recorded['participants'])
     value.participants=recorded['participants']
    return value,error
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
 out=dict(passed=True,cohort_complete=(s['completed']==p['expected_episodes']),technical_rows=[x for x in s['rows'] if x['status']!='completed'],requests_replayed=sum(x['api_calls'] for x in rows),created_utc=stamp(),network_blocked=True,isolated_archived_source=True,episodes=len(rows),requests=len(req),state_files_verified=len(rows),all_offpeak=not peak_starts,peak_request_starts=peak_starts,known_recorded_period_cny=known,known_offpeak_cny=known if not peak_starts else None,peak_upper_cny=upper+unknown,unknown_reservation_cny=unknown,reservation_already_in_usage_cny=in_usage,missing_response_requests=pending,all_attacks_exposed=all(r['exposed'] for r in rows if r['phase']=='attacked'),rows=rows)
 write(d/'audit.json',out);print(json.dumps({k:v for k,v in out.items() if k!='rows'}))

def verify(directory):
 d=Path(directory).resolve();script=Path(__file__).resolve()
 with tempfile.TemporaryDirectory(prefix='agentdojo_extension_replay_') as td:
  checkout=Path(td)/'checkout';shutil.copytree(d/'source_snapshot',checkout)
  dependency=d/'dependency_manifest.json'
  if dependency.exists():
   meta=json.loads(dependency.read_text())
   import hashlib
   for name,h in meta['paths'].items():
    src=d/'dependency_snapshot'/name;target=checkout/name
    assert not target.exists() and hashlib.sha256(src.read_bytes()).hexdigest()==h
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,target)
  env={**os.environ,'PYTHONPATH':str(checkout/'src')+os.pathsep+str(checkout),'PYTHONDONTWRITEBYTECODE':'1'}
  subprocess.run([os.sys.executable,str(script),'--worker',str(d)],cwd=checkout,env=env,check=True)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('directory');a.add_argument('--worker',action='store_true');v=a.parse_args()
 (worker if v.worker else verify)(v.directory)
