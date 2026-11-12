"""Check delivered document dimensions and chart/source agreement, without API calls."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
read = lambda p: json.loads((ROOT / p).read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
F = read('course_project/formal/results.json')
D = read('course_project/date_followup/results.json')
arms = ['baseline', 'repeat', 'recovery']
expected = [
    [[F['arms'][a]['metrics'][k]['mean'] * 100 for a in arms]
     for k in ['clean_utility', 'attacked_safe_completion']],
    [[13/18*100, 14/36*100], [100, 31/36*100]],
    [[D['arms'][a]['metrics']['attacked_safe_completion']['mean'] * 100 for a in arms]],
]
ns = {'c': 'http://schemas.openxmlformats.org/drawingml/2006/chart'}
ppt = ROOT / 'output/pptx/FTEC5660_AgentDojo_Presentation.pptx'
with ZipFile(ppt) as z:
    slides = [n for n in z.namelist() if n.startswith('ppt/slides/slide') and n.endswith('.xml')]
    notes = [n for n in z.namelist() if n.startswith('ppt/notesSlides/notesSlide') and n.endswith('.xml')]
    charts = sorted(n for n in z.namelist() if '/charts/chart' in n and n.endswith('.xml'))
    workbooks = [n for n in z.namelist() if n.startswith('ppt/embeddings/') and n.endswith('.xlsx')]
    assert len(slides) == len(notes) == 14 and len(charts) == len(workbooks) == 3
    for name, exp in zip(charts, expected):
        root = ET.fromstring(z.read(name))
        got = [[float(v.text) for v in s.findall('.//c:val/c:numRef/c:numCache/c:pt/c:v', ns)]
               for s in root.findall('.//c:ser', ns)]
        assert len(got) == len(exp)
        for a, b in zip(got, exp):
            assert len(a) == len(b) and all(abs(x-y) < 1e-8 for x, y in zip(a, b))
report = ROOT / 'output/pdf/FTEC5660_AgentDojo_Report.pdf'
script = ROOT / 'output/pdf/FTEC5660_AgentDojo_中文讲解稿.pdf'
r = PdfReader(report)
assert len(r.pages) == 10 and len(PdfReader(script).pages) == 14
fields = r.get_fields()
assert set(fields) == {'student_name', 'student_id'}
assert all(f.get('/V', '') == '' for f in fields.values())
receipt = dict(
    passed=True, report_pages=10, slides=14, script_pages=14,
    chart_data_agrees_with_recorded_results=True, native_charts=3,
    embedded_chart_workbooks=3, speaker_notes_slides=14,
    blank_identity_fields=True, native_powerpoint_opening_verified=False,
    artifacts={str(p.relative_to(ROOT)): dict(bytes=p.stat().st_size, sha256=sha(p))
               for p in [report, ppt, script]},
    research_sources={p: sha(ROOT/p) for p in [
        'course_project/formal/results.json',
        'course_project/date_followup/results.json',
        'course_project/formal/recovery_diagnosis.json',
        'course_project/evidence/verification.json']},
    pending=['Student review and identity fields', 'GitHub publication',
             'Actual Zoom recording and accessible link', 'Blackboard submission'],
)
(ROOT/'course_project/materials/delivery_validation.json').write_text(
    json.dumps(receipt, indent=2, ensure_ascii=False)+'\n')
print(json.dumps(receipt, indent=2, ensure_ascii=False))
