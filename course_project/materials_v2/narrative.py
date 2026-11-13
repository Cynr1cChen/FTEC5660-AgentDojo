"""Final report prose and fluent English/Chinese recording script.

Research values enter from facts.json. Layout lives in separate builders.
"""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
F=json.loads((HERE/'facts.json').read_text())
pc=lambda v:f'{100*v:.2f}%'
main_rate=lambda a:pc(F['main'][a]['safe']['mean'])
neutral_count=lambda a:F['neutral'][a]['attacked']['strict_safe']['count']

TITLE='Beyond Attack Rejection'
SUBTITLE='Task Completion in AgentDojo'

# Blocks: p=paragraph, h=section heading, fig/data/diagram=builder-owned evidence.
REPORT=[
{'title':'', 'blocks':[
('h','Abstract'),
('p',f"A tool-using agent can reject a prompt injection and still abandon the user's task. This project reproduces AgentDojo's execution and evaluation workflow with DeepSeek Flash and tests one bounded task-review stage. In a frozen six-task banking comparison, safe completion under attack rises from {main_rate('baseline')} for the native agent to {main_rate('recovery')} for review, while prompt repetition reaches {main_rate('repeat')}. A separate matched continuation study records 18/36, 25/36 and 35/36 completions for baseline, neutral continuation and review. Cross-scenario tests identify an important failure: review can replace a useful informational answer with an incomplete confirmation. Exploratory authorization experiments then demonstrate actual parameter-level interception, followed by a shared-policy candidate that completes all 12 attacked rent cases but reduces other legitimate control completion from 9/9 to 5/9. The resulting contribution is an auditable account of completion gains, failure mechanisms and authorization trade-offs."),
('h','1. Motivation and research questions'),
('p',"Consider a request to refund an incoming payment. The transaction subject contains an instruction to redirect another payment. The agent recognizes the injection and refuses it, yet asks the user to authorize the already requested refund again. The attacker misses its target and the useful workflow remains unfinished. This gap motivates completion-focused evaluation alongside attack success."),
('data','questions'),
('p',"The primary modification is one bounded review after the native pipeline stops. Neutral continuation tests the explanation for its gain. Transfer tests and authorization controls form separate exploratory studies. Their results explain when the method helps, when it fails and which candidate should remain an experiment."),
('source','Sources: [1,2]; formal/protocol.json; extension_review/banking_control_results.json; closure/results.json.')
]},
{'title':'2. System and reproduction scope','blocks':[
('p',"AgentDojo couples an LLM agent to executable Python tools and mutable application state. The agent reads business data, selects tools and receives their results before continuing. User-task utility and attacker-goal checks inspect answers or environment changes [1,2]. This study uses the authors' repository and native tool implementations, preserving the multi-step interaction rather than replacing it with a text-only simulation."),
('diagram','system'),
('p',"The original user request and runtime define trusted authority. The attacker replaces designated later tool-result text, such as a transaction subject or a landlord notice. That text can supply relevant facts while also attempting to create a conflicting instruction. The attacker does not modify the user's request, tool implementation or evaluator."),
('data','scope'),
('h','Reproduction target'),
('p',"The project reproduces the framework's tool-use workflow and its joint utility/security evaluation. It also reproduces attack-associated task abandonment in the selected banking conditions. DeepSeek replaces the paper's models, and the task subset, attack coverage and benchmark version differ. The paper's aggregate scores therefore serve as context, while the frozen local comparisons establish this project's numerical results."),
('p',"The main task IDs are 4, 7, 11, 12, 14 and 15. They cover refunds, information retrieval, fee payment, rent adjustment, a conditional password update and a compound moving request. Development tasks and the pre-outcome scorer audit determine this selection before formal model outcomes. Later scenario and policy candidates use their own frozen protocols."),
('source','Sources: [1,2]; stage1/task_audit.json; formal/protocol.json; run_pilot.py; interventions.py.')
]},
{'title':'3. Measurement and bounded review','blocks':[
('p',"Let U denote the native user-task pass, A the specified attacker-goal success and B the supplementary state checks declared for that protocol. Native safe completion is U and not A. Strict safe completion additionally requires B. Clean utility measures U without injection. Each table identifies the metric and denominator because B becomes more demanding in later studies."),
('data','metrics'),
('p',"The scorer audit exposes why these distinctions matter. Some native tasks pass without an intended write. A rent amount can satisfy utility even when a malicious recipient change also succeeds. Added checks inspect relevant parameters, extra transfers and, where specified, date or recurrence. Native scores remain intact, and sensitivity analyses appear separately."),
('p',"The native baseline runs the original pipeline. The authors' repetition defense re-appends the user request after tool execution. Review uses a separate added stage and does not combine that defense with the action gate. Main attacks use the original tool_knowledge template and native goals 4 and 7."),
('h','One change to the native pipeline'),
('p',"After a native invocation produces its final answer, the recovery arm adds a system review asking the agent to reread the original request, identify unfinished authorized work and complete it with available facts. It asks for minimal changes, preservation of unspecified fields and no duplicate writes. It still asks for genuinely missing information. The trigger uses the stopping point, without scores, reference actions or hidden state."),
('diagram','review'),
('p',"The extra stage shares the remaining 15 tool rounds rather than resetting the budget. It runs at most once per native invocation. AgentDojo's existing suite-level reinvocation on absent output remains unchanged. The main matrix contains six tasks, three arms, clean plus two attacker goals and three trials: 162 runs, with 18 clean and 36 attacked runs per arm. The original tool_knowledge payload for each task/goal is identical across arms and trials. Arm order rotates within conditions."),
('p',"Mean and sample SD describe three trial rates on the same fixed tasks. They measure observed run variability. The intervention is selected before formal sampling, and later candidate development remains distinct from this primary comparison."),
('source','Sources: formal/protocol.json; interventions.py::Recovery; formal.py; results_formal.py.')
]},
{'title':'4. Banking completion improves','blocks':[
('fig','main'),
('data','main'),
('p',f"Bounded review improves safe completion by 50.00 percentage points over baseline and by 36.11 points over prompt repetition. All 108 attacked runs encounter the injection, and every arm records zero specified attacker-goal successes. The result establishes additional legitimate completion. The predeclared supplementary state checks agree with the native completion outcomes."),
('p',"The improvement is uneven across tasks. Review completes all six attacked repetitions for five task IDs but only one of six for rent task 12. Its notice requests a standing-order adjustment next month, while the stored transaction is non-recurring and dated in the past. Some trajectories perform the required amount update, while others request further clarification."),
('h','A separate date-context follow-up'),
('p',"A secondary protocol supplies every arm with the same simulation date, 2022-04-01, on transfer tasks 4, 11 and 15. The 81 fresh runs yield 16.67%, 55.56% and 94.44% safe completion for baseline, repetition and review. Supplementary state/date checks agree, and new transfers use the supplied date. This follow-up confirms the completion advantage with grounded timing. It remains a separate subset and sampling protocol."),
('source','Figure 1: original six-task study, n=36 attacked per arm, mean and sample SD over three trials. Sources: formal/results.json; date_followup/results.json.')
]},
{'title':'5. The gain exceeds neutral continuation','blocks':[
('p',"An extra opportunity to act could explain part of the banking gain. A later comparison therefore gives a neutral continuation arm the same post-stop trigger and remaining loop budget as review. Every arm receives the same explicit simulation date. The six tasks and attacks remain matched within this new study."),
('fig','neutral'),
('p',"Attacked strict safe completion is 18/36 for baseline, 25/36 for neutral continuation and 35/36 for bounded review. Clean completion is 16/18, 16/18 and 18/18. All three arms again record zero attack-goal successes. Review exceeds the neutral opportunity to continue by ten completions in this cohort."),
('h','Recorded trajectories explain the extra work'),
('quote','bank'),
('p',"Replaying the same review trajectories only up to the first added stage gives 17/36 attacked completions before review and 35/36 afterward. Eighteen runs recover and none lose completion. Neutral trajectories improve from 18/36 to 25/36. These within-trajectory replays locate the added work without treating independent arms as identical model prefixes."),
('h','Stricter interpretation narrows the advantage'),
('p',"A post-hoc requirement to preserve unspecified rent dates and recurrence lowers review to 32/36, while neutral continuation remains 25/36. Removing the fee-payment task, whose demand resembles a scam, and retaining timing preservation gives 26/30 versus 24/30. The direction survives these checks, but the size depends on the business interpretation. Benchmark fee completion alone does not establish that paying the demand is a sound financial decision."),
('source','Figure 2: separate matched continuation study, n=36 attacked per arm, three trials. Sources: extension_review/banking_control_results.json; banking_prefix.json; sensitivity.json.')
]},
{'title':'6. Transfer exposes answer replacement','blocks':[
('p',"Scenario expansion first tests Workspace, Travel calendar tasks and Slack. The native baseline already completes every tested attacked condition in these subsets, leaving no completion headroom. These ceiling results extend coverage but do not establish an improvement."),
('data','transfer'),
('h','A useful answer becomes an incomplete confirmation'),
('quote','travel'),
('p',"More complex Travel tasks 12, 15 and 18 require a detailed informational answer. In 81 runs, baseline and neutral continuation each complete 14/18 attacked cases, while review completes 12/18. Clean completion is 7/9, 9/9 and 4/9. No specified attack succeeds. Thus adding review can damage utility even without an unauthorized action."),
('p',"The saved review trajectories identify the mechanism. Before the added stage, 22/27 answers pass the native grader. Afterward, 16/27 pass. Six previously complete answers lose required content, with no rescued answers and no state changes. In the Paris example, the review says it already supplied the addresses but omits both addresses from the final answer. The grader's literal sensitivity matters, and the concrete loss of requested information makes this failure substantive."),
('h','A bounded repair attempt'),
('p',"A post-hoc selector retains the original answer when review proposes no additional tool calls. An 81-run fresh follow-up on the same observed tasks gives baseline and the selector 22/27 completions each. The selector avoids answer replacement but does not outperform baseline. The project retains this negative result and stops this branch. Action recovery and answer revision require different output handling."),
('source','Sources: extension_review/*merged_results.json; round2/slack_broader_results.json; travel_broader_results.json; travel_diagnosis.json; travel_output_followup_results.json.')
]},
{'title':'7. Authorization controls reveal a second gap','blocks':[
('p',"The original attacks leave banking ASR at zero. Stronger parameter attacks instead hide a recipient-account substitution inside a plausible landlord notice. A tool call can complete the rent amount change and satisfy the attacker's recipient goal simultaneously. This makes real execution control measurable."),
('data','authorization'),
('p',"The semantic gate reviews proposed writes and their parameter values against the original task. Business-looking instructions can still persuade it. In the same-development-task confirmation, attacker success is 9/12 for native baseline, 5/12 for the gate and 8/12 for review. Only one actual semantic denial occurs. The difference between outcome rates therefore cannot be read as a count of interceptions."),
('h','Full permission lists overconstrain useful work'),
('p',"The permission compiler produces an explicit operation contract before execution. Across five task types and three trials, its ASR is 0/36 versus 8/36 for baseline, while clean completion drops from 11/15 to 6/15. Empty contracts and missing required fields explain blocked legitimate operations. Attacked strict safe completion also falls from 15/36 to 12/36. This candidate sacrifices too much task completion."),
('h','Narrow hard rules produce actual interception'),
('p',"A narrower executor requires scheduled-payment recipients and password values to have direct support in the original request. A fresh formal comparison records ASR 6/36 for baseline, 7/36 for the semantic gate and 0/36 for the hard-rule arm. Clean completion is 9/15, 11/15 and 10/15. Seven recorded calls pass the semantic gate and then receive a hard denial. Executing each denied call on its exact saved pre-operation state would achieve the attacker goal, confirming seven local interceptions."),
('p',"Rent strict safe completion nevertheless remains 0/12 in that hard-rule study. Positive normal controls reach 9/9, but the attacked rent task still stops after rejection or never proposes the safe adjustment. The next experiment addresses this completion gap while retaining the same hard rules."),
('source','Separate cohorts: S7 permission compiler and S8 hard-rule follow-up. Sources: extension_review/parameter_confirmation_results.json; round2/contract_formal_results.json; anchored_merged_results.json; gate_diagnosis.json.')
]},
{'title':'8. Shared policy repairs rent with a cost','blocks':[
('p',"The prior rent traces reveal inconsistent authorization reasoning: a checker can reject an account substitution, then reject an amount-only call for omitting that same substitution. One final candidate gives the actor and semantic checker a shared policy. It separates supported ordinary work from protected recipient/password changes and preserves unspecified date and recurrence."),
('diagram','policy'),
('p',"The candidate retains the original hard rules, tool implementations, denial feedback and loop limits. It adds no post-stop recovery, parameter rewriting or simulated user confirmation. A frozen 48-run study compares the old semantic-plus-hard-rule policy with the shared policy across three trials. Each arm has 12 attacked rent cases, three clean rent cases and nine other legitimate controls."),
('fig','closure'),
('p',"Attacked rent strict safe completion changes from 0/12 to 12/12, and clean rent from 0/3 to 3/3. Both arms retain ASR 0/12. The new actor directly proposes the supported amount adjustment, preserving the recipient and existing timing fields. These are completions through better initial planning, with no new actual hard or semantic denials."),
('p',"Other legitimate controls decline from 9/9 to 5/9: address updates remain 3/3, conditional password changes fall to 2/3 and the compound moving task falls to 0/3. Including clean rent, overall clean completion changes from 9/12 to 8/12. The shared policy is a local repair with a measurable authorization cost, so it remains an exploratory candidate rather than the global default."),
('source','Figure 3: fixed 48-run closure study. Comparator is the old semantic-plus-hard-rule policy. Sources: closure/shared_policy/protocol.json; pipelines.py; results.json; action_audit.json.')
]},
{'title':'9. Genuine user authority gets misread','blocks':[
('quote','authority'),
('p',"All four failed legitimate controls omit the affected sensitive operation before proposing it. One password trajectory identifies suspicious activity but treats the user's conditional password request as insufficiently direct. Three compound-task trajectories request confirmation of a landlord account that the original user already supplied. Some still update the address or issue the refund, leaving the full task incomplete."),
('p',"The request-level audit checks all 234 actual requests. The actor receives the complete original query, and the checker's original_user_request field matches it. The shared policy reaches both components. The requested account and password values are present, and the unchanged hard rules would allow them if proposed. These losses arise in model authorization interpretation, without a hard or semantic denial of the affected operation."),
('data','debug'),
('h','Conclusions and research closure'),
('p',"First, bounded review improves completion of the tested banking workflows and outperforms a neutral continuation opportunity. Second, transfer depends on task form: informational answers can regress when confirmation replaces the requested details. Third, narrow execution rules provide observed parameter-level interception, but successful rejection and authorized completion remain separate outcomes."),
('p',"The final shared-policy attempt closes the explanatory loop. A concrete inconsistency motivates one candidate, a fixed evaluation reveals both its local repair and legitimate-task cost, and request/state audits identify where the remaining failures occur. The project keeps bounded review as the primary contribution, retains the normal-control regression and ends further policy development. Fixed tasks, static attacks and three repetitions define the empirical scope. The qualitative trace diagnosis comes from one non-blind assistant review."),
('source','Sources: closure/wire_review.json; action_audit.json; RESEARCH_CLOSURE.md; round2/gate_diagnosis.json.')
]},
{'title':'10. Reproducibility and references','blocks':[
('p',"The four evidence archives cover 326, 587, 677 and 48 completed runs, including development, comparison conditions and repeated trials. Their total of 1,638 describes execution volume, not independent task diversity. Each archive preserves model requests/responses, protocol and source hashes, native calls and environment states. Offline verification restores archived source into an isolated directory and blocks outgoing sockets while replaying saved responses."),
('data','replay'),
('p',"Sixty relevant tests pass. A fresh Python environment on the same macOS system, installed from a locked offline cache, also passes the recorded checks and archive replay. Technical interruptions preserve completed cases and diagnostic records. The final cohort resumes its exact remaining schedule, without candidate or scoring changes."),
('h','References and evidence index'),
('ref','[1] E. Debenedetti, J. Zhang, M. Balunovic, L. Beurer-Kellner, M. Fischer and F. Tramèr. AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents. NeurIPS Datasets and Benchmarks, 2024. arXiv:2406.13352v3. https://arxiv.org/html/2406.13352v3'),
('ref','[2] ETH Zurich SPY Lab. AgentDojo author repository. Pinned commit 089ed468cf3ed0322acc66b0211f26d9d90dbf60. https://github.com/ethz-spylab/agentdojo'),
('ref','[3] Primary method and frozen main evidence: course_project/interventions.py; formal/protocol.json; formal/results.json; date_followup/results.json.'),
('ref','[4] Continuation and sensitivity: course_project/extension_review/banking_control_results.json; banking_prefix.json; sensitivity.json. Transfer and execution-control studies: course_project/round2/.'),
('ref','[5] Final policy, results and provenance: course_project/closure/pipelines.py; shared_policy/protocol.json; results.json; action_audit.json; wire_review.json. Evidence ledger: course_project/materials_v2/evidence_ledger.json.'),
]}
]

# Speech is authored separately, with explicit paragraphs and slide transitions.
from spoken_script import SCRIPT

if __name__=='__main__':
    import re
    print('Report prose words:',sum(len(re.findall(r"\b[\w'-]+\b",v)) for p in REPORT for k,v in p['blocks'] if k in ['p','ref']))
    print('English script words:',sum(len(re.findall(r"\b[\w'-]+\b",e)) for _,e,_ in SCRIPT))
