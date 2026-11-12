"""No-network replay of every saved request, intervention and native score."""
import sys
import json
import socket
import runpy
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from openai.types.chat import ChatCompletion
from agentdojo.task_suite.load_suites import get_suite
from course_project.deepseek_adapter import DeepSeekLLM
from course_project.interventions import build
from course_project.stage1 import ROOT,read,write,sha,stamp

def run(phase):
    d=sorted((ROOT/f'runs/{phase}').iterdir())[-1]
    summary=read(d/'summary.json');p=read(d/'manifest.json')['protocol']
    assert summary['completed']==p['expected_episodes']
    for name,digest in p['source_hashes'].items():
        assert sha(d/'source_snapshot'/name)==digest
        assert sha(ROOT/name)==digest,'Live source changed: '+name
    reqs=[read(f) for f in sorted((d/'calls').glob('*.request.json'))]
    responses=[read(f) for f in sorted((d/'calls').glob('*.response.json'))]
    uses=[json.loads(x) for x in (d/'usage.jsonl').read_text().splitlines()]
    assert len(reqs)==len(responses)==len(uses)==summary['api_calls']
    known=upper=0.;total_seconds=0.
    for req,res,u in zip(reqs,responses,uses):
        dt=datetime.fromisoformat(req['created_utc']).astimezone(timezone(timedelta(hours=8)))
        m=dt.hour*60+dt.minute;assert not(dt.weekday()<5 and(540<=m<720 or 840<=m<1080))
        usage=res['response']['usage'];assert usage==u['usage'] and u['status']=='ok'
        hit=usage.get('prompt_cache_hit_tokens',0)
        known+=(hit*.02+(usage['prompt_tokens']-hit)+usage['completion_tokens']*4)/1e6
        c=(usage['prompt_tokens']*2+usage['completion_tokens']*8)/1e6
        assert abs(c-u['estimated_cost_cny'])<1e-10;upper+=c;total_seconds+=u['duration_seconds']
    assert abs(upper-summary['peak_upper_cny'])<1e-10
    exposure=runpy.run_path(str(ROOT/'course_project/stage1/verify_development.py'))['exposure']
    def blocked(*a,**k):raise RuntimeError('Network disabled in replay')
    socket.socket.connect=blocked;socket.socket.connect_ex=blocked;socket.create_connection=blocked
    suite=get_suite('v1.2.2','banking');rows=[];payloads={}
    for row in summary['rows']:
        case=p['schedule'][row['index']];assert all(row[k]==v for k,v in case.items())
        ids=[i for i,r in enumerate(reqs) if r['case']==case]
        class Client:
            def __init__(self):self.n=0;self.chat=SimpleNamespace(completions=self)
            def create(self,**request):
                i=ids[self.n];assert request==reqs[i]['request'],'Wire request mismatch'
                self.n+=1;return ChatCompletion.model_validate(responses[i]['response'])
        client=Client();llm=DeepSeekLLM(client,'deepseek-flash',p['config'])
        llm.context=case;events=[];pipeline=build(llm,case.get('arm','baseline'),events)
        trace=read(d/row['trace']);assert sha(d/row['trace'])==row['trace_sha256']
        task=(suite.get_injection_task_by_id(row['task']) if row['phase']=='capability'
              else suite.get_user_task_by_id(row['task']))
        goal=suite.get_injection_task_by_id(row['goal']) if row['phase']=='attacked' else None
        u,a=suite.run_task_with_pipeline(pipeline,task,goal,trace['injections'])
        assert u==row['utility']
        if goal:
            assert a==row['attack_success']
            key=(row['task'],row['goal'],row.get('attack'))
            if key in payloads:assert payloads[key]==trace['injections']
            payloads[key]=trace['injections']
            if 'payloads' in p:assert trace['injections']==p['payloads'][str(row['index'])]
        assert client.n==len(ids)==row['api_calls']
        rows.append(dict(**row,exposure_verified=exposure(trace) if goal else None,checker_events=events))
    result=dict(audited_utc=stamp(),network_blocked=True,episodes=len(rows),requests=len(reqs),all_offpeak=True,
        exact_request_replay=True,identical_paired_payloads=True,known_offpeak_cny=known,
        peak_upper_cny=upper,summed_call_seconds=total_seconds,rows=rows,auditor_sha256=sha(__file__))
    write(d/'audit.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='rows'}))

if __name__=='__main__':run(sys.argv[1])
