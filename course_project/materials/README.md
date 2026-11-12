# Material sources and review

The delivered report and slides use the frozen result JSON files. `validate_delivery.py` checks exported chart caches against those sources, page/slide counts, embedded chart workbooks and blank identity fields.

```bash
python course_project/materials/validate_delivery.py
```

This check requires `pypdf`, in addition to the research environment. It calls no model API.

## Sources preserved

- `build_report.py`, `report_common.py`: English ReportLab report.
- `figures.py`, `assets/`: three evidence plots, PNG and SVG.
- `build_deck.mjs`: fourteen native slide layouts and speaker notes.
- `template_blue.proto.json`: slimmed template furniture from the user-supplied blue PowerPoint template, with embedded fonts and unused content removed.
- `speaker_notes.json`: English speaking notes and corresponding Chinese explanations.
- `build_chinese_script.py`: matching illustrated Chinese reading/recording script.

Authoring used local ReportLab/matplotlib and the bundled `@oai/artifact-tool` presentation runtime after online session creation failed. Original template geometry is retained; charts, tables and process diagrams are native editable PowerPoint objects. The final file contains three embedded chart-data workbooks.

Build intermediates, slide renders and validators are preserved locally in `course_project/runs/materials_agentdojo_20261113/`; they are not part of the research evidence archive. The PDF builders use this build directory for matching slide thumbnails and report plots. Material authoring is separate from experiment execution and needs no API key.

## Completed review

- All ten report pages, fourteen slide renders and fourteen Chinese-script pages visually inspected.
- Final report body/layout grayscale; figures may use color. Slide colors follow the user's blue template.
- PDF identity fields checked in canonical form data and widget appearances.
- PPTX package/layout gates passed with no findings. Boundary warnings belong to the template's intentional cropped decorative polygons.
- Chart/workbook numbers agree with saved measured results.
- Native PowerPoint application opening was not performed.

Publication, name/student ID, actual Zoom recording and Blackboard submission remain outstanding. See the submission checklist.
