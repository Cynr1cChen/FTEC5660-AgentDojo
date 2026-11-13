"""Offline classification of all prior anchored rent cases, before new draws."""
from collections import Counter
from course_project.stage1 import ROOT,read,write,sha,stamp
from agentdojo.types import get_text_content_as_str

def main():
    out=[]
    for path in read(ROOT/'course_project/round2/anchored_merged_results.json')['runs']:
        d=ROOT/path;a=read(d/'audit.json');assert a['passed']
        for r in a['rows']:
            if r['arm']!='anchored' or r['task']!='user_task_12':continue
            ep=d/f"episodes/{r['index']:03d}"
            tr=read(d/r['trace']);events=read(ep/'decisions.json')
            tools=[m for m in tr['messages'] if m['role']=='tool']
            writes=[m for m in tools if m['tool_call']['function']=='update_scheduled_transaction']
            hard=[e for e in events if e.get('stage')=='anchored_rule' and e['decision']=='deny']
            sem=[e for e in events if e.get('stage') is None and e.get('decision')=='deny']
            category=('completed' if r['utility'] else 'hard_denied' if hard else
                      'semantic_denied' if sem else 'no_write_proposal')
            amount_only=[e for e in sem if e['operation']=='update_scheduled_transaction' and
                         set(e['args'])=={'id','amount'}]
            out.append(dict(source_run=path,index=r['index'],phase=r['phase'],trial=r['trial'],attack=r.get('attack'),
                            category=category,amount_only_denials=amount_only,hard_denials=len(hard),
                            semantic_denials=len(sem),write_proposals=len(writes),utility=r['utility'],
                            final_text=get_text_content_as_str(tr['messages'][-1]['content']),
                            decisions=events,trace_sha256=sha(d/r['trace']),audit_sha256=sha(d/'audit.json')))
    attacks=[x for x in out if x['phase']=='attacked']
    counts=dict(Counter(x['category'] for x in attacks))
    assert len(attacks)==12 and counts==dict(hard_denied=7,semantic_denied=2,no_write_proposal=3)
    assert sum(bool(x['amount_only_denials']) for x in attacks)==1
    write(ROOT/'course_project/closure/prior_diagnosis.json',dict(created_utc=stamp(),api_calls=0,
         method='All15 prior anchored rent cases, including12 attacked. Categories use saved tool proposals and actual denial events, not semantic NLP labels. Full final text retained. Interpretation is one unblinded assistant review.',
         attack_categories=counts,hypothesis='Shared authority policy may reduce unnecessary confirmation and contradictory semantic rejection of separable ordinary updates. No claim that these explain every failure.',rows=out))
    print(counts)

if __name__=='__main__':main()
