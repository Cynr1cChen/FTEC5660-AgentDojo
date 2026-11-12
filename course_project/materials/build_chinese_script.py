"""Chinese study/recording script, matched to the fourteen English slides."""
import json
from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate,Paragraph,Image,Spacer,PageBreak
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[2];B=ROOT/'course_project/runs/materials_agentdojo_20261113'
notes=json.loads((B/'speaker_notes.json').read_text());assert len(notes)==14
pdfmetrics.registerFont(TTFont('ChineseEmbedded','/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
style=ParagraphStyle('cn',fontName='ChineseEmbedded',fontSize=13.2,leading=22.5,spaceAfter=12,textColor=colors.HexColor('#202020'))
title=ParagraphStyle('title',parent=style,fontSize=19,leading=27,spaceAfter=12)
small=ParagraphStyle('small',parent=style,fontSize=10.5,leading=17,textColor=colors.HexColor('#555555'))
titles=['项目研究什么','一个具体的退款例子','实验环境与被测Agent','先检查评分器','正式实验怎样安排','为何调整主要改动','一次有边界的任务复核','正式主结果','同一轨迹中的变化','仍然失败的租金任务','统一日期的补充检验','提升的费用与时间代价','如何复核实验记录','结论与录制准备']
extra={4:'这里的“安全完成”指：用户原任务完成，同时指定攻击目标没有达成。它不是只看Agent有没有说“拒绝”。',
       7:'三次重复中，每组每次有12个攻击条件案例。原版分别完成3、6、4个，复核版分别完成10、10、11个，平均比例为36.11%和86.11%。',
       10:'这是在发现日期问题后另外设计的补充实验：范围固定后才调用API，所有组使用相同日期。它不替换主实验，也不与主实验混合计算。',
       13:'录制准备：补齐姓名学号；练习约10至13分钟；实际Zoom视频必须不超过15分钟。报告、学生GitHub链接和录屏链接是三个提交项目。仓库尚未发布，需你审阅后决定。'}
story=[]
for i,n in enumerate(notes):
 if i:story.append(PageBreak())
 story.append(Paragraph(f'第{i+1}页｜{titles[i]}',title))
 story.append(Paragraph('与英文PPT对应的中文讲解稿；建议结合幻灯片练习。',small))
 image=Image(str(B/f'slide_previews/slide-{i+1:02d}.png'),width=499,height=499*1080/1920)
 story.extend([image,Spacer(1,16),Paragraph(n['chinese'],style)])
 if i in extra:story.append(Paragraph(extra[i],small))
def footer(c,d):
 c.setFont('ChineseEmbedded',9);c.setFillColor(colors.HexColor('#555555'))
 c.drawString(48,29,'FTEC5660｜AgentDojo 中文讲解与录制准备');c.drawRightString(547,29,f'{d.page} / 14')
dest=ROOT/'output/pdf/FTEC5660_AgentDojo_中文讲解稿.pdf'
SimpleDocTemplate(str(dest),pagesize=(595.28,841.89),leftMargin=48,rightMargin=48,topMargin=44,bottomMargin=55,title='AgentDojo 中文讲解稿').build(story,onFirstPage=footer,onLaterPages=footer)
assert len(PdfReader(dest).pages)==14
print(dest)
