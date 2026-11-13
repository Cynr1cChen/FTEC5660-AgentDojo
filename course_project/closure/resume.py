"""Resume only the unchanged remainder after explicit user resumption."""
from copy import deepcopy
import json
from course_project.closure import runner as r
from course_project.stage1 import ROOT,read,write,sha,stamp

def main():
    d=sorted((ROOT/'runs/closure/shared_policy').iterdir())[-1]
    s=read(d/'summary.json');p=read(d/'manifest.json')['protocol'];offset=s['completed']
    assert offset==14 and len(s['rows'])==offset and all(x['status']=='completed' for x in s['rows'])
    uses=[json.loads(x) for x in (d/'usage.jsonl').read_text().splitlines()]
    pending=[f for f in sorted((d/'calls').glob('*.request.json')) if not f.with_name(f.name.replace('.request.','.response.')).exists()]
    assert len(pending)==1 and uses[-1]['status']=='error' and 'usage' not in uses[-1]
    assert read(pending[0])['case']==p['schedule'][offset]
    receipt=dict(created_utc=stamp(),pending_requests=[f.name for f in pending],
        pending_request_hashes={f.name:sha(f) for f in pending},unknown_reservation_cny=0,
        reservation_already_in_usage_cny=uses[-1]['estimated_cost_cny'],completed_before_interruption=offset,
        cause='User explicitly paused the turn; SIGINT stopped the runner. User has now explicitly requested resumption.',
        accounting='Reservation is already in usage.jsonl. Do not count it twice. Partial responses and trace retained, no outcome assigned to interrupted case.')
    target=d/'interruption.json';assert not target.exists();write(target,receipt)
    actors={'course_project/deepseek_adapter.py','course_project/stage1.py','course_project/interventions.py',
            'course_project/run_pilot.py','course_project/extension/pipelines.py','course_project/extension/runner.py',
            'course_project/round2/anchored.py','course_project/round2/pipelines.py','course_project/round2/contract.py',
            'course_project/round2/rubrics.py','course_project/closure/pipelines.py',
            'course_project/closure/rubrics.py','course_project/closure/runner.py'}
    for name,digest in p['source_hashes'].items():
        if name.startswith('src/') or name in actors:assert sha(ROOT/name)==digest,name
    q=deepcopy(p);remaining=round(p['config']['run_budget_cny']-s['peak_upper_cny'],12);assert remaining>0
    q.update(name='shared_policy_continuation',created_utc=stamp(),schedule=p['schedule'][offset:],
        expected_episodes=48-offset,original_index_offset=offset,parent_protocol_sha256=sha(r.HERE/'shared_policy/protocol.json'),
        prior_upper_cny=r.prior_spending(),source_hashes={str(f.relative_to(ROOT)):sha(f) for f in r.source_files()},
        payloads={str(int(i)-offset):v for i,v in p['payloads'].items() if int(i)>=offset},
        amendment='Explicit user pause/resume only. Preserve14 completed original cases and all partial request costs. Restart interrupted case in fresh simulated environment and run exact remaining34 cases. Same actor, rubric, model, tasks, contexts and payloads. No quality retry or candidate change. Total original+continuation cap remains5CNY.',
        original_and_continuation_cap_cny=5,actor_source_hashes={name:p['source_hashes'][name] for name in sorted(actors)})
    q['config']['run_budget_cny']=remaining;q['config']['max_api_calls']=p['config']['max_api_calls']-s['api_calls']
    path=r.HERE/'shared_policy_continuation/protocol.json';assert not path.exists();write(path,q)
    print('Frozen unchanged remainder',q['expected_episodes'],'cap',remaining,'cumulative',r.prior_spending())

if __name__=='__main__':main()
