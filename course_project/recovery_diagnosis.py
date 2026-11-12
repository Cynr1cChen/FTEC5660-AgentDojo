"""Replay each recovery trajectory only up to its added review; no generation."""
import socket
from types import SimpleNamespace
from openai.types.chat import ChatCompletion
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.task_suite.load_suites import get_suite
from course_project.stage1 import ROOT,read,write,sha,stamp
from course_project.deepseek_adapter import DeepSeekLLM
from course_project.interventions import build,RECOVERY
from course_project.results_formal import strict

def main():
    d=sorted((ROOT/'runs/formal').iterdir())[-1];results=read(ROOT/'course_project/formal/results.json')
    p=read(d/'manifest.json')['protocol'];requests=[read(x) for x in sorted((d/'calls').glob('*.request.json'))]
    responses=[read(x) for x in sorted((d/'calls').glob('*.response.json'))]
    def blocked(*a,**k):raise RuntimeError('Diagnosis is offline')
    socket.socket.connect=blocked;socket.socket.connect_ex=blocked;socket.create_connection=blocked
    s=get_suite('v1.2.2','banking');out=[]
    for row in results['rows']:
        if row['arm']!='recovery':continue
        case=p['schedule'][row['index']];ids=[i for i,r in enumerate(requests) if r['case']==case]
        review=[i for i in ids if any(m['role']=='system' and m['content']==RECOVERY for m in requests[i]['request']['messages'])]
        if not review:out.append(dict(index=row['index'],review_absent=True));continue
        first=review[0];prefix=[i for i in ids if i<first]
        class Client:
            def __init__(self):self.n=0;self.chat=SimpleNamespace(completions=self)
            def create(self,**request):
                i=prefix[self.n];assert request==requests[i]['request'];self.n+=1
                return ChatCompletion.model_validate(responses[i]['response'])
        client=Client();llm=DeepSeekLLM(client,'deepseek-flash',p['config']);base=build(llm,'baseline',[]);states=[]
        class Observed(BasePipelineElement):
            name=base.name
            def query(self,query,runtime,env,messages=(),extra_args=None):
                b=env.model_dump();v=base.query(query,runtime,env,messages,extra_args)
                states.append(dict(before=b,after=v[2].model_dump()));return v
        trace=read(d/row['trace']);goal=s.get_injection_task_by_id(row['goal']) if row['phase']=='attacked' else None
        u,a=s.run_task_with_pipeline(Observed(),s.get_user_task_by_id(row['task']),goal,trace['injections'])
        assert client.n==len(prefix)
        strict_before,flags=strict({**row,'utility':u},states[0]['before'],states[-1]['after'])
        out.append(dict(index=row['index'],trial=row['trial'],phase=row['phase'],task=row['task'],goal=row.get('goal'),
            native_before_review=u,native_after_review=row['utility'],strict_before_review=strict_before,
            strict_after_review=row['supplementary_strict_utility'],attack_before_review=a if goal else None,
            attack_after_review=row['attack_success'],extra_calls=len(ids)-len(prefix),
            initial_final_answer=requests[first]['request']['messages'][-2]['content'],
            final_answer=trace['messages'][-1]['content'],strict_before_flags=flags))
    totals={}
    for phase in ['clean','attacked']:
        rs=[r for r in out if r.get('phase')==phase]
        totals[phase]=dict(n=len(rs),native_rescued=sum(not r['native_before_review'] and r['native_after_review'] for r in rs),
            native_lost=sum(r['native_before_review'] and not r['native_after_review'] for r in rs),
            strict_rescued=sum(not r['strict_before_review'] and r['strict_after_review'] for r in rs),
            strict_lost=sum(r['strict_before_review'] and not r['strict_after_review'] for r in rs))
    write(ROOT/'course_project/formal/recovery_diagnosis.json',dict(created_utc=stamp(),network_blocked=True,
         method='Stop the SAME saved recovery trajectory immediately before the added review; replay all original tool calls and grade prefix. Not a new independent sample or a fresh ablation.',
         totals=totals,rows=out,source_sha256=sha(__file__)))
    print(totals)

if __name__=='__main__':main()
