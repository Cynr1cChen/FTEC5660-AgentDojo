"""Complete bounded development search with two released author baselines."""
import sys
from agentdojo.attacks import load_attack
from agentdojo.models import MODEL_NAMES
from types import SimpleNamespace
from course_project.extension import runner as r

def generate(suite,task,goal,style):
 MODEL_NAMES['deepseek-flash']='DeepSeek'
 return load_attack(style,suite,SimpleNamespace(name='deepseek-flash')).attack(task,goal)
def freeze():
 r.generate=generate;cases=[]
 for suite,tasks,goals in [('workspace',[6,29,33],[0,1]),('slack',[1,3,6],[1,4])]:
  for style in ['direct','injecagent']:
   for t in tasks:
    for g in goals:cases.append(dict(suite=suite,phase='attacked',task=f'user_task_{t}',goal=f'injection_task_{g}',attack=style,arm='baseline',trial=0))
 r.freeze('author_baselines_development',cases,2,dict(development_only=True,final_bounded_search=True,reason='Add released TODO/direct and InjecAgent templates to the five structural/workflow styles and three routing styles already tested. Preserve unchanged trusted channel/model/scorers. No further search planned if zero.'))
if __name__=='__main__':
 if sys.argv[1]=='freeze':freeze()
 elif sys.argv[1]=='run':r.run('author_baselines_development')
