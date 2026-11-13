# Supplemental research acceptance

This directory contains research records and offline analysis, not a new submission report or presentation. Original PDF/PPTX/script files remain unchanged. Historical `course_project/README.md` results describe the earlier 326-episode stage; supplementary results must be read separately.

## Offline review

From the repository root, using the existing Python environment:

```bash
.venv/bin/python -m pytest -q course_project/extension/tests course_project/extension_review/test_review.py
.venv/bin/python -m course_project.extension_review.evidence verify
```

The supplemental archive is `course_project/evidence/extension_evidence.zip`; its manifest indexes every file and retains technical failures. Verification extracts to a temporary directory, checks all hashes, and reruns the archived actors using recorded responses with outgoing sockets blocked. It does not generate new model answers. It reuses installed dependencies; it is not a fresh dependency installation.

Historical 326-episode evidence remains in its separate archive and is verified with `python -m course_project.evidence verify`. Neither archive should be described as covering the other.

## Analysis records

- `workspace_merged_results.json`: original151 + continuation29, unique frozen schedule, complete audit.
- `banking_control_results.json`: six-task matched-continuation comparison, three trials.
- `banking_pairs.json`: every recovery-success/neutral-failure pair; independent model draws, not identical-prefix counterfactuals.
- `banking_prefix.json`: actual native-tool prefix replay, before/after each saved added stage.
- `sensitivity.json`: explicitly post-hoc preservation-of-rent-date criterion and exclusion of the scam-like fee task; not replacement formal scores.
- `parameter_development_results.json`: original ten-case development diagnosis.
- `parameter_exposure_correction.json`: rendered literal-escape exposure diagnosis; original fields retained.
- `parameter_confirmation_results.json`: same-development-task repeated confirmation, not a held-out evaluation.
- `gate_diagnosis.json`: actual allow/deny decisions, distinct from aggregate ASR differences.
- `travel_audit.json`: task/scorer reference and no-op controls, prospective development/formal split.
- `travel_development_results.json`: development cohort, excluded from formal efficacy.
- `execution_notes.json`: technical recovery and verifier adjustments.
- `materials_unchanged.json`: existing report/deck/script artifact hashes.

## Paid reruns

Historical freeze/run entry points reproduce the frozen original schedule and are not an outcome-retry mechanism. Fresh samples should use `course_project.extension.rerun PHASE --budget-cny AMOUNT --live` with an explicit budget and the off-peak guard. Dry-run is the default. Current cumulative conservative accounting is in the acceptance receipt; do not assume an8CNY default reservation fits remaining budget. No credentials belong in the repository.

## Interpretation boundaries

Static-goal recovery, data-dependent recipient redirection, native utility and actual gate denials are different observations. In particular, user delegation to a landlord file makes disguised account-change content an authorization/data-integrity ambiguity. A lower native targeted ASR does not alone establish reliable semantic authorization. Formal trials reuse fixed tasks; three trials are not three independent datasets.

Formal Travel tasks were reserved before its first model outputs. They are three calendar-reminder tasks, not coverage of all Travel applications. The development set includes recommendation, reservation and budget-calculation tasks, but those are not formal held-out efficacy cases. Never expand a cross-scene claim beyond these sampled tasks.
