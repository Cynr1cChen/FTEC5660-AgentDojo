"""Organize verified local files for Blackboard, without publishing or submitting."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime,timezone
from pathlib import Path

from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
COURSE=ROOT.parent.parent/'Reproducibility.pdf'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--destination',type=Path,default=ROOT.parent.parent/'FTEC5660_Submission')
    args=ap.parse_args();dest=args.destination.resolve()
    # Never replace an identity-filled PDF or a link template edited by the user.
    if dest.exists() and any(dest.iterdir()):
        raise SystemExit('Submission folder already contains files. Use a new --destination to preserve user edits.')
    upload=dest/'01_Blackboard上传文件';aux=dest/'03_录制辅助_无需另交'
    upload.mkdir(parents=True,exist_ok=True);aux.mkdir(parents=True,exist_ok=True)
    accepted=json.loads((HERE/'delivery_validation.json').read_text())
    assert accepted['passed']
    notes=json.loads((HERE/'speaker_notes.json').read_text())
    spoken_words=sum(len(re.findall(r"\b[\w'-]+\b",n['english'])) for n in notes)
    roles={
      'FTEC5660_AgentDojo_Final_Report.pdf':('Required report attachment',upload),
      'FTEC5660_AgentDojo_Final_Presentation.pptx':('Recording aid; not separately required',aux),
      'FTEC5660_AgentDojo_Recording_Script_EN_CN.pdf':('Recording aid; not separately required',aux)}
    files=[]
    for item in accepted['deliverables']:
        src=ROOT/item['path'];assert sha(src)==item['sha256'],src
        role,folder=roles[src.name];target=folder/src.name
        shutil.copy2(src,target);assert sha(src)==sha(target)
        files.append({'file':str(target.relative_to(dest)),'source':str(src),'sha256':sha(target),
                      'bytes':target.stat().st_size,'role':role})
    report=upload/'FTEC5660_AgentDojo_Final_Report.pdf'
    r=PdfReader(report);assert len(r.pages)==10
    fields=r.get_fields();assert set(fields)=={'student_name','student_id'}
    blank_identity=all(not f.get('/V') for f in fields.values())
    assert blank_identity,'Record the filled identity status before packaging a changed report.'
    text_template='''FTEC5660 Individual Reproducibility Project
Reproducing AgentDojo: Task Recovery and Authorization Trade-offs

Name: [FILL IN]
Student ID: [FILL IN]

GitHub repository: [PASTE YOUR STUDENT PROJECT REPOSITORY URL]
Zoom presentation recording: [PASTE THE VIEWABLE RECORDING URL]
Recording access passcode (if required): [ENTER PASSCODE OR N/A]

Report attachment: FTEC5660_AgentDojo_Final_Report.pdf
'''
    (dest/'02_Blackboard提交文本_待填写.txt').write_text(text_template)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    branch=subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    guide=f'''# FTEC5660 提交文件夹

状态：材料已核对并归集，尚未提交。报告和PPT中的姓名、学号仍为空，GitHub与Zoom链接待完成。

## 正式提交范围

课程原始说明第2–3页要求三项：最多10页报告、含自己改动及运行说明的GitHub链接、不超过15分钟的Zoom录制展示链接。

你已确认Blackboard页面有文件区和文本区，对应操作为：

1. **文件区**：上传 `01_Blackboard上传文件/FTEC5660_AgentDojo_Final_Report.pdf`。
2. **文本区**：填写并复制 `02_Blackboard提交文本_待填写.txt` 的内容，提供学生项目GitHub链接与可观看的Zoom录像链接。若录像需要密码，一并提供。
3. 检查附件预览、两个链接和身份信息，再完成Blackboard最终提交并保存回执或提交成功页面。

课程说明没有要求单独上传PPT、讲稿、源码ZIP或整份提交文件夹。PPT与讲稿放在 `03_录制辅助_无需另交/`，用于准备与录制展示。

## 当前文件

- 报告：10页，保留可填写的姓名和学号字段。
- PPT：12页主讲加3页默认隐藏备用，约1.9 MB；封面身份信息待填写。
- 讲稿：12页，英文正文{spoken_words}词，下方中文对照，不含目标时长标签。
- 文本模板：两个链接尚未填写，不能原样当成完成版提交。

归集时逐文件验证哈希，与已验收成品完全一致。`核对记录.json`记录来源、版本及检查范围。

## 还欠缺什么

1. 填写报告首页的姓名、学号，并在录制前补齐PPT封面。
2. 完成学生GitHub仓库发布，保留已有分阶段提交和运行说明，验证教师可以访问。本地origin目前是作者原仓库，不能用它替代含自己改动的学生项目链接。
3. 使用Zoom录制展示，最终视频不超过15分钟，检查音画完整和分享访问权限，填入录像链接及所需密码。
4. 完成Blackboard实际提交并保存回执。

GitHub发布时还需检查提交历史中的凭据。当前跟踪文本及四份研究归档的常见凭据模式检查未发现问题，完整历史检查和公开访问验收在发布时完成。

## 本地代码位置

`{ROOT}`

- 分支：`{branch}`
- 归集前HEAD：`{head}`
- 学生项目入口：`course_project/README.md`
- 当前材料入口：`course_project/materials_v2/README.md`
- 四份可离线核验的研究证据：`course_project/evidence/`

GitHub提交采用项目链接，按课程要求不另附源码ZIP。

## 截止与后续修改

原始课程PDF标注“13 November, midnight”。最终提交时核对Blackboard作业页显示的截止时间。

本文件夹是当前成品快照。你审阅或填写身份后，以最终定稿更新上传目录；保留这里已填写的链接模板，避免被旧副本覆盖。重新归集脚本默认拒绝覆盖已有非空文件夹。

原始要求文件：`{COURSE}`，已逐页核对。
'''
    (dest/'00_提交说明.md').write_text(guide)
    scan_path=HERE/'submission_credential_check.json'
    scan=json.loads(scan_path.read_text())
    assert not scan['issues']
    check={'created_utc':datetime.now(timezone.utc).isoformat(),'status':'materials_organized_submission_pending',
      'platform':'Blackboard; file and text areas confirmed by user',
      'requirement_source':{'path':str(COURSE),'sha256':sha(COURSE),'submission_pages':[2,3],'deadline_page':1},
      'required_items':['Report attachment, at most 10 pages','Student GitHub repository link','Zoom recorded presentation link, at most 15 minutes'],
      'files':files,'report_pages':len(r.pages),'identity_fields_blank':blank_identity,
      'presentation_main_slides':12,'presentation_hidden_backups':3,'script_english_words':spoken_words,
      'repository':{'local_path':str(ROOT),'branch':branch,'head':head,'origin_is_author_repository':True,
                    'student_repository_url':None,'github_connector_account':'Cynr1cChen','repository_search_query':'user:Cynr1cChen agentdojo','agentdojo_repository_search_found':False},
      'credential_scan':scan,'zoom_url':None,'actual_zoom_duration_checked':False,
      'blackboard_submitted':False,'receipt_saved':False,
      'missing':['Name/student ID','Student repository publication/link and access check','Zoom recording/link and access check','Actual Blackboard submission and receipt'],
      'paid_research_calls':0}
    (dest/'核对记录.json').write_text(json.dumps(check,ensure_ascii=False,indent=2)+'\n')
    record={'folder':str(dest),'files':[str(p.relative_to(dest)) for p in dest.rglob('*') if p.is_file()],
            'status':check['status'],'source_head':head,'report_identity_blank':blank_identity,
            'blackboard_submission_performed':False}
    (HERE/'submission_package.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(record,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
