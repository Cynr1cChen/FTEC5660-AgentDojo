# Final course materials

The research is closed. These materials cover the banking study, matched continuation, transfer failures, execution controls and final shared-policy trade-off.

## Current deliverables

- [English report, 10 pages](../../output/pdf/FTEC5660_AgentDojo_Final_Report.pdf)
- [Submission presentation PDF, 15 pages: 12 main slides and 3 backups](../../output/pdf/FTEC5660_AgentDojo_Final_Presentation.pdf)
- [English presentation, 12 main slides and 3 hidden backups](../../output/pptx/FTEC5660_AgentDojo_Final_Presentation.pptx)
- [Recording script, English with Chinese below](../../output/pdf/FTEC5660_AgentDojo_Recording_Script_EN_CN.pdf)

The spoken script has 1,541 English words. It follows the 12 main slides as a connected spoken narrative, with deliberate paragraph boundaries and transitions between slides. English comes first, followed by Chinese, without target-duration labels. Public report and presentation files omit the student name and ID. Identified copies are retained only in the local submission folder. The slide notes include the corresponding English/Chinese script and source pointers.

The supplied blue geometric template remains the design base. Ordinary explanations use flat educational illustrations inspired by the user's MEV reference. Architecture, execution flow and evidence diagrams use academic conventions and editable native shapes. Four native charts include four embedded data workbooks, and seven tables remain editable. Explanatory text accompanies the visuals where needed.

## Sources and rebuilding

- `collect_facts.py` verifies the frozen research source hashes and creates `facts.json`.
- `narrative.py` contains the report prose and imports the bilingual speech from `spoken_script.py`. `report.md`, `recording_script_EN_CN.md` and `speaker_notes.json` expose the corresponding text for review.
- `build_pdf.py` builds the report and bilingual script with ReportLab and embedded font subsets.
- `build_deck.mjs` imports the supplied slim template, creates native objects and a versioned validated PPTX in the private `build/final/` directory. It uses the bundled `@oai/artifact-tool` runtime. The reviewed final file is copied unchanged to the delivery location.
- `update_speaker_notes.mjs` authors revised notes with Artifact Tool, then replaces only the 12 main note parts. `notes_revision.json` verifies that all visible slides, media, charts and embedded workbooks remain byte-identical.
- `asset_manifest.json` records illustration provenance and reference hashes.
- `validate_materials.py` checks the delivered files against source values, page/slide counts, notes, blank identity fields, chart/workbook contents and the four unchanged evidence archives. It performs no model sampling.

PDF authoring/validation requires ReportLab, pypdf, pdfplumber, Pillow and the documented system fonts. Presentation authoring uses the Codex bundled runtime located with `load_workspace_dependencies`. The Node module link and build/render scratch files are deliberately excluded from Git.

## Acceptance record

`delivery_validation.json` is the current acceptance receipt. Every final report page, script page and packaged slide was rendered and reviewed individually. Package structure, declared fonts, native charts and embedded workbooks pass. Retained corner polygons intentionally bleed outside the canvas, matching the supplied template. Native PowerPoint application opening was not performed.

The old report/PPT remain retired at their original paths. The earlier Chinese script and historical builders remain available as historical sources. `framework_checks.json` records the earlier planning stage, and the original research acceptance receipts predate material retirement. Neither is a current-file hash assertion. Use `delivery_validation.json` for the final exports.

The [public student repository](https://github.com/Cynr1cChen/FTEC5660-AgentDojo) is published with the original author attribution and complete history. Anonymous access and key file hashes were verified; see `github_publication.json`. The recording has been completed, and its access details are supplied privately for submission. The remaining action is Blackboard submission and saving the receipt. No new research experiment or DeepSeek sampling was performed during material authoring.

## Blackboard submission folder

The user confirmed a file area and a text area in Blackboard. The report PDF belongs in the file area, and the student GitHub and Zoom recording links belong in the text area. The assignment does not separately require the PPTX or script. The student also requested submission of a complete 15-page presentation PDF, which is included in the upload directory.

`prepare_submission.py` organized unchanged copies at `/Users/Admin1/Desktop/Courses/Agentic AI for Business and FinTech/individual project2/FTEC5660_Submission/`, with an upload directory, a link-text template and recording aids. `submission_package.json` records this handoff. The script refuses to overwrite a nonempty folder, preserving future identity/link edits. `submission_credential_check.json` records a current-tree and evidence-archive pattern scan, separate from the full history check needed before publication. The initial packaging step did not publish or submit anything. GitHub publication has since completed; Blackboard submission remains pending.
