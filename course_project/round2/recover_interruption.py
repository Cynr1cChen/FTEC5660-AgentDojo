"""Reconstruct a process-interrupted cohort without fabricating observations."""
import json
from course_project.stage1 import ROOT,read,write,sha,stamp

def main():
 d=sorted((ROOT/'runs/round2/anchored_formal').iterdir())[-1]
 assert not (d/'summary.json').exists() and not (d/'interruption.json').exists()
 p=read(d/'manifest.json')['protocol'];rows=[read(f) for f in sorted(d.glob('episodes/*/result.json'))]
 assert [r['index'] for r in rows]==list(range(len(rows))) and all(r['status']=='completed' for r in rows)
 requests=sorted((d/'calls').glob('*.request.json'));responses=sorted((d/'calls').glob('*.response.json'))
 pending=[f for f in requests if not f.with_name(f.name.replace('.request.','.response.')).exists()]
 uses=[json.loads(l) for l in (d/'usage.jsonl').read_text().splitlines()];assert len(responses)==len(uses)
 unknown=0
 for f in pending:
  q=read(f)['request'];n=len(json.dumps(dict(messages=q['messages'],tools=q.get('tools',[])),ensure_ascii=False).encode('utf-8'))+64*len(q['messages'])+512
  unknown+=(n*2+p['config']['max_output_tokens']*8)/1e6
 offset=len(rows);case=p['schedule'][offset];assert all(read(f)['case']==case for f in pending)
 case_uses=[u for u in uses if all(u.get(k)==v for k,v in case.items())]
 error=dict(index=offset,**case,status='error',error_type='ProcessInterrupted',error_message='Process absent on resumed session; final request has no saved response. Cause unestablished. Not an empirical task failure or successful defense.',api_calls=len(case_uses)+len(pending),peak_upper_cny=sum(u['estimated_cost_cny'] for u in case_uses)+unknown,reconstructed=True)
 write(d/'interruption.json',dict(created_utc=stamp(),completed_before_interruption=offset,pending_requests=[f.name for f in pending],pending_request_hashes={f.name:sha(f) for f in pending},unknown_reservation_cny=unknown,basis='Same byte-length input bound and maximum output tokens as adapter, peak no-cache prices. Actual billing unknown; no fabricated response or usage row.',original_artifacts_preserved=True,process_absence_observed=True))
 total=sum(u['estimated_cost_cny'] for u in uses)+unknown
 write(d/'summary.json',dict(created_utc=stamp(),name=p['name'],expected_episodes=p['expected_episodes'],completed=offset,api_calls=len(requests),peak_upper_cny=total,project_upper_cny=read(d/'manifest.json')['prior_upper_cny']+total,rows=[*rows,error],reconstructed_after_process_interruption=True,unknown_reservation_cny=unknown))
 print('Recovered completed',offset,'pending requests',len(pending),'reserved unknown CNY',unknown)
if __name__=='__main__':main()
