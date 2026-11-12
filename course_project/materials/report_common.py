from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import *
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/"course_project/runs/materials_agentdojo_20261113"
F=Path('/System/Library/Fonts/Supplemental')
for name,file in [('Body','Arial.ttf'),('Bold','Arial Bold.ttf'),('Italic','Arial Italic.ttf')]:pdfmetrics.registerFont(TTFont(name,str(F/file)))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='Bold',italic='Italic',boldItalic='Bold')
INK=colors.HexColor('#202020');GRAY=colors.HexColor('#555555');LINE=colors.HexColor('#D2D2D2');W=499.28
ST={
 'body':ParagraphStyle('body',fontName='Body',fontSize=10.4,leading=14.5,textColor=INK,spaceAfter=8),
 'small':ParagraphStyle('small',fontName='Body',fontSize=8.5,leading=11.4,textColor=GRAY,spaceAfter=6),
 'h1':ParagraphStyle('h1',fontName='Bold',fontSize=21,leading=25,textColor=INK,spaceAfter=14),
 'h2':ParagraphStyle('h2',fontName='Bold',fontSize=12,leading=16,textColor=INK,spaceBefore=6,spaceAfter=7),
 'title':ParagraphStyle('title',fontName='Bold',fontSize=28,leading=33,textColor=INK,spaceAfter=12),
 'subtitle':ParagraphStyle('subtitle',fontName='Body',fontSize=13,leading=18,textColor=GRAY,spaceAfter=14),
 'code':ParagraphStyle('code',fontName='Body',fontSize=8.2,leading=12,textColor=INK,spaceAfter=5),
}
def P(s,style='body'):return Paragraph(str(s),ST[style])
def H(s):return P(s,'h2')
def table(rows,widths=None,size=9.1):
 cell=ParagraphStyle('cell',parent=ST['body'],fontSize=size,leading=size+3,spaceAfter=0)
 head=ParagraphStyle('head',parent=cell,fontName='Bold')
 t=Table([[Paragraph(escape(str(x)).replace('\n','<br/>'),head if i==0 else cell) for x in row] for i,row in enumerate(rows)],colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EEEEEE')),('LINEBELOW',(0,0),(-1,0),.7,GRAY),('LINEBELOW',(0,-1),(-1,-1),.5,LINE),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
 return t
def fig(name,height):
 im=Image(str(HERE/'assets'/name));scale=min(W/im.imageWidth,height/im.imageHeight);im.drawWidth=im.imageWidth*scale;im.drawHeight=im.imageHeight*scale;return im
class Identity(Flowable):
 def __init__(self):super().__init__();self.width=W;self.height=30
 def draw(self):
  c=self.canv;c.setFont('Body',9);c.setFillColor(GRAY)
  c.drawString(0,14,'Name:');c.drawString(262,14,'Student ID:')
  for n,x,w in [('student_name',34,202),('student_id',322,174)]:c.acroForm.textfield(name=n,tooltip=n,x=x,y=8,relative=True,width=w,height=19,borderStyle='underlined',borderColor=LINE,fillColor=colors.white,textColor=INK,fontName='Helvetica',fontSize=10,value='')
def footer(c,doc):
 c.saveState();c.setStrokeColor(LINE);c.setLineWidth(.45);c.line(48,43,547,43);c.setFont('Body',8);c.setFillColor(GRAY)
 c.drawString(48,29,'FTEC5660  /  AgentDojo reproducibility study');c.drawRightString(547,29,f'{doc.page} / 10');c.restoreState()
def page(title,items):return [P(title,'h1'),*items]
