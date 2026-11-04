"""Build a Chinese reading guide from reviewed content and real local evidence.

Rendering only: no model requests, credentials, or paid services are used.
"""
import hashlib
import json
import math
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle, Image, Spacer, Preformatted

from guide_content import PAGES, SOURCES

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "course_project/output/pdf/AgentDojo_论文与仓库详解.pdf"
TMP = ROOT / "course_project/tmp/pdfs/reading_guide"
W, H = 595.276, 841.89
MARGIN, CONTENT_W = 48, W - 96
INK = colors.HexColor("#193047")
BLUE = colors.HexColor("#245b94")
TEAL = colors.HexColor("#15766e")
MUTED = colors.HexColor("#586c7e")
PALE = colors.HexColor("#edf3f8")
RED = colors.HexColor("#aa493b")

FONT_PATH = "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
pdfmetrics.registerFont(TTFont("Guide", FONT_PATH))
pdfmetrics.registerFontFamily("Guide", normal="Guide", bold="Guide", italic="Guide", boldItalic="Guide")


def style(size=10.6, leading=17.0, color=INK, **kwargs):
    return ParagraphStyle("guide", fontName="Guide", fontSize=size, leading=leading,
                          textColor=color, wordWrap="CJK", spaceAfter=7, **kwargs)


def markup(value):
    value = value.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    value = escape(value)
    value = re.sub(r"\*\*(.*?)\*\*", r'<font color="#245b94">\1</font>', value)
    return value.replace("\n", "<br/>")


def para(value, size=10.6, leading=17.0, color=INK):
    return Paragraph(markup(value), style(size, leading, color))


def table(rows, widths=None, size=9.0):
    widths = [CONTENT_W / len(rows[0])] * len(rows[0]) if widths is None else [CONTENT_W*x for x in widths]
    data = [[para(str(cell), size, size*1.53, colors.white if i == 0 else INK)
             for cell in row] for i, row in enumerate(rows)]
    t = Table(data, colWidths=widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, BLUE),
        ("LINEBELOW", (0, -1), (-1, -1), 0.4, colors.HexColor("#ccd9e3")),
    ]))
    return t


def box(value, tone="blue"):
    accent = {"blue": BLUE, "teal": TEAL, "red": RED}[tone]
    t = Table([[para(value, 10.3, 16.5, accent)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("LINEBEFORE", (0, 0), (0, 0), 3, accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


class Diagram:
    def __init__(self, kind, height=150):
        self.kind, self.height = kind, height
    def wrap(self, width, height):
        return width, self.height
    def drawOn(self, c, x, y):
        c.saveState()
        c.translate(x, y)
        if self.kind == "overview":
            blocks = [(0, 70, 105, 57, "用户任务", "可信的任务要求", BLUE),
                      (183, 70, 118, 57, "工具调用 Agent", "LLM + 执行循环", BLUE),
                      (379, 70, 120, 57, "模拟环境", "文件、账户、交易", TEAL)]
            self.blocks(c, blocks)
            self.arrow(c, 109, 98, 179, 98, BLUE)
            self.arrow(c, 305, 110, 375, 110, BLUE)
            self.arrow(c, 375, 86, 305, 86, TEAL)
            self.label(c, 315, 126, "工具调用", 8)
            self.label(c, 313, 68, "工具返回内容", 8)
            self.blocks(c, [(369, 0, 130, 43, "攻击者", "改写指定外部内容", RED)])
            self.arrow(c, 408, 47, 355, 79, RED)
            self.label(c, 0, 31, "研究者从环境状态和日志中分别判定：", 9)
            self.label(c, 0, 12, "用户任务是否完成？攻击目标是否达成？", 10, BLUE)
        elif self.kind == "pipeline":
            names = [("SystemMessage", "系统说明"), ("InitQuery", "用户任务"), ("LLM", "提出调用"),
                     ("ToolsExecutor", "执行工具"), ("LLM", "读取返回并继续")]
            for i, (a, b) in enumerate(names):
                xx = i * 101
                self.blocks(c, [(xx, 66, 94, 63, a, b, BLUE if i != 3 else TEAL)])
                if i < 4:
                    self.arrow(c, xx+95, 98, xx+100, 98, BLUE)
            c.setStrokeColor(TEAL)
            c.lines([(447, 62, 447, 33), (447, 33, 248, 33), (248, 33, 248, 62)])
            self.arrow(c, 248, 33, 248, 62, TEAL)
            self.label(c, 262, 42, "还有工具调用就继续循环", 9, TEAL)
            self.label(c, 0, 5, "循环停止：模型不再提出调用，或达到轮数限制。", 9)
        elif self.kind == "injection":
            self.blocks(c, [(0, 78, 143, 65, "环境模板", "合法内容 + 插入位置", BLUE),
                            (179, 78, 143, 65, "攻击生成器", "根据目标生成注入文本", RED),
                            (357, 78, 142, 65, "被读取的工具输出", "原有数据 + 攻击指令", TEAL)])
            self.arrow(c, 146, 110, 175, 110, BLUE)
            self.arrow(c, 325, 110, 353, 110, RED)
            self.label(c, 0, 45, "例：地址变更通知中有一个额外文字插槽。", 10)
            self.label(c, 0, 25, "攻击者能改插槽，不能因此直接改成真正的 system 角色。", 10)
            self.label(c, 0, 5, "如果插槽覆盖整张账单，合法任务信息也可能一并丢失。", 9, RED)
        elif self.kind == "defense":
            self.blocks(c, [(0, 73, 139, 65, "工具暴露之前", "Tool filter 预选工具", BLUE),
                            (179, 73, 141, 65, "工具返回之后", "检测、分隔、重复任务", TEAL),
                            (360, 73, 139, 65, "下一次模型决策", "是否继续合法任务", BLUE)])
            self.arrow(c, 142, 106, 175, 106, BLUE)
            self.arrow(c, 323, 106, 356, 106, TEAL)
            self.label(c, 0, 40, "过滤工具限制“能做什么”；处理返回内容影响“相信什么”。", 10)
            self.label(c, 0, 18, "同一个工具既可完成合法操作，也可能执行攻击操作。", 10, RED)
        elif self.kind == "grading":
            self.blocks(c, [(0, 73, 142, 64, "运行前状态", "账户、交易、文件", BLUE),
                            (178, 73, 143, 64, "执行轨迹", "工具调用与最终回答", TEAL),
                            (357, 73, 142, 64, "运行后状态", "哪些数据被改变？", BLUE)])
            self.arrow(c, 145, 105, 174, 105, BLUE)
            self.arrow(c, 324, 105, 353, 105, BLUE)
            self.label(c, 0, 40, "utility(...) 判用户任务；security(...) 判攻击目标。", 10)
            self.label(c, 0, 18, "某些任务还会通过 *_from_traces 检查曾经发生的动作。", 10)
        elif self.kind == "results":
            labels = ["无新增防御", "内容分隔", "注入检测器", "重复用户任务", "预选工具"]
            utility = [69.0, 72.66, 41.49, 85.53, 73.13]
            asr = [57.69, 41.65, 7.95, 27.82, 6.84]
            x0, full, y0 = 95, 300, 156
            for i, label in enumerate(labels):
                yy = y0 - i*31
                self.label(c, 0, yy+3, label, 9)
                for value, offset, col in [(utility[i], 9, BLUE), (asr[i], -3, RED)]:
                    c.setFillColor(col)
                    c.rect(x0, yy+offset, full*value/100, 9, fill=1, stroke=0)
                    self.label(c, x0+full*value/100+5, yy+offset-1, f"{value:.2f}%", 8, col)
            self.label(c, 95, 7, "蓝：正常任务效用，越高越好", 8.5, BLUE)
            self.label(c, 291, 7, "红：目标攻击成功率，越低越好", 8.5, RED)
        elif self.kind == "callchain":
            entries = [("scripts/benchmark.py", "解析配置、选择场景"),
                       ("benchmark.py", "枚举任务与攻击组合"),
                       ("TaskSuite.run_task_with_pipeline", "构造环境并运行 Agent"),
                       ("AgentPipeline + FunctionsRuntime", "模型决策与真实 Python 工具执行"),
                       ("utility / security + TraceLogger", "判定结果并保存日志")]
            for i, (a, b) in enumerate(entries):
                yy = 180-i*38
                self.blocks(c, [(0, yy, 499, 31, a, b, BLUE)])
                if i < 4:
                    self.arrow(c, 249, yy-1, 249, yy-6, BLUE)
        c.restoreState()

    @staticmethod
    def label(c, x, y, value, size=9, color=MUTED):
        c.setFont("Guide", size)
        c.setFillColor(color)
        c.drawString(x, y, value)

    @staticmethod
    def blocks(c, blocks):
        for x, y, w, h, title, subtitle, col in blocks:
            c.setFillColor(PALE)
            c.setStrokeColor(colors.HexColor("#d1dfe9"))
            c.roundRect(x, y, w, h, 7, fill=1, stroke=1)
            c.setFillColor(col)
            title_size = 9 if len(title) > 16 else 11
            c.setFont("Guide", title_size)
            if h <= 35:
                c.drawString(x+10, y+11, title)
                c.setFont("Guide", 8.5)
                c.setFillColor(MUTED)
                c.drawRightString(x+w-10, y+11, subtitle)
            else:
                c.drawCentredString(x+w/2, y+h-22, title)
                c.setFont("Guide", 8.5)
                c.setFillColor(MUTED)
                c.drawCentredString(x+w/2, y+12, subtitle)

    @staticmethod
    def arrow(c, x1, y1, x2, y2, color):
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(1)
        c.line(x1, y1, x2, y2)
        angle = math.atan2(y2-y1, x2-x1)
        p = c.beginPath()
        p.moveTo(x2, y2)
        p.lineTo(x2-5*math.cos(angle-.45), y2-5*math.sin(angle-.45))
        p.lineTo(x2-5*math.cos(angle+.45), y2-5*math.sin(angle+.45))
        p.close()
        c.drawPath(p, stroke=0, fill=1)


def item_flowables(item):
    kind, value = item[0], item[1]
    if kind == "p":
        return [para(value)]
    if kind == "h":
        return [Spacer(1, 4), para(value, 12.3, 19, BLUE)]
    if kind == "box":
        return [box(value, item[2] if len(item)>2 else "blue"), Spacer(1, 9)]
    if kind == "table":
        return [table(value, item[2] if len(item)>2 else None, item[3] if len(item)>3 else 9), Spacer(1, 10)]
    if kind == "diagram":
        return [Diagram(value, item[2] if len(item)>2 else 150), Spacer(1, 9)]
    if kind == "code":
        return [Preformatted(value, style(8.0, 11.7, INK), maxLineLength=100), Spacer(1, 9)]
    if kind == "image":
        return [Image(str(ROOT / value), width=CONTENT_W, height=CONTENT_W*9/16), Spacer(1, 10)]
    if kind == "links":
        return [Paragraph("<br/>".join(
            f'<link href="{escape(url, {chr(34): "&quot;"})}" color="#245b94">{escape(label)}</link>'
            for label, url in value), style(9.1, 15.1)), Spacer(1, 8)]
    raise ValueError(kind)


def draw_page(c, page, number):
    c.bookmarkPage(f"page_{number}")
    c.addOutlineEntry(f"{number:02d}  {page['title']}", f"page_{number}", 0)
    if number == 1:
        cover(c, page)
        return
    c.setFillColor(PALE)
    c.rect(0, H-117, W, 117, fill=1, stroke=0)
    c.setFont("Guide", 8.6)
    c.setFillColor(TEAL)
    c.drawString(MARGIN, H-30, page["part"])
    c.setFont("Guide", 22)
    c.setFillColor(INK)
    c.drawString(MARGIN, H-64, page["title"])
    subtitle = Paragraph(markup(page["subtitle"]), style(9.7, 15.2, MUTED))
    _, sh = subtitle.wrap(CONTENT_W, 40)
    subtitle.drawOn(c, MARGIN, H-77-sh)
    y = H - 138
    elements = [flow for item in page["items"] for flow in item_flowables(item)]
    measured = []
    for flow in elements:
        _, height = flow.wrap(CONTENT_W, H)
        measured.append((flow, height))
    total = sum(height + (7 if isinstance(flow, Paragraph) else getattr(flow, "spaceAfter", 0))
                for flow, height in measured)
    if total > y-68:
        raise RuntimeError(f"Page {number} is overfull by {total-(y-68):.1f} pt: {page['title']}")
    for flow, height in measured:
        y -= height
        flow.drawOn(c, MARGIN, y)
        y -= getattr(flow, "spaceAfter", 0) if not isinstance(flow, Paragraph) else 7
    if y < 66:
        raise RuntimeError(f"Page {number} footer collision, y={y:.1f}")
    footer(c, page, number)


def footer(c, page, number):
    c.setStrokeColor(colors.HexColor("#d6e1e9"))
    c.line(MARGIN, 53, W-MARGIN, 53)
    refs = page.get("refs", [])
    if refs:
        content = "依据：" + "  ·  ".join(
            f'<link href="{SOURCES[key][1]}" color="#245b94">[{key}] {SOURCES[key][0]}</link>' for key in refs)
        pp = Paragraph(content, style(7.3, 9.8, MUTED))
        _, hh = pp.wrap(CONTENT_W-37, 24)
        pp.drawOn(c, MARGIN, 40-hh)
    c.setFont("Guide", 8.5)
    c.setFillColor(MUTED)
    c.drawRightString(W-MARGIN, 24, f"{number:02d}")


def cover(c, page):
    c.setFillColor(INK)
    c.rect(0, H-335, W, 335, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#84d5c6"))
    c.setFont("Guide", 11)
    c.drawString(MARGIN, H-60, "FTEC5660  /  阅读与理解材料  /  2026-11-04")
    c.setFillColor(colors.white)
    c.setFont("Guide", 36)
    c.drawString(MARGIN, H-127, "AgentDojo")
    c.setFont("Guide", 27)
    c.drawString(MARGIN, H-176, "论文与原仓库详解")
    c.setFont("Guide", 12)
    c.drawString(MARGIN, H-224, "从研究问题到一次真实执行，再到可验证的课程实验")
    c.setFillColor(colors.HexColor("#c8dce9"))
    c.setFont("Guide", 10.5)
    c.drawString(MARGIN, H-275, "分开理解：论文结论 · 官方实现 · 我们的适配与试跑")
    y = 458
    for item in page["items"]:
        for flow in item_flowables(item):
            _, hh = flow.wrap(CONTENT_W, H)
            y -= hh
            flow.drawOn(c, MARGIN, y)
            y -= 11
    c.setFont("Guide", 9)
    c.setFillColor(MUTED)
    c.drawString(MARGIN, 48, "本文是独立中文讲解，不是论文逐句翻译，也不是课程最终报告。")
    c.drawString(MARGIN, 31, "原作者与来源见文末；图示由讲解重新绘制，实际日志另行标记。")
    c.drawRightString(W-MARGIN, 31, "01")


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    TMP.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
    c.setTitle("AgentDojo 论文与原仓库详解")
    c.setAuthor("课程项目阅读说明；原研究作者见来源页")
    c.setSubject("AgentDojo 原论文、官方仓库和课程复现的中文阅读指南")
    c.setKeywords("AgentDojo, FTEC5660, prompt injection, reproducibility, 中文")
    for index, page in enumerate(PAGES, 1):
        draw_page(c, page, index)
        c.showPage()
    c.save()
    manifest = {"pdf": str(OUT.relative_to(ROOT)), "pages": len(PAGES),
                "sha256": hashlib.sha256(OUT.read_bytes()).hexdigest(),
                "topics": [{"page": i, "title": p["title"]} for i,p in enumerate(PAGES,1)]}
    (TMP / "build_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    print(json.dumps({"pdf": str(OUT), "pages": len(PAGES), "bytes": OUT.stat().st_size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
