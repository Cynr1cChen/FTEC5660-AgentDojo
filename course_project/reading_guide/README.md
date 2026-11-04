# AgentDojo 中文阅读指南

成品：[AgentDojo 论文与仓库详解](../output/pdf/AgentDojo_论文与仓库详解.pdf)，35 页。

指南依据 NeurIPS 2024 Datasets and Benchmarks Track 正式论文、固定上游提交 `089ed468cf3ed0322acc66b0211f26d9d90dbf60`，以及 2026-11-01 的本地开发日志。涵盖原论文的研究设计、实验和局限，仓库的任务／工具／攻击／防御／评分执行链，以及截至 2026-11-04 的课程工作。文中表格明确标注来源与版本；两幅案例图源于已保存的日志，而非新运行结果。

这是一份阅读说明，不是已完成的复现研究，也不是课程要求的最终报告。此次制作没有调用模型 API，没有运行新的付费评测，没有实现新增防御。

## 重新生成

从仓库根目录运行，所用 Python 需安装 `reportlab`：

```bash
python3 course_project/reading_guide/build_guide.py
```

脚本使用 macOS 的 `/System/Library/Fonts/Supplemental/Arial Unicode.ttf`。在其他系统需将 `FONT_PATH` 改为可嵌入、包含简体中文的 TrueType 字体。内容位于 `guide_content.py`，插图由 ReportLab 绘制，案例图引用 `course_project/presentation_assets/` 中的已追踪文件。脚本无需读取 `.env` 或访问网络。

## 排版核查

```bash
pdftoppm -r 105 -png 'course_project/output/pdf/AgentDojo_论文与仓库详解.pdf' course_project/tmp/pdfs/reading_guide/page
```

成品已经检查页序、35 个书签、目录与来源链接、中文文字提取和字体嵌入，并查看全部页面的渲染结果。临时预览与生成记录存于 `course_project/tmp/`，不纳入 Git。
