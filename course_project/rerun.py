"""Portable NEW sampling entry. Dry-run by default; never overwrites study runs."""
import argparse
import copy
from datetime import datetime,timezone
from course_project.stage1 import ROOT,read,write,sha,sources,previous_spending
import course_project.stage1 as s

def main():
    a=argparse.ArgumentParser();a.add_argument('--context',choices=['original','dated'],default='original')
    a.add_argument('--budget-cny',type=float,default=3);a.add_argument('--live',action='store_true')
    args=a.parse_args();assert 0<args.budget_cny<=10
    phase='formal' if args.context=='original' else 'date_followup'
    p=copy.deepcopy(read(ROOT/f'course_project/{phase}/protocol.json'))
    if not args.live:
        print(dict(dry_run=True,episodes=len(p['schedule']),context=args.context,
                   cap_cny=args.budget_cny,requires_key_only_with_live=True));return
    # Both code paths preserve the study interventions and out-of-model state observer.
    if phase=='formal':
        from course_project.formal import configure
    else:
        from course_project.dated import configure
    configure()
    tag=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    base=ROOT/'runs/rerun'/tag;s.HERE=base/'control';s.OUT=base/'execution'
    s.CONFIG={**p['config'],'run_budget_cny':args.budget_cny}
    ledger=read(ROOT/'course_project/date_followup/results.json')['cost']['project_upper_cny']
    for old in (ROOT/'runs/rerun').glob('*/execution/*/summary.json'):ledger+=read(old)['peak_upper_cny']
    assert ledger+args.budget_cny<=100,'Project100CNY guard leaves insufficient budget'
    p.update(created_utc=datetime.now(timezone.utc).isoformat(),purpose='NEW sampling rerun, separate from frozen study',
        config=s.CONFIG,amem_cost_sources={},amem_prior_upper_cny=ledger-previous_spending(),
        source_hashes={str(f.relative_to(ROOT)):sha(f) for f in sources()},
        parent_protocol_sha256=sha(ROOT/f'course_project/{phase}/protocol.json'),
        portable_ledger_note='Uses released final conservative project bound plus all later local reruns; no external A-Mem folder is required.')
    write(s.HERE/'development_protocol.json',p);s.run()

if __name__=='__main__':main()
