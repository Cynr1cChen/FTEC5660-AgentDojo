# FTEC5660: AgentDojo reproduction and bounded task recovery

**Final materials are complete: [report, presentation and bilingual recording script](materials_v2/README.md).** They cover the completed research through the fixed48-case shared-policy study. Research sampling is closed, retaining both local gains and normal-control regressions. Read the [研究收尾与结项](closure/RESEARCH_CLOSURE.md) for the research disposition. The old report/PPT remain retired, and the earlier Chinese script is historical. The page below describes the original326-run stage; later evidence is in [extension_review](extension_review/README.md), [round2](round2/README.md) and [closure](closure/README.md). Identity completion, GitHub publication, actual Zoom recording and submission remain outstanding.

This project runs the released AgentDojo banking Agent, reproduces multi-step tool execution and attack-associated utility loss, and adds **one bounded task-review stage** after the native Agent stops. Review uses the original user request and visible tool results, without reference answers, attack labels, scores or hidden state.

## Read first

- [Final materials and source files](materials_v2/README.md)
- [Report/PPT/recording-script framework](materials_v2/FRAMEWORK.md)
- [Exact retirement scope and original hashes](materials_v2/retired_artifacts.json)
- [Historical Chinese explanation, not the new recording script](../output/pdf/FTEC5660_AgentDojo_中文讲解稿.pdf)
- [Submission checklist](SUBMISSION_CHECKLIST.md)

## Main results

Frozen six-task experiment, three fresh API repetitions, 162 episodes:

| Arm | Clean completion | Safe completion under attack, mean (sample SD) | Attacker success |
|---|---:|---:|---:|
| Native baseline | 66.67% | 36.11% (12.73 pp) | 0/36 |
| Author prompt repetition | 72.22% | 50.00% (0.00 pp) | 0/36 |
| Bounded task review | 100.00% | 86.11% (4.81 pp) | 0/36 |

Safe completion means user-task success and attacker-goal failure. All attacked episodes expose the injected text. Native utility and prospectively specified supplementary state checks agree in every formal episode. The improvement concerns completion, not an ASR reduction from zero.

Prefix replay of recovery trajectories gives 14/36 attacked completions before review versus 31/36 afterwards: **17 rescued, none lost**. This is a within-trajectory diagnostic, not an independently sampled baseline. Remaining main failures concentrate in task 12, whose rent notice and stored recurrence/date fields conflict.

A separately frozen follow-up gives the same simulation date to all arms on three transfer tasks. Safe completion is 16.67%, 55.56% and 94.44%. Exact state/date checks agree. This post-hoc follow-up is reported separately.

## Reproduction target and scope

We reproduce AgentDojo's utility/security behavior, rather than equality to paper aggregates. The model, task coverage and benchmark version differ. Successful malicious actions were not reproduced for tested attacks.

- Author commit: `089ed468cf3ed0322acc66b0211f26d9d90dbf60`.
- Package `0.1.35`; benchmark `v1.2.2`, banking only.
- Main tasks: 4, 7, 11, 12, 14, 15; original `tool_knowledge` attack, goals 4 and 7.
- Official DeepSeek API; requested/returned alias `deepseek-flash`.
- Temperature 0, thinking disabled, 2,048 output tokens, SDK retries disabled.
- Native 15 tool rounds per invocation; at most one added review using remaining rounds. Native suite-level reinvocation behavior stays unchanged.
- Trusted original user/runtime; attacker controls designated later tool-result text.

The initial action/parameter gate was implemented and compared on development tasks. Recovery performed better and became the sole formal modification **before formal sampling**. The recovery arm does not also enable that gate. See `comparison_dev/decision.json`.

## Install

Verified locally on macOS arm64, Python 3.12.14. No GPU required. From repository root:

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r course_project/requirements.lock.txt
```

Alternatively activate a Python 3.12 virtual environment and run `pip install -r course_project/requirements.lock.txt`. The lock records validated versions. A fresh virtual environment on the same OS has now been validated using an offline package cache; see `round2/fresh_environment.json`. Another OS and fresh network downloads have not been validated.

## Verify saved evidence without API calls

```bash
.venv/bin/python -m course_project.evidence verify
```

This restores hash-indexed evidence into an isolated temporary checkout, checks saved requests/responses, replays native tools and scoring with sockets blocked, checks formal states, and recomputes results. It reuses installed dependencies, requires no key, and preserves original runs. **326 episodes, 1,016 requests and 243 formal state files passed.** Replay does not generate new model answers.

```bash
.venv/bin/python -m pytest course_project/tests tests/test_task_injectability.py tests/test_agent_pipeline/test_prompting_llm.py tests/test_functions_runtime/test_functions_runtime.py tests/test_benchmark.py tests/test_workspace_user_tasks.py -q
```

Result: **37 passed**. Empirical performance comes from recorded API runs, not test fixtures.

## Fresh model samples

Dry runs cost nothing:

```bash
.venv/bin/python -m course_project.rerun --context original
.venv/bin/python -m course_project.rerun --context dated
```

For paid sampling, create a local `.env` from `.env.example` if needed, fill the key in an editor, retain the declared model/base URL, then explicitly add `--live`:

```bash
.venv/bin/python -m course_project.rerun --context original --budget-cny 3 --live
```

Fresh samples go to timestamped `runs/rerun/` directories. Original study files remain unchanged. The runner enforces local and cumulative 100 CNY conservative budgets and low-period request-start guards. New samples can differ stochastically. Recheck current pricing before future paid work. Use this portable entry rather than historical development-freeze commands.

## Evidence and implementation map

| Path | Purpose |
|---|---|
| `stage1/task_audit.json` | Task/scorer audit and reference controls |
| `stage1/`, `supplement/`, `comparison_dev/` | Development cohorts and prospective selection |
| `formal/protocol.json`, `formal/results.json` | Main frozen plan and results |
| `formal/recovery_diagnosis.json` | Prefix replay |
| `date_followup/` | Separate shared-date follow-up |
| `interventions.py` | Action gate and bounded review |
| `formal.py`, `dated.py` | Out-of-model observers and supplementary scoring |
| `audit_controlled.py`, `formal_audit.py` | Request/trace/state verification |
| `evidence/` | Synthetic-data archive, hashes and verification receipt |
| `materials/` | Report/deck/script authoring sources |
| `budget_final.json` | Usage and conservative accounting |

New runs total approximately **0.8621 CNY** at recorded low-period/cache rates; no-cache peak-rate bound **5.5254 CNY**. Including prior A-Mem and old AgentDojo accounting, the conservative project bound is **76.4827 CNY**. These usage estimates are distinct from a provider account statement.

Original exploratory cohorts remain separate. The figures and100CNY rerun limit above describe the historical stage. Final research disposition and explicitly authorized150CNY accounting are owned by closure/acceptance.json; round2 remains historical, and old paid rerun commands retain their original limits. Do not pool these distinct experimental protocols.

## Primary references

- [AgentDojo paper v3](https://arxiv.org/html/2406.13352v3), NeurIPS 2024 Datasets and Benchmarks.
- [Author code](https://github.com/ethz-spylab/agentdojo).
- [Pipeline documentation](https://agentdojo.spylab.ai/concepts/agent_pipeline/).
- [DeepSeek pricing](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/), checked 13 November 2026.
