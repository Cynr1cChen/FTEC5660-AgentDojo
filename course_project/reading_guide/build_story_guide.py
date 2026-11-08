"""Render the narrative PDF revision locally; no API calls or credentials."""
import hashlib
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Preformatted, Spacer, Table, TableStyle

import build_guide as layout
from story_content import PAGES

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "course_project/output/pdf/AgentDojo_通俗讲解修订版.pdf"
TMP = ROOT / "course_project/tmp/pdfs/story_guide"
TITLE = "跟着一位银行助理读懂 AgentDojo"


def para(value, size=12.0, leading=21.0, color=layout.INK):
    return Paragraph(layout.markup(value), layout.style(size, leading, color))


class StoryDiagram(layout.Diagram):
    def drawOn(self, c, x, y):
        if self.kind not in {"layers", "clean_story", "lab_parts", "execution_gate"}:
            return super().drawOn(c, x, y)
        c.saveState()
        c.translate(x, y)
        if self.kind == "layers":
            rows = [("原论文", "实验报告：问题、方法、结果与边界", layout.BLUE),
                    ("官方仓库", "实验设备：环境、工具、任务、运行与判分", layout.TEAL),
                    ("我们的课程工作", "在设备上开展：复现、一次修改、对照分析", layout.BLUE)]
            for i, (title, subtitle, color) in enumerate(rows):
                yy = 112-i*50
                self.blocks(c, [(0, yy, 499, 35, title, subtitle, color)])
                if i < 2:
                    self.arrow(c, 249, yy-1, 249, yy-10, layout.TEAL)
        elif self.kind == "clean_story":
            rows = [("1  用户交代任务", "读通知，更新地址"),
                    ("2  AI 提出读取请求", "read_file → 文件文本"),
                    ("3  AI 提出更新请求", "update_user_info → 新街道、新城市"),
                    ("4  程序保存变化", "检查账户状态，再向用户说明结果")]
            for i, (title, sub) in enumerate(rows):
                yy = 132-i*42
                self.blocks(c, [(0, yy, 499, 35, title, sub, layout.BLUE if i<3 else layout.TEAL)])
                if i<3:
                    self.arrow(c, 249, yy-1, 249, yy-6, layout.TEAL)
        elif self.kind == "lab_parts":
            blocks = [(0, 100, 149, 51, "准备业务", "环境、工具、用户要求", layout.BLUE),
                      (175, 100, 149, 51, "加入干扰", "允许的位置、目标、文字", layout.RED),
                      (350, 100, 149, 51, "让助理实际执行", "保存消息、调用与结果", layout.TEAL)]
            self.blocks(c, blocks)
            self.arrow(c, 152, 126, 171, 126, layout.BLUE)
            self.arrow(c, 327, 126, 346, 126, layout.RED)
            self.blocks(c, [(175, 15, 324, 52, "两组检查", "业务是否完成？攻击者目标是否达成？", layout.BLUE)])
            self.arrow(c, 425, 96, 425, 72, layout.TEAL)
            self.label(c, 0, 45, "同一实验条件下", 10, layout.MUTED)
            self.label(c, 0, 25, "比较多个模型或防御", 10, layout.MUTED)
        elif self.kind == "execution_gate":
            self.blocks(c, [(0, 83, 143, 59, "模型提出操作", "工具名 + 具体参数", layout.BLUE),
                            (178, 83, 143, 59, "候选一致性检查", "用户目的 + 可见证据", layout.TEAL),
                            (356, 83, 143, 59, "实际工具执行", "允许后才改变状态", layout.BLUE)])
            self.arrow(c, 146, 113, 174, 113, layout.BLUE)
            self.arrow(c, 324, 113, 352, 113, layout.TEAL)
            self.label(c, 179, 57, "拒绝：说明原因，交回助理继续处理", 9.3, layout.RED)
            self.label(c, 0, 20, "这是尚待实现和验证的课程候选设计，不是已经生效的新防御。", 9.2, layout.RED)
        c.restoreState()


ORIGINAL_ITEM = layout.item_flowables


def item_flowables(item):
    kind, value = item[0], item[1]
    if kind == "say":
        label, text = value, item[2]
        tone = item[3] if len(item)>3 else "blue"
        accent = {"blue":layout.BLUE,"teal":layout.TEAL,"red":layout.RED}[tone]
        content = [[para(label, 9.3, 14.0, accent)], [para(text, 11.6, 20.0, layout.INK)]]
        t = Table(content, colWidths=[layout.CONTENT_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),layout.PALE),
            ("LINEBEFORE",(0,0),(0,-1),3,accent),
            ("LEFTPADDING",(0,0),(-1,-1),13),
            ("RIGHTPADDING",(0,0),(-1,-1),13),
            ("TOPPADDING",(0,0),(-1,0),8),
            ("BOTTOMPADDING",(0,0),(-1,0),1),
            ("TOPPADDING",(0,1),(-1,1),3),
            ("BOTTOMPADDING",(0,1),(-1,1),10),
        ]))
        return [t, Spacer(1,11)]
    if kind == "diagram":
        return [StoryDiagram(value,item[2] if len(item)>2 else 150),Spacer(1,10)]
    if kind == "code":
        return [Preformatted(value,layout.style(9.5,14.5,layout.INK),maxLineLength=100),Spacer(1,10)]
    if kind == "h":
        return [Spacer(1,4),para(value,13.2,21.0,layout.BLUE)]
    return ORIGINAL_ITEM(item)


def cover(c, page):
    W,H=layout.W,layout.H
    c.setFillColor(layout.INK)
    c.rect(0,H-317,W,317,stroke=0,fill=1)
    c.setFillColor(colors.HexColor("#92dbcb"))
    c.setFont("Guide",11)
    c.drawString(48,H-54,"FTEC5660  /  通俗讲解修订版  /  2026-11-08")
    c.setFillColor(colors.white)
    c.setFont("Guide",31)
    c.drawString(48,H-111,"跟着一位银行助理")
    c.drawString(48,H-155,"读懂 AgentDojo")
    c.setFont("Guide",13)
    c.drawString(48,H-202,"先看事情怎样发生，再理解论文与代码")
    c.setFont("Guide",10.5)
    c.setFillColor(colors.HexColor("#c5dce8"))
    c.drawString(48,H-256,"完整故事 · 逐步图解 · 真实案例 · 实验设计 · 源码导读")
    y=486
    for item in page["items"]:
        for flow in item_flowables(item):
            _,h=flow.wrap(layout.CONTENT_W,H)
            y-=h
            flow.drawOn(c,48,y)
            y-=11
    if y<85:
        raise RuntimeError(f"Cover is overfull: {y}")
    c.setFillColor(layout.MUTED)
    c.setFont("Guide",8.6)
    c.drawString(48,47,"依据：NeurIPS 2024 正式论文、固定上游代码与已保存的本地开发日志。")
    c.drawString(48,31,"这是阅读说明；教学假设与真实结果分别标注。制作过程没有新调用模型 API。")
    c.drawRightString(W-48,31,"01")


def export_markdown():
    lines=[f"# {TITLE}","", "通俗讲解修订版，2026-11-08。页码对应 PDF。", ""]
    for i,p in enumerate(PAGES,1):
        lines.extend([f"## 第 {i} 页 · {p['title']}","",p['part']+"："+p['subtitle'],""])
        for item in p['items']:
            kind,value=item[0],item[1]
            if kind in {"p","box"}: lines.extend([value,""])
            elif kind=="h": lines.extend([f"### {value}",""])
            elif kind=="say": lines.extend([f"**{value}**", "", "> "+item[2],""])
            elif kind=="code": lines.extend(["```python",value,"```",""])
            elif kind=="table":
                lines.append("| "+" | ".join(value[0])+" |")
                lines.append("| "+" | ".join("---" for _ in value[0])+" |")
                for row in value[1:]:lines.append("| "+" | ".join(row)+" |")
                lines.append("")
            elif kind=="image":lines.extend([f"![真实日志摘录重排](../../{value})",""])
            elif kind=="diagram":lines.extend([f"[矢量图：{value}，见 PDF]",""])
            elif kind=="links":lines.extend([f"- [{label}]({url})" for label,url in value if not url.startswith("#")]+[""])
        if p['refs']:
            lines.extend(["依据："+" · ".join(f"[{k} {layout.SOURCES[k][0]}]({layout.SOURCES[k][1]})" for k in p['refs']),""])
    (Path(__file__).parent/"AgentDojo_通俗讲解修订版.md").write_text("\n".join(lines).rstrip()+"\n")


def main():
    OUT.parent.mkdir(parents=True,exist_ok=True)
    TMP.mkdir(parents=True,exist_ok=True)
    layout.para=para
    layout.item_flowables=item_flowables
    layout.cover=cover
    c=canvas.Canvas(str(OUT),pagesize=(layout.W,layout.H),pageCompression=1)
    c.setTitle(TITLE+"：论文与仓库通俗讲解修订版")
    c.setAuthor("课程项目中文阅读说明；原研究作者见来源页")
    c.setSubject("从具体银行任务理解 AgentDojo 原论文、官方实现和课程复现")
    c.setKeywords("AgentDojo, FTEC5660, 中文, 提示注入, 论文导读, 仓库导读")
    for i,p in enumerate(PAGES,1):
        layout.draw_page(c,p,i)
        c.showPage()
    c.save()
    export_markdown()
    report={"pdf":str(OUT.relative_to(ROOT)),"pages":len(PAGES),"bytes":OUT.stat().st_size,
            "sha256":hashlib.sha256(OUT.read_bytes()).hexdigest(),
            "topics":[dict(page=i,title=p['title']) for i,p in enumerate(PAGES,1)]}
    (TMP/"build_manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="topics"},ensure_ascii=False))


if __name__=="__main__":
    main()
