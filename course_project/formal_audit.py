"""Extends exact-request replay with BEFORE/AFTER state verification."""
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
import course_project.audit_controlled as a
from course_project.stage1 import ROOT,read,write,sha

def main(phase='formal'):
    d=sorted((ROOT/f'runs/{phase}').iterdir())[-1]
    original=a.build;verified=[]
    def observe(llm,arm,events):
        delegate=original(llm,arm,events);case=llm.context
        if phase=='date_followup':
            from course_project.dated import DATE_CONTEXT
            delegate.elements[0].system_message+='\n'+DATE_CONTEXT
        name='_'.join(str(case.get(k,'none')) for k in ['trial','arm','phase','task','goal'])
        expected=read(d/f'states/{name}.json')
        class Observer(BasePipelineElement):
            name=delegate.name
            def __init__(self):self.n=0
            def query(self,query,runtime,env,messages=(),extra_args=None):
                before=env.model_dump();result=delegate.query(query,runtime,env,messages,extra_args)
                assert dict(before=before,after=result[2].model_dump())==expected[self.n]
                self.n+=1;verified.append(name)
                return result
        return Observer()
    a.build=observe;a.run(phase)
    result=read(d/'audit.json')
    expected_count=sum(len(read(p)) for p in (d/'states').glob('*.json'))
    assert len(verified)==expected_count
    result.update(state_replays_verified=len(verified),state_files_verified=len(set(verified)),
                  state_replay_auditor_sha256=sha(__file__))
    write(d/'audit.json',result)
    print('All formal environment snapshots independently replayed:',len(verified))

if __name__=='__main__':
    import sys
    main(sys.argv[1] if len(sys.argv)>1 else 'formal')
