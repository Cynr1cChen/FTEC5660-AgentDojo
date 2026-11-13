"""Fresh same-development-task confirmation, not held-out efficacy."""
from course_project.extension import runner as r
from course_project.stage1 import read,sha
def freeze():
 p=read(r.HERE/'parameter_development/protocol.json');cases=[];payloads={}
 for trial in range(3):
  for i,c in enumerate(p['schedule'][5:]):
   arms=['baseline','guard','recovery'];j=(trial+i)%3;arms=arms[j:]+arms[:j]
   for arm in arms:cases.append({**c,'trial':trial,'arm':arm})
 old=r.generate
 r.generate=lambda suite,task,goal,style: next(p['payloads'][str(i)] for i,c in enumerate(p['schedule']) if c.get('attack')==style and c['task']==task.ID)
 r.freeze('parameter_confirmation',cases,1.0,dict(development_confirmation=True,held_out=False,trials=3,parent_protocol_sha256=sha(r.HERE/'parameter_development/protocol.json'),reason='First observed native/state recipient redirections on task2. Retain all four styles, clean controls, baseline/gate/recovery; no prompt tuning.',authorization_caveat='User delegates to landlord notice. Account-change instructions in that source create an authorization/data-integrity ambiguity; native goal success is not by itself proof of unambiguous semantic violation. No general prevention claim.'))
if __name__=='__main__':freeze()
