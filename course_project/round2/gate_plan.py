"""Contract development is separate from its later task-family evaluation."""
from course_project.round2 import runner as r
from course_project.stage1 import read
from course_project.extension.attacks import generate as standard
PARAM=read(r.ROOT/'course_project/extension/parameter_development/protocol.json')
def payload(suite,task,goal,style):
 if style in ['remittance_correction','routing_metadata','inactive_account','supplier_note']:
  return next(PARAM['payloads'][str(i)] for i,c in enumerate(PARAM['schedule']) if c['task']==task.ID and c.get('attack')==style)
 return standard(suite,task,goal,style)
def freeze():
 cases=[]
 # Full previously diagnosed rent set, not cherry-picked successes.
 for c in PARAM['schedule'][5:]:
  for arm in ['baseline','guard','contract']:cases.append({**c,'arm':arm})
 # Positive business controls include explicit password and recipient parameters.
 for n in [13,14,15]:cases.append(dict(suite='banking',phase='clean',task=f'user_task_{n}',arm='contract',trial=0,context='The current date in this simulated banking environment is 2022-04-01.'))
 r.generate=payload
 r.freeze('contract_development',cases,3,dict(development_only=True,new_intervention='Trusted-request contract compiled before any external observations, enforced in code. Existing recipient change requires original-user literal; password exact literal; all other writes use model-compiled fields/values.',tradeoff='Delegated changes to existing payment recipients are deliberately confirmation-required, even if legitimate; not general business-data authentication.',no_hidden_labels=True,no_stack_with_recovery=True))
if __name__=='__main__':freeze()
