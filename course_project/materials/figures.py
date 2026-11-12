"""Scientific evidence plots for the PDF; PowerPoint charts are native objects."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[2];O=R/'course_project/runs/materials_agentdojo_20261113/assets';O.mkdir(parents=True,exist_ok=True)
F=json.loads((R/'course_project/formal/results.json').read_text());D=json.loads((R/'course_project/date_followup/results.json').read_text())
J=json.loads((R/'course_project/formal/recovery_diagnosis.json').read_text())
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#999999','svg.fonttype':'none'})
arms=['baseline','repeat','recovery'];labels=['Baseline','Repeat prompt','Bounded recovery'];blue='#263D6D';teal='#35847C'
def bars(name,series,ylabel='Completion (%)'):
 fig,ax=plt.subplots(figsize=(8.5,4.1));x=np.arange(len(labels));width=.34
 for j,(lab,values,color) in enumerate(series):
  p=x+(j-(len(series)-1)/2)*width;b=ax.bar(p,values,width,color=color,label=lab)
  ax.bar_label(b,labels=[f'{v:.1f}' for v in values],padding=4,fontsize=11)
 ax.set_xticks(x,labels);ax.set_ylim(0,113);ax.set_yticks([0,25,50,75,100]);ax.set_ylabel(ylabel)
 ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);ax.legend(loc='upper left',bbox_to_anchor=(0,1.18),ncol=2,frameon=False)
 fig.tight_layout();fig.savefig(O/(name+'.png'),dpi=240,bbox_inches='tight');fig.savefig(O/(name+'.svg'),bbox_inches='tight');plt.close(fig)
bars('main',[('No attack',[F['arms'][a]['metrics']['clean_utility']['mean']*100 for a in arms],'#A9B2C2'),('Under attack',[F['arms'][a]['metrics']['attacked_safe_completion']['mean']*100 for a in arms],blue)])
original=[]
for a in arms:
 rows=[r for r in F['rows'] if r['arm']==a and r['phase']=='attacked' and r['task'] in ['user_task_4','user_task_11','user_task_15']]
 original.append(sum(r['utility'] and not r['attack_success'] for r in rows)/len(rows)*100)
bars('date_context',[('Original context: same 3 tasks',original,'#A9B2C2'),('Shared simulation date',[D['arms'][a]['metrics']['attacked_safe_completion']['mean']*100 for a in arms],teal)],'Safe completion (%)')
fig,ax=plt.subplots(figsize=(8.5,4.1));x=np.arange(2)
before=[13/18*100,14/36*100];after=[100,31/36*100]
for pos,(lab,vals,col,counts) in enumerate([('Before added review',before,'#A9B2C2',['13/18','14/36']),('After added review',after,teal,['18/18','31/36'])]):
 b=ax.bar(x+(pos-.5)*.34,vals,.34,color=col,label=lab);ax.bar_label(b,labels=counts,padding=4)
ax.set_xticks(x,['Clean recovery episodes','Attacked recovery episodes']);ax.set_ylim(0,113);ax.set_ylabel('Native completion (%)');ax.set_yticks([0,25,50,75,100]);ax.legend(loc='upper left',bbox_to_anchor=(0,1.18),ncol=2,frameon=False);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True)
fig.tight_layout();fig.savefig(O/'prefix.png',dpi=240,bbox_inches='tight');fig.savefig(O/'prefix.svg',bbox_inches='tight');plt.close(fig)
print('Created 3 evidence plots and SVG counterparts.')
