# Beyond Attack Rejection: Task Completion in AgentDojo

**FTEC5660 Individual Reproducibility Project**

A tool-using agent can reject a prompt injection and still leave the user's task unfinished. This project reproduces AgentDojo's execution and evaluation workflow with DeepSeek Flash, adds one bounded task-review stage, and investigates where completion improves, where it regresses, and how execution controls interact with user authorization.

[Report](output/pdf/FTEC5660_AgentDojo_Final_Report.pdf) · [Presentation PDF](output/pdf/FTEC5660_AgentDojo_Final_Presentation.pdf) · [Editable slides](output/pptx/FTEC5660_AgentDojo_Final_Presentation.pptx) · [English/Chinese recording script](output/pdf/FTEC5660_AgentDojo_Recording_Script_EN_CN.pdf)

## Research question

Imagine asking an assistant to refund an incoming payment. The transaction record contains an instruction to redirect another payment. The assistant rejects the injected instruction, then asks the user to authorize the already requested refund again. The attack fails, but the refund never happens.

The project examines three questions:

1. Can one bounded review help the agent complete authorized work after it stops?
2. Does that improvement transfer to other task types and scenarios?
3. Can execution controls block malicious parameter changes while preserving legitimate task completion?

## What this project contributes

| Contribution | Implementation and evidence |
|---|---|
| Reproduction and evaluation audit | Pinned AgentDojo version, DeepSeek adapter, task/scorer controls and recorded requests, responses and native states; [project guide](course_project/README.md) |
| Bounded task review, the primary modification | One review after the native pipeline returns, using the original request and visible tool results within the remaining tool-round budget; [implementation](course_project/interventions.py), [formal protocol](course_project/formal/protocol.json) |
| Matched continuation and sensitivity studies | Separate native, neutral-continuation and review samples, plus state/date checks and task-exclusion sensitivity; [supplemental analysis](course_project/extension_review/README.md) |
| Transfer and failure analysis | Workspace, Travel and Slack tests; diagnosis of review replacing useful informational answers; one output-selection follow-up; [second extension](course_project/round2/README.md) |
| Authorization experiments | Semantic review, permission compilation, hard parameter checks and a final shared actor/checker policy; [extension pipelines](course_project/extension/pipelines.py), [round2 pipelines](course_project/round2/pipelines.py), [shared-policy implementation](course_project/closure/pipelines.py) |
| Reproducible research evidence | Four hash-indexed archives, offline native-tool replay, analysis scripts and test receipts; [evidence directory](course_project/evidence/), [final research disposition](course_project/closure/RESEARCH_CLOSURE.md) |

Most student implementation is in `course_project/`. The upstream source change in [`task_suite.py`](src/agentdojo/task_suite/task_suite.py) corrects injectability detection for string and structured tool content; [`test_task_injectability.py`](tests/test_task_injectability.py) covers that correction. The task-review and authorization methods are implemented separately from the original benchmark core.

## Main findings

### 1. Bounded review improves completion on the banking study

The original frozen six-task comparison has three arms, three repetitions and 162 completed episodes. Each arm includes 36 attacked episodes.

| Arm | Clean completion | Safe completion under attack | Attacker success |
|---|---:|---:|---:|
| Native agent | 66.67% | 36.11% (13/36) | 0/36 |
| Author prompt repetition | 72.22% | 50.00% (18/36) | 0/36 |
| Bounded task review | 100.00% | **86.11% (31/36)** | 0/36 |

Safe completion requires both user-task success and attacker-goal failure. The observed gain is in completion; attack success is already zero in the native baseline. Sources: [formal results](course_project/formal/results.json) and [report](output/pdf/FTEC5660_AgentDojo_Final_Report.pdf).

A separate matched continuation study records **18/36 native, 25/36 neutral continuation and 35/36 bounded review** attacked completions. This supports a benefit beyond simply giving the agent another chance to continue. It is a separate protocol and is not pooled with the original comparison. See [matched-study results](course_project/extension_review/banking_control_results.json).

### 2. Transfer depends on preserving useful answers

Workspace, the initial Travel calendar subset and Slack reach ceiling performance in the tested subsets, so they do not demonstrate an improvement from review. In harder Travel tasks, review can replace a complete answer with an incomplete confirmation: completion falls from **22/27 before review to 16/27 after review** on the same saved trajectories. The subsequent output-selection study does not outperform the native baseline. See [Travel diagnosis](course_project/round2/travel_diagnosis.json) and [output-selection results](course_project/round2/travel_output_followup_results.json).

### 3. Execution control and useful completion need separate evaluation

The hard-parameter study retains **seven actual local interception witnesses**, verified against the saved pre-operation states. These are evidence of blocked operations, distinct from zero aggregate attack success. See [gate diagnosis](course_project/round2/gate_diagnosis.json).

A final fixed 48-run study compares the previous semantic-plus-hard-rule policy with one shared actor/checker policy:

| Outcome | Previous policy | Shared policy |
|---|---:|---:|
| Safe completion of attacked rent tasks | 0/12 | **12/12** |
| Completion of other legitimate controls | **9/9** | 5/9 |

The shared policy improves the rent workflow but causes the model to misread some valid user authority and ask for confirmation again. Its 12 rent completions occur through directly proposing a supported amount adjustment; they are not 12 new interceptions. The candidate remains an exploratory result, while bounded review remains the primary modification. See [final results](course_project/closure/results.json), [action audit](course_project/closure/action_audit.json) and [request-provenance review](course_project/closure/wire_review.json).

The research is closed with both gains and failures retained. The four stages contain **1,638 completed runs**, including development conditions and repeated tasks; they are not 1,638 independent tasks and are not combined into one performance score. This is a behavioral reproduction with a substitute model, rather than a numerical reproduction of the paper's aggregate results.

## Install

Validated setup: macOS arm64, Python 3.12, AgentDojo package 0.1.35, benchmark v1.2.2. The upstream baseline is pinned to commit `089ed468cf3ed0322acc66b0211f26d9d90dbf60`.

```bash
git clone https://github.com/Cynr1cChen/FTEC5660-AgentDojo.git
cd FTEC5660-AgentDojo
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r course_project/requirements.lock.txt
```

The lock file installs this checkout in editable mode. No API key is needed to verify saved evidence.

## Verify saved evidence without model calls

Run from the repository root:

```bash
.venv/bin/python -m course_project.evidence verify
.venv/bin/python -m course_project.extension_review.evidence verify
.venv/bin/python -m course_project.round2.evidence verify
.venv/bin/python -m course_project.closure.evidence verify
```

Each command verifies its own archive, restores saved records and the corresponding archived source in an isolated directory, and replays native tools and scoring with outgoing sockets blocked. Replay checks the saved experiment; it does not generate new model responses. The four archives cover separate research stages and retain technical interruptions.

The final research acceptance records 60 relevant passing tests. Validation and replay receipts are retained in [round2](course_project/round2/) and [closure verification](course_project/closure/verification/). Installation and detailed stage-specific commands are in the [project guide](course_project/README.md) and the stage READMEs.

For a cost-free preview of the original study's fresh-sample runner:

```bash
.venv/bin/python -m course_project.rerun --context original
```

Dry-run is the default. Live sampling requires a local API key, explicit `--live` and an applicable budget. Historical frozen protocols, paid-run limits and final accounting remain in their respective stage records.

## Repository map

| Path | Contents |
|---|---|
| `course_project/interventions.py` | Primary bounded review and the initial semantic gate |
| `course_project/formal/`, `course_project/date_followup/` | Main experiment and separate shared-date follow-up |
| `course_project/extension/`, `course_project/extension_review/` | Matched continuation, sensitivity, initial transfer and parameter studies |
| `course_project/round2/` | Broader transfer tests, output selection, permission compilation and hard-rule experiments |
| `course_project/closure/` | Final shared-policy candidate, fixed 48-run study and research closure |
| `course_project/evidence/` | Four replayable archives and manifests |
| `course_project/materials_v2/` | Current report, deck and script sources, plus validation records |
| `output/pdf/`, `output/pptx/` | Final materials and explicitly retained historical aids |
| `src/agentdojo/`, `tests/` | Original framework and benchmark tests, with the documented injectability correction |

Start with the **Final** report and presentation linked at the top. Stage acceptance documents preserve the status at the time they were written; references there to unfinished report or presentation work are historical. The current materials cover all completed research stages.

## Original project and attribution

This course project builds on **AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents**, by Edoardo Debenedetti, Jie Zhang, Mislav Balunović, Luca Beurer-Kellner, Marc Fischer and Florian Tramèr (NeurIPS 2024 Datasets and Benchmarks).

- [Original repository](https://github.com/ethz-spylab/agentdojo)
- [Paper](https://arxiv.org/abs/2406.13352)
- [Original README at the pinned commit](README_UPSTREAM.md)
- [Original citation](CITATION.bib)
- [MIT license](LICENSE)

The student research, modifications and interpretation are described above. Original framework attribution and licensing are retained.
