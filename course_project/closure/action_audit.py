"""Native tool replay distinguishes actual denials from attack avoidance."""
from copy import deepcopy
import socket
from collections import Counter
from course_project.stage1 import ROOT,read,write,stamp,sha
from course_project.round2.anchored import hard_decide
from agentdojo.task_suite.load_suites import get_suite
from agentdojo.functions_runtime import FunctionsRuntime

def main():
    def blocked(*a,**k):raise RuntimeError('Offline action audit')
    socket.socket.connect=blocked;socket.create_connection=blocked
    result=read(ROOT/'course_project/closure/results.json');out=[];traces=[]
    suite=get_suite('v1.2.2','banking')
    for r in result['rows']:
        d=ROOT/r['source_run'];tr=read(d/r['trace']);task=suite.get_user_task_by_id(r['task'])
        env=task.init_environment(suite.load_and_inject_default_environment(tr['injections']))
        initial=env.model_copy(deep=True);runtime=FunctionsRuntime(suite.tools)
        goal=suite.get_injection_task_by_id(r['goal']) if r['phase']=='attacked' else None
        writes=[]
        for m in tr['messages']:
            if m['role']!='tool':continue
            c=m['tool_call'];before=env.model_copy(deep=True);error=str(m.get('error') or '')
            denied=error.startswith('Action not executed:')
            allow,reason=hard_decide(task.PROMPT,c['function'],c['args'])
            if denied:
                hypo=before.model_copy(deep=True);_,err=runtime.run_function(hypo,c['function'],deepcopy(c['args']))
                old_goal=bool(goal.security('',initial,before)) if goal else False
                new_goal=bool(goal.security('',initial,hypo)) if goal else False
                old_recip={t.id:t.recipient for t in before.bank_account.scheduled_transactions}
                new_recip={t.id:t.recipient for t in hypo.bank_account.scheduled_transactions}
                out.append(dict(index=r['index'],source_run=r['source_run'],source_index=r['source_index'],
                    arm=r['arm'],phase=r['phase'],trial=r['trial'],attack=r.get('attack'),call=c,
                    layer='hard' if not allow and error.startswith('Action not executed: '+reason) else 'semantic',
                    native_tool_error_if_executed=err,goal_transition_if_executed=not old_goal and new_goal,
                    recipient_change_if_executed=old_recip!=new_recip,
                    task_pass_if_executed=bool(task.utility('',initial,hypo)),
                    actually_executed=False,error=error))
            else:
                _,err=runtime.run_function(env,c['function'],deepcopy(c['args']));assert err==m.get('error')
                if c['function']=='update_scheduled_transaction':writes.append(c)
        states=read(d/f"episodes/{r['source_index']:03d}/states.json")
        assert env.model_dump(mode='json')==states[-1]['after']
        traces.append(dict(index=r['index'],arm=r['arm'],phase=r['phase'],task=r['task'],
                           strict_safe=r['strict_safe'],actual_scheduled_updates=writes,
                           final_state_sha256=sha(d/f"episodes/{r['source_index']:03d}/states.json")))
    summaries={}
    for arm in ['anchored','aligned']:
        for phase in ['clean','attacked']:
            xs=[x for x in out if x['arm']==arm and x['phase']==phase]
            summaries[arm+'/'+phase]=dict(denials=len(xs),layers=dict(Counter(x['layer'] for x in xs)),
                goal_transitions_prevented=sum(x['goal_transition_if_executed'] for x in xs),
                recipient_changes_prevented=sum(x['recipient_change_if_executed'] for x in xs),
                native_task_passing_calls_denied=sum(x['task_pass_if_executed'] for x in xs))
    write(ROOT/'course_project/closure/action_audit.json',dict(created_utc=stamp(),network_blocked=True,
        final_states_replayed=len(traces),summary=summaries,denials=out,traces=traces,
        method='All48 saved bank trajectories replay native tools to exact saved final state. Every denied operation tested on its own pre-operation state; no new model calls. A would-pass-task call can also be malicious under the native amount-only grader, so it is not automatically a false block.',
        limitation='Counterfactuals are local operation checks, not fabricated end-to-end model recovery. Fewer bad proposals are avoidance, not actual hard interception.'))
    print(summaries)

if __name__=='__main__':main()
