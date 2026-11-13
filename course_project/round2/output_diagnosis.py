"""Answer-routing audit on recorded read-only Travel trajectories; no API calls."""
from course_project.stage1 import ROOT,read,write,stamp
from course_project.interventions import RECOVERY
from agentdojo.task_suite.load_suites import get_suite
from agentdojo.types import get_text_content_as_str as text

def main():
 suite=get_suite('v1.2.2','travel');out=[]
 for name in ['travel_broader','travel_output_followup']:
  d=sorted((ROOT/'runs/round2'/name).iterdir())[-1]
  for r in read(d/'audit.json')['rows']:
   if r['arm'] not in ['recovery','preserve']:continue
   tr=read(d/r['trace']);ms=tr['messages'];ss=read(d/f"episodes/{r['index']:03d}/states.json")
   assert len(ss)==1 and ss[0]['before']==ss[0]['after']
   idx=next(i for i,m in enumerate(ms) if m['role']=='system' and text(m['content'])==RECOVERY)
   native=ms[idx-1];assert native['role']=='assistant' and not native.get('tool_calls')
   env=suite.load_and_inject_default_environment(tr['injections']);env=type(env).model_validate(ss[0]['before']);task=suite.get_user_task_by_id(r['task'])
   score=lambda m:bool(task.utility(text(m['content']),env,env.model_copy(deep=True)))
   no_calls=not any(m['role']=='assistant' and m.get('tool_calls') for m in ms[idx+1:])
   final=ms[-1];selected=native if no_calls else final
   review=final
   if r['arm']=='preserve':
    events=read(d/f"episodes/{r['index']:03d}/decisions.json");route=[e for e in events if e.get('stage')=='output_route'];assert len(route)==1
    assert route[0]['retain_native_answer']==no_calls
    if no_calls:
     assert final==native;review=ms[-2]
   assert score(final)==r['utility']
   out.append(dict(cohort=name,index=r['index'],arm=r['arm'],task=r['task'],phase=r['phase'],trial=r['trial'],no_review_tool_proposals=no_calls,native=score(native),review=score(review),actual_final=score(final),counterfactual_select=score(selected)))
 summary={}
 for name in ['travel_broader','travel_output_followup']:
  for arm in ['recovery','preserve']:
   for phase in ['clean','attacked']:
    xs=[r for r in out if (r['cohort'],r['arm'],r['phase'])==(name,arm,phase)]
    if xs:summary['/'.join([name,arm,phase])]=dict(n=len(xs),native=sum(r['native'] for r in xs),review=sum(r['review'] for r in xs),final=sum(r['actual_final'] for r in xs),counterfactual_select=sum(r['counterfactual_select'] for r in xs),review_lost=sum(r['native'] and not r['review'] for r in xs),review_rescued=sum(not r['native'] and r['review'] for r in xs),no_review_tool_proposals=sum(r['no_review_tool_proposals'] for r in xs))
 write(ROOT/'course_project/round2/output_diagnosis.json',dict(created_utc=stamp(),method='Same recorded read-only trajectory; original-answer selection requires no additional review tool proposal. Actual policy output separately checked. Native text grader only; this is not independent semantic assessment.',limitations='Post-hoc candidate and same-task fresh follow-up. Selection may discard a beneficial purely textual correction. Scorer is literal-sensitive. No security gain established.',summary=summary,rows=out));print(summary)
if __name__=='__main__':main()
