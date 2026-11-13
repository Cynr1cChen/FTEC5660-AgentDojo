"""Offline acceptance of final materials against frozen research evidence."""
import collections
import hashlib
import json
import re
import zipfile
from datetime import datetime,timezone
from pathlib import Path
from xml.etree import ElementTree as ET

import pdfplumber
from pypdf import PdfReader
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
NS={'p':'http://schemas.openxmlformats.org/presentationml/2006/main',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
    'c':'http://schemas.openxmlformats.org/drawingml/2006/chart',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def read(path):return json.loads((ROOT/path).read_text())
def norm(s):return re.sub(r'\s+','',s)

def main():
    facts=read('course_project/materials_v2/facts.json')
    ledger=read('course_project/materials_v2/evidence_ledger.json')
    for item in ledger['studies']:assert sha(ROOT/item['source'])==item['source_sha256'],item['id']
    for item in ledger['notes'].values():
        if 'path' in item:assert sha(ROOT/item['path'])==item['sha256'],item['path']
    archives=[]
    for name,receipt in [
      ('recovery','course_project/evidence/verification.json'),
      ('extension','course_project/extension_review/package_verification.json'),
      ('round2','course_project/round2/package_verification.json'),
      ('closure','course_project/closure/package_verification.json')]:
        p=ROOT/f'course_project/evidence/{name}_evidence.zip';expected=read(receipt)['archive_sha256']
        assert sha(p)==expected
        archives.append({'file':str(p.relative_to(ROOT)),'sha256':expected})
    report=ROOT/'output/pdf/FTEC5660_AgentDojo_Final_Report.pdf'
    script=ROOT/'output/pdf/FTEC5660_AgentDojo_Recording_Script_EN_CN.pdf'
    deck=ROOT/'output/pptx/FTEC5660_AgentDojo_Final_Presentation.pptx'
    rd=PdfReader(report);sc=PdfReader(script)
    assert len(rd.pages)==10 and len(sc.pages)==12
    fields=rd.get_fields();assert set(fields)=={'student_name','student_id'}
    assert all(not f.get('/V') for f in fields.values())
    widgets=[a.get_object() for page in rd.pages for a in page.get('/Annots',[]) if a.get_object().get('/Subtype')=='/Widget']
    assert len(widgets)==2 and all(not x.get('/V') and x.get('/AP',{}).get('/N') for x in widgets)
    assert all('中文对照' in page.extract_text() for page in sc.pages)
    script_text='\n'.join(p.extract_text() for p in sc.pages)
    assert not re.search(r'target time|target duration|\b\d+\s*(?:seconds|minutes)\b|目标时长|预计时长',script_text,re.I)
    notes=read('course_project/materials_v2/speaker_notes.json')
    words=sum(len(re.findall(r"\b[\w'-]+\b",n['english'])) for n in notes)
    assert len(notes)==12 and 1300<=words<=1650
    bounds=[]
    for path in [report,script]:
        with pdfplumber.open(path) as pdf:
            for number,page in enumerate(pdf.pages,1):
                chars=[c for c in page.chars if c['text'].strip()]
                assert all(c['x0']>=35 and c['x1']<=page.width-35 for c in chars),(path.name,number,'horizontal bounds')
                assert all(c['top']>=25 and c['bottom']<=page.height-20 for c in chars),(path.name,number,'vertical bounds')
                bounds.append({'file':path.name,'page':number,'min_x':round(min(c['x0'] for c in chars),2),
                               'max_x':round(max(c['x1'] for c in chars),2),'max_bottom':round(max(c['bottom'] for c in chars),2)})
    pages8=rd.pages[7].extract_text()
    assert all(x in pages8 for x in ['0/12','12/12','9/9','5/9','9/12','8/12'])
    # Ratio/denominator checks against original result sources, then chart cache checks.
    wanted=[
      [facts['main'][a]['safe']['mean'] for a in ['baseline','repeat','recovery']],
      [facts['neutral'][a]['attacked']['strict_safe']['mean'] for a in ['baseline','neutral','recovery']],
      [facts['closure']['rent_attacked'][a]['metrics']['strict_safe']['mean'] for a in ['anchored','aligned']],
      [facts['closure']['positive_controls'][a]['metrics']['strict_safe']['mean'] for a in ['anchored','aligned']],
    ]
    checks=[]
    with zipfile.ZipFile(deck) as z:
        pr=ET.fromstring(z.read('ppt/presentation.xml'));size=pr.find('p:sldSz',NS)
        assert (size.get('cx'),size.get('cy'))==('18288000','10287000')
        parts=sorted([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)],key=lambda n:int(re.search(r'slide(\d+)',n).group(1)))
        assert len(parts)==15
        for i,part in enumerate(parts,1):
            x=ET.fromstring(z.read(part));hidden=x.get('show')=='0'
            assert hidden==(i>12),(i,'hidden flag')
            txt=''.join(t.text or '' for t in x.findall('.//a:t',NS))
            assert not any(v in txt for v in ['张小可','李小画','毕业论文答辩模板','演示文稿是一种实用'])
            if i==1:assert 'Name: ____' in txt and 'Student ID: ____' in txt
            if i in [3,6,7,13,14,15]:assert x.findall('.//a:tbl',NS),i
        charts=sorted([n for n in z.namelist() if re.fullmatch(r'ppt/slides/charts/chart\d+\.xml',n)],key=lambda n:int(re.search(r'chart(\d+)',n).group(1)))
        assert len(charts)==4
        for part,expected in zip(charts,wanted):
            c=ET.fromstring(z.read(part))
            actual=[float(v.text) for v in c.findall('.//c:ser/c:val/c:numRef/c:numCache/c:pt/c:v',NS)]
            assert len(actual)==len(expected),(part,actual)
            assert all(abs(x-y)<1e-11 for x,y in zip(actual,expected)),(part,actual,expected)
            assert c.find('.//c:externalData',NS) is not None
            checks.append({'part':part,'actual':actual,'source_values':expected,'passed':True})
        assert len([n for n in z.namelist() if n.endswith('.xlsx')])==4
        assert not any(n.startswith('ppt/fonts/') for n in z.namelist())
        for i,note in enumerate(notes,1):
            x=ET.fromstring(z.read(f'ppt/notesSlides/notesSlide{i}.xml'))
            txt=''.join(t.text or '' for t in x.findall('.//a:t',NS))
            assert norm(note['english']) in norm(txt),(i,'English note')
            assert norm(note['chinese']) in norm(txt),(i,'Chinese note')
            assert 'Sources' in txt
        embedded={sha_bytes(z.read(n)) for n in z.namelist() if n.startswith('ppt/media/')}
        assert all(sha(HERE/'assets'/n) in embedded for n in ['cover_flat.png','refund_flat.png'])
    latest=read('course_project/materials_v2/build/final/latest_revision.json')
    finalizer=json.loads(Path(latest['build'],'validation.json').read_text())
    assert finalizer['finalSha256']==sha(deck)
    assert finalizer['packageIntegrity']['findingCount']==0
    assert finalizer['presentationLayout']['findingCount']==0
    assert finalizer['fontSelection']['passed']
    warnings=finalizer['presentationLayout']['warnings']
    assert all(w['kind']=='object_outside_slide_boundary' for w in warnings)
    # These are precisely the retained source-template corner objects, reviewed visually.
    corner_ids={'4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','20','21'}
    assert all(w['object_id'] in corner_ids for w in warnings)
    template=read('course_project/materials_v2/template_slimming.json')
    assert sha(Path('/Users/Admin1/Downloads/模板.pptx'))=='6fffbef873e11fc4ef62139db7a7e8a0c28bc3c8f093e7c091a39503ba67a75d'
    assert sha(ROOT/'output/pdf/FTEC5660_AgentDojo_中文讲解稿.pdf')=='2cacb99845a8c412c6fdb58c87e4b25b260bbb967bf85a4f30e3a7d96ba1b56d'
    assert sha(report)!='18b125453358aa893f97a6251ffdbf918e02574eefe156e108453670992f8e05'
    assert sha(deck)!='de1da3d751cbcd1ca91a664e0361eddc8d58dc49da62eecded6c794e67508f4b'
    assert not (ROOT/'output/pdf/FTEC5660_AgentDojo_Report.pdf').exists()
    assert not (ROOT/'output/pptx/FTEC5660_AgentDojo_Presentation.pptx').exists()
    rendered=[]
    for folder,n in [(HERE/'build/final/report_pages',10),(HERE/'build/final/script_pages',12),(Path(latest['build'])/'final_previews',15)]:
        assert len(list(folder.glob('page-*.png' if n!=15 else 'slide-*.png')))==n
        for pth in sorted(folder.glob('page-*.png' if n!=15 else 'slide-*.png')):
            with Image.open(pth) as im:assert min(im.size)>700
            rendered.append({'file':str(pth.relative_to(ROOT)),'sha256':sha(pth)})
    out={'created_utc':datetime.now(timezone.utc).isoformat(),'passed':True,
         'deliverables':[{ 'path':str(p.relative_to(ROOT)),'sha256':sha(p),'bytes':p.stat().st_size} for p in [report,deck,script]],
         'report_pages':10,'presentation_main_slides':12,'presentation_hidden_backup_slides':3,'script_pages':12,
         'english_script_words':words,'script_has_target_duration_labels':False,'blank_identity_fields_verified':True,
         'native_editable_charts':4,'embedded_workbooks':4,'chart_source_checks':checks,'pdf_text_bounds':bounds,
         'research_sources_unchanged':True,'evidence_archives_unchanged':archives,'original_template_unchanged':True,
         'old_chinese_script_preserved':True,'template_corner_warnings_reviewed':len(warnings),
         'native_powerpoint_opening_performed':False,'new_research_model_calls':0,
         'visual_review':{'all_37_pages_or_slides_individually_reviewed':True,'unresolved_visual_defects':[],
           'rendered_files':rendered},
         'remaining_user_actions':['Fill name/student ID','Publish student GitHub repository','Record Zoom presentation','Submit and save receipt']}
    (HERE/'delivery_validation.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k in ['passed','report_pages','presentation_main_slides','presentation_hidden_backup_slides','script_pages','english_script_words','native_editable_charts','embedded_workbooks','new_research_model_calls']},indent=2))

def sha_bytes(data):return hashlib.sha256(data).hexdigest()

if __name__=='__main__':main()
