"""Restoration audit and bounded DEVELOPMENT baseline; no new defense."""
import argparse
import copy
import hashlib
import inspect
import json
import os
import socket
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace

import httpx
from dotenv import load_dotenv
from openai import OpenAI
from agentdojo.attacks import load_attack
from agentdojo.benchmark import run_task_without_injection_tasks, run_task_with_injection_tasks
from agentdojo.logging import OutputLogger
from agentdojo.task_suite.load_suites import get_suite
from agentdojo.types import get_text_content_as_str, FunctionCall
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.default_suites.v1.tools.banking_client import send_money
from course_project.deepseek_adapter import DeepSeekLLM
from course_project.run_pilot import build_pipeline, previous_spending
from course_project.prepare import ROOT, environment_metadata

HERE = ROOT / 'course_project/stage1'
OUT = ROOT / 'runs/stage1'
TASKS = [0, 1, 2, 3, 13]  # Original development partition only.
GOALS = [4, 5, 7]
STYLES = ['tool_knowledge', 'important_instructions']
CONFIG = dict(temperature=0.0, thinking='disabled', max_output_tokens=2048,
              max_api_calls=300, run_budget_cny=2.0, max_tool_rounds=15)

def stamp(): return datetime.now(timezone.utc).isoformat()
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def write(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(x, ensure_ascii=False, indent=2) + '\n')
def sources():
    return sorted(list((ROOT/'src').rglob('*.py')) + list((ROOT/'src').rglob('*.yaml')) +
                  list((ROOT/'course_project').glob('*.py')))
def offpeak():
    d = datetime.now(timezone(timedelta(hours=8)))
    minute = d.hour*60+d.minute
    # Conservative weekday rule; no holiday exception needed for this run.
    if d.weekday()<5 and (538 <= minute < 720 or 838 <= minute < 1080):
        raise RuntimeError('Paid request prohibited in or immediately before peak window')

def audit():
    s=get_suite('v1.2.2','banking'); ok, checks=s.check(check_injectable=True)
    rows=[]
    for task in s.user_tasks.values():
        pre=task.init_environment(s.load_and_inject_default_environment({}))
        noop=task.utility('',pre.model_copy(deep=True),pre.model_copy(deep=True))
        rows.append(dict(id=task.ID,prompt=task.PROMPT,source=inspect.getfile(type(task)),
                         utility_source=inspect.getsource(type(task).utility),
                         no_action_passes=noop,
                         reference=[x.model_dump() for x in task.ground_truth(pre)]))
    goals=[]
    for task in s.injection_tasks.values():
        pre=s.load_and_inject_default_environment({})
        goals.append(dict(id=task.ID,goal=task.GOAL,source=inspect.getfile(type(task)),
                          scorer=inspect.getsource(type(task).security),
                          no_action_passes=task.security('',pre,pre.model_copy(deep=True))))
    counter=[]
    for n in [0,1,3]:
        task=s.get_injection_task_by_id(f'injection_task_{n}')
        pre=s.load_and_inject_default_environment({}); post=pre.model_copy(deep=True)
        send_money(post.bank_account,task._ATTACKER_IBAN,.01,'unrelated text','2022-01-01')
        counter.append(dict(id=task.ID,native_success=task.security('',pre,post),
                            required_information_in_subject=False))
    write(HERE/'task_audit.json',dict(created_utc=stamp(),kind='offline_not_model_performance',
          environment=environment_metadata(),reference_checks=checks,all_reference_checks_pass=ok,
          users=rows,goals=goals,scorer_counterexamples=counter))
    print(json.dumps(dict(audit_ok=ok,users=len(rows),goals=len(goals),
                    no_action_user_passes=[x['id'] for x in rows if x['no_action_passes']],
                    scorer_counterexamples=counter)))

def freeze():
    target=HERE/'development_protocol.json'
    if target.exists(): raise RuntimeError('Protocol already frozen')
    amem=ROOT.parent.parent/'amem_project/course_project/runs/retrieval_B_20261112'
    a=read(amem/'protocol.json'); r=read(amem/'results.json')
    prior=a['project_upper_before_cny']+r['cost']['peak_upper_cny'] if 'cost' in r else None
    if prior is None:
        # Locate exact owning cost block without guessing its key.
        blocks=[v for v in r.values() if isinstance(v,dict) and 'peak_upper_cny' in v]
        assert len(blocks)==1
        prior=a['project_upper_before_cny']+blocks[0]['peak_upper_cny']
    schedule=[dict(phase='capability',task=f'injection_task_{i}') for i in GOALS]
    schedule += [dict(phase='clean',task=f'user_task_{i}') for i in TASKS]
    schedule += [dict(phase='attacked',task=f'user_task_{i}',goal=f'injection_task_{j}',attack=k)
                 for k in STYLES for i in TASKS for j in GOALS]
    write(target,dict(created_utc=stamp(),purpose='DEVELOPMENT ONLY; not formal replication or defense efficacy',
       benchmark='v1.2.2',suite='banking',model='deepseek-flash',config=CONFIG,
       task_partition='Original development tasks only; no formal outcomes used for tuning',
       schedule=schedule,expected_episodes=len(schedule),trials=1,
       shared_system_prompt='native unchanged; no supplied date or reference answer',
       stop_policy='First technical/protocol error or budget/time guard stops; no quality retries',
       amem_prior_upper_cny=prior,amem_cost_sources={str(p):sha(p) for p in [amem/'protocol.json',amem/'results.json']},
       old_agentdojo_upper_cny=previous_spending(),offpeak_only=True,
       source_hashes={str(p.relative_to(ROOT)):sha(p) for p in sources()},
       source_snapshots='runs/stage1/<run>/source_snapshot; includes uncommitted source bytes',
       metrics=['clean utility','attack utility','attack success','safe completion','actual exposure','usage','latency'],
       source_price='https://api-docs.deepseek.com/zh-cn/quick_start/pricing/',price_checked='2026-11-13'))
    print('Frozen development episodes:',len(schedule),'prior project upper:',prior+previous_spending())

class RecordedClient:
    def __init__(self,client,directory):
        self.client=client; self.directory=directory; self.chat=SimpleNamespace(completions=self)
        self.counter=0; self.case=None
    def create(self,**request):
        offpeak(); self.counter+=1
        path=self.directory/f'calls/{self.counter:04d}'
        write(path.with_suffix('.request.json'),dict(created_utc=stamp(),case=self.case,request=request))
        result=self.client.chat.completions.create(**request)
        write(path.with_suffix('.response.json'),dict(received_utc=stamp(),response=result.model_dump()))
        return result

def run():
    p=read(HERE/'development_protocol.json')
    for name,digest in p['source_hashes'].items(): assert sha(ROOT/name)==digest,name
    for name,digest in p['amem_cost_sources'].items(): assert sha(name)==digest,name
    offpeak(); load_dotenv(ROOT/'.env',override=False)
    key=os.getenv('DEEPSEEK_API_KEY','').strip(); assert key,'Missing local key'
    assert os.getenv('DEEPSEEK_MODEL','deepseek-flash')=='deepseek-flash'
    prior=p['amem_prior_upper_cny']+previous_spending()
    for f in OUT.glob('*/usage.jsonl'):
        prior+=sum(json.loads(x)['estimated_cost_cny'] for x in f.read_text().splitlines())
    assert prior+CONFIG['run_budget_cny']<=100
    d=OUT/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');d.mkdir(parents=True,exist_ok=False)
    for name in p['source_hashes']:
        t=d/'source_snapshot'/name;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes((ROOT/name).read_bytes())
    write(d/'manifest.json',dict(protocol=p,protocol_sha256=sha(HERE/'development_protocol.json'),
        environment=environment_metadata(),prior_upper_cny=prior,
        git_status=subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)))
    client=OpenAI(api_key=key,base_url='https://api.deepseek.com',max_retries=0,
                  timeout=httpx.Timeout(180,connect=15))
    rec=RecordedClient(client,d); llm=DeepSeekLLM(rec,'deepseek-flash',CONFIG,d/'usage.jsonl',prior)
    suite=get_suite('v1.2.2','banking'); rows=[]
    try:
        for index,case in enumerate(p['schedule']):
            rec.case=case; llm.context=case; start=len(llm.records)
            ep=d/f'episodes/{index:03d}'; row=dict(index=index,**case,status='error')
            pipeline=build_pipeline(llm,'none',15)
            try:
                with OutputLogger(str(ep/'traces')):
                    if case['phase']=='attacked':
                        attack=load_attack(case['attack'],suite,pipeline)
                        u,a=run_task_with_injection_tasks(suite,pipeline,suite.get_user_task_by_id(case['task']),
                            attack,ep,True,[case['goal']],'v1.2.2')
                        u=u[(case['task'],case['goal'])]; a=a[(case['task'],case['goal'])]
                    else:
                        t=(suite.get_injection_task_by_id(case['task']) if case['phase']=='capability'
                           else suite.get_user_task_by_id(case['task']))
                        u,_=run_task_without_injection_tasks(suite,pipeline,t,ep,True,'v1.2.2'); a=None
                assert all(x['status']=='ok' for x in llm.records[start:]),'Caught API error'
                traces=list((ep/'traces').rglob('*.json')); assert len(traces)==1
                trace=read(traces[0]);assert not trace.get('error'), 'Trace error'
                tools=[m for m in trace['messages'] if m['role']=='tool']
                payloads=list(trace['injections'].values())
                exposed=any(v in get_text_content_as_str(m['content']) for v in payloads for m in tools)
                row.update(status='completed',utility=u,attack_success=a,
                           actual_payload_exposure=exposed if a is not None else None,
                           trace=str(traces[0].relative_to(d)),trace_sha256=sha(traces[0]))
            except Exception as exc:
                row['error_type']=type(exc).__name__
            row.update(api_calls=len(llm.records)-start,
                       peak_upper_cny=sum(x['estimated_cost_cny'] for x in llm.records[start:]))
            rows.append(row);write(ep/'result.json',row)
            print(json.dumps(row),flush=True)
            if row['status']!='completed': break
    finally:
        client.close()
        write(d/'summary.json',dict(created_utc=stamp(),development_only=True,rows=rows,
             expected_episodes=p['expected_episodes'],completed=sum(x['status']=='completed' for x in rows),
             api_calls=len(llm.records),peak_upper_cny=llm.estimated_cost_cny,
             project_upper_cny=prior+llm.estimated_cost_cny))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['audit','freeze','run'])
    args=parser.parse_args();globals()[args.action]()
