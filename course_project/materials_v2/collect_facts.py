"""Read frozen research results and create the shared materials data snapshot.

No model generation, experiment execution, scorer changes or research writes.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]

def read(path):
    return json.loads((ROOT / path).read_text())

def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

def main():
    ledger = read('course_project/materials_v2/evidence_ledger.json')
    sources = {}
    raw = {}
    for s in ledger['studies']:
        assert digest(s['source']) == s['source_sha256'], s['source']
        raw[s['id']] = read(s['source'])
        sources[s['id']] = {k:s[k] for k in ['label','source','source_sha256','control']}
    for k, v in ledger['notes'].items():
        if 'path' in v:
            assert digest(v['path']) == v['sha256'], v['path']
            sources[k] = v
    facts = {'sources':sources, 'upstream_commit':'089ed468cf3ed0322acc66b0211f26d9d90dbf60',
             'paper':'https://arxiv.org/html/2406.13352v3', 'main':{}, 'dated':{},
             'neutral':{}, 'transfer':{}, 'authorization':{}, 'closure':raw['S9']['groups']}
    for sid,key,nclean,nattack in [('S1','main',18,36),('S2','dated',9,18)]:
        for a, v in raw[sid]['arms'].items():
            ms=v['metrics']; m=ms['attacked_safe_completion']; c=ms['clean_utility']
            facts[key][a] = {'safe':m, 'clean':c, 'count':round(m['mean']*nattack),
                'n':nattack, 'clean_count':round(c['mean']*nclean), 'clean_n':nclean,
                'asr':ms['attacked_attack_success'],
                'mean_calls':v['mean_calls_per_episode'], 'mean_api_seconds':v['mean_api_seconds_per_episode'],
                'estimated_cny':v['known_offpeak_cny']}
    for a,v in raw['S3']['arms'].items():
        facts['neutral'][a] = v['metrics']
    for sid in ['S4a','S4b','S4c','S5a','S5b']:
        facts['transfer'][sid]={a:v['metrics'] for a,v in raw[sid]['arms'].items()}
    for sid in ['S6','S7','S8']:
        facts['authorization'][sid]={a:v['metrics'] for a,v in raw[sid]['arms'].items()}
    facts['prefix']=read(ledger['notes']['same_prefix']['path'])['summary']
    sens=read(ledger['notes']['sensitivity']['path'])
    facts['sensitivity']={a:{k:v for k,v in x.items() if k!='items'} for a,x in sens['arms'].items()}
    facts['travel_diagnosis']=read('course_project/round2/output_diagnosis.json')['summary']
    facts['gate_diagnosis']=read('course_project/round2/gate_diagnosis.json')['summary']
    facts['closure_action_audit']=read('course_project/closure/action_audit.json')['summary']
    facts['closure_cost']=raw['S9']['cost']
    bp=read('course_project/extension_review/banking_prefix.json')
    bank=next(r for r in bp['rows'] if r['arm']=='recovery' and r['phase']=='attacked'
              and not r['before'] and r['after'] and r['task']=='user_task_4')
    travel=next(r for r in read('course_project/round2/travel_diagnosis.json')['rows']
                if r['arm']=='recovery' and r['before'] and not r['after'])
    wire=read('course_project/closure/wire_review.json')
    facts['examples']={'bank':bank,'travel':travel,'authority':wire['normal_loss_cases'][2]}
    facts['wire']={k:v for k,v in wire.items() if k not in ['normal_loss_cases','analysis_source_sha256']}
    facts['stage_runs']=[326,587,677,48]
    facts['completed_runs']=sum(facts['stage_runs'])
    facts['tests']=60
    (HERE/'facts.json').write_text(json.dumps(facts,indent=2,ensure_ascii=False)+'\n')
    print('Verified',len(ledger['studies']),'result sources and',len(sources),'source records')

if __name__=='__main__':
    main()
