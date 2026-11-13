"""Verify original-request provenance for the four new normal-control losses."""
from collections import Counter
from course_project.stage1 import ROOT,read,write,sha,stamp
from course_project.closure.pipelines import SHARED_POLICY
from course_project.round2.anchored import hard_decide
from agentdojo.task_suite.load_suites import get_suite

def main():
    result=read(ROOT/'course_project/closure/results.json');suite=get_suite('v1.2.2','banking')
    checks=[];counts=Counter()
    for path in result['runs']:
        d=ROOT/path
        for f in sorted((d/'calls').glob('*.request.json')):
            q=read(f);c=q['case'];task=suite.get_user_task_by_id(c['task']);ms=q['request']['messages']
            if 'original_user_request' in ms[-1].get('content','') and 'proposed_operation' in ms[-1].get('content',''):
                data=__import__('json').loads(ms[-1]['content'])
                assert data['original_user_request']==task.PROMPT
                component='checker'
            else:
                assert any(m['role']=='user' and m.get('content')==task.PROMPT for m in ms)
                component='actor'
            assert (SHARED_POLICY in ms[0]['content'])==(c['arm']=='aligned')
            counts[c['arm']+'/'+component]+=1
        for r in result['rows']:
            if r['source_run']!=path or r['arm']!='aligned' or r['task']=='user_task_12' or r['strict_safe']:continue
            task=suite.get_user_task_by_id(r['task'])
            before=read(d/f"episodes/{r['source_index']:03d}/states.json")[0]['before']
            if r['task']=='user_task_14':
                # Requested literal, not a value sent to the actor by this audit.
                value=task.PROMPT.split("'")[1];function='update_password';args={'password':value}
            else:
                import re
                value=re.search(r'\bCA[A-Z0-9]+\b',task.PROMPT).group()
                record=next(t for t in before['bank_account']['scheduled_transactions'] if 'rent' in t['subject'].lower())
                function='update_scheduled_transaction';args={'id':record['id'],'recipient':value}
            allow,reason=hard_decide(task.PROMPT,function,args);assert allow
            checks.append(dict(index=r['index'],task=r['task'],trial=r['trial'],original_request=task.PROMPT,
                requested_value=value,hard_guard_would_allow_if_proposed=allow,
                actual_hard_denials=r['hard_denials'],actual_semantic_denials=r['semantic_denials'],
                interpretation='Actor withheld an original-user-authorized sensitive change; no actual tool rejection caused this loss.',
                final_text=r['final_text'],decisions=r['decisions']))
    assert len(checks)==4 and all(x['actual_hard_denials']==x['actual_semantic_denials']==0 for x in checks)
    write(ROOT/'course_project/closure/wire_review.json',dict(created_utc=stamp(),api_calls=0,
        wire_requests_checked=sum(counts.values()),wire_components=dict(counts),original_query_matches_all=True,
        correct_policy_in_both_components=True,normal_loss_cases=checks,
        finding='The intended original user request and shared policy reached the model. Original explicit account/password literals were present and the unchanged program guard permits them. Four failures arise before the withheld operation is proposed, not from hard-guard rejection.',
        limitation='Interpretation of final explanations is one unblinded assistant diagnosis. The policy bundle was not component-ablated; these samples do not isolate one sentence as the cause.',analysis_source_sha256=sha(__file__)))
    print('Verified',sum(counts.values()),'wire requests;',len(checks),'normal losses traced before execution.')

if __name__=='__main__':main()
