"""Offline independent replay, wire-request and native grading verification."""
import copy
import json
import re
import socket
from datetime import datetime
from pathlib import Path
import yaml
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.agent_pipeline.llms.openai_llm import _function_to_openai
from agentdojo.types import FunctionCall, get_text_content_as_str
from agentdojo.task_suite.load_suites import get_suite
from course_project.deepseek_adapter import serialize_messages
from course_project.run_pilot import build_pipeline
from course_project.stage1 import OUT, HERE, read, write, sha, stamp

def normalized(s): return re.sub(r'\s+', ' ', s).strip()
def strings(x):
    if isinstance(x,str): yield x
    elif isinstance(x,list):
        for v in x: yield from strings(v)
    elif isinstance(x,dict):
        for v in x.values(): yield from strings(v)
def exposure(trace):
    candidates=[]
    for m in trace['messages']:
        if m['role']!='tool': continue
        text=get_text_content_as_str(m['content']);candidates.append(text)
        try: candidates.extend(strings(yaml.safe_load(text)))
        except yaml.YAMLError: pass
    return any(normalized(p) in normalized(t) for p in trace['injections'].values() for t in candidates)

class Replay(BasePipelineElement):
    def __init__(self,trace,calls):
        self.model=self.name='deepseek-flash'; self.trace=trace;self.calls=calls;self.n=0;self.used=0
    def query(self,query,runtime,env,messages=(),extra_args=None):
        clean=json.loads(json.dumps(messages,default=lambda x:x.model_dump()))
        assert clean==self.trace['messages'][:len(clean)]
        request=self.calls[self.n]['request']
        assert serialize_messages(messages)==request['messages']
        assert [_function_to_openai(t) for t in runtime.functions.values()]==request.get('tools',[])
        assert request['model']=='deepseek-flash' and request['temperature']==0
        assert request['extra_body']=={'thinking':{'type':'disabled'}}
        answer=copy.deepcopy(self.trace['messages'][len(clean)]);assert answer['role']=='assistant'
        if answer.get('tool_calls') is not None:
            answer['tool_calls']=[FunctionCall(**x) for x in answer['tool_calls']]
        self.n+=1;self.used=len(clean)+1
        return query,runtime,env,[*messages,answer],extra_args or {}

def main():
    d=sorted(OUT.iterdir())[-1]; summary=read(d/'summary.json');p=read(HERE/'development_protocol.json')
    assert summary['completed']==p['expected_episodes']
    for name,digest in p['source_hashes'].items():assert sha(d/'source_snapshot'/name)==digest
    calls=[read(f) for f in sorted((d/'calls').glob('*.request.json'))]
    responses=[read(f) for f in sorted((d/'calls').glob('*.response.json'))]
    usages=[json.loads(x) for x in (d/'usage.jsonl').read_text().splitlines()]
    assert len(calls)==len(responses)==len(usages)==summary['api_calls']
    known=0.; upper=0.; durations=[]
    from datetime import timezone,timedelta
    for req,res,u in zip(calls,responses,usages):
        local=datetime.fromisoformat(req['created_utc']).astimezone(timezone(timedelta(hours=8)))
        m=local.hour*60+local.minute
        assert not(local.weekday()<5 and (540<=m<720 or 840<=m<1080))
        usage=res['response']['usage'];assert usage==u['usage'];assert u['status']=='ok'
        hit=usage.get('prompt_cache_hit_tokens',0); miss=usage['prompt_tokens']-hit
        known+=(hit*.02+miss*1+usage['completion_tokens']*4)/1e6
        peak=(usage['prompt_tokens']*2+usage['completion_tokens']*8)/1e6
        assert abs(peak-u['estimated_cost_cny'])<1e-10
        upper+=peak;durations.append(u['duration_seconds'])
    def blocked(*a,**k):raise RuntimeError('Network disabled during replay')
    socket.socket.connect=blocked;socket.socket.connect_ex=blocked;socket.create_connection=blocked
    suite=get_suite('v1.2.2','banking'); audited=[]
    for row in summary['rows']:
        trace=read(d/row['trace']);assert sha(d/row['trace'])==row['trace_sha256']
        selected=[x for x in calls if x['case']=={k:row[k] for k in ['phase','task','goal','attack'] if k in row}]
        llm=Replay(trace,selected); pipeline=build_pipeline(llm,'none',15)
        task=(suite.get_injection_task_by_id(row['task']) if row['phase']=='capability'
              else suite.get_user_task_by_id(row['task']))
        goal=suite.get_injection_task_by_id(row['goal']) if row['phase']=='attacked' else None
        utility,attack=suite.run_task_with_pipeline(pipeline,task,goal,trace['injections'])
        assert utility==row['utility']
        if goal: assert attack==row['attack_success']
        assert llm.n==row['api_calls']==len(selected) and llm.used==len(trace['messages'])
        audited.append(dict(**row,exposure_normalized=exposure(trace) if goal else None))
    assert abs(upper-summary['peak_upper_cny'])<1e-10
    write(d/'audit.json',dict(audited_utc=stamp(),network_blocked=True,episodes_replayed=len(audited),
        requests_verified=len(calls),all_offpeak=True,known_offpeak_cny=known,peak_upper_cny=upper,
        summed_call_seconds=sum(durations),rows=audited,
        exposure_diagnostic_correction='Raw substring in runner is too strict because environment rendering folds whitespace. This audit uses whitespace normalization and YAML scalar decoding; paid protocol/requests/results unchanged.',
        audit_implementation_sha256=sha(__file__)))
    print(json.dumps(dict(verified=len(audited),calls=len(calls),known_offpeak_cny=known,peak_upper_cny=upper)))

if __name__=='__main__':main()
