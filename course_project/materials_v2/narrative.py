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

TITLE='Reproducing AgentDojo'
SUBTITLE='Task Recovery and Authorization Trade-offs'

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
('p',"Sixty relevant tests pass. A fresh Python environment on the same macOS system, installed from a locked offline cache, also passes the recorded checks and archive replay. Technical interruptions preserve completed cases and partial usage. The final cohort resumes its exact remaining schedule, without candidate or scoring changes."),
('data','cost'),
('p',"Main-cohort call and latency means appear above. The final 48-run cohort records CNY 0.1784 in known usage plus a CNY 0.0275 unknown-request reservation, with a CNY 1.11583 conservative upper bound. The cumulative project ledger reaches CNY 125.13 against the authorized CNY 150 ceiling and includes earlier historical attempts. That cumulative bound is separate from the AgentDojo experiment usage estimates."),
('h','References and evidence index'),
('ref','[1] E. Debenedetti, J. Zhang, M. Balunovic, L. Beurer-Kellner, M. Fischer and F. Tramèr. AgentDojo: A Dynamic Environment to Evaluate Prompt Injection Attacks and Defenses for LLM Agents. NeurIPS Datasets and Benchmarks, 2024. arXiv:2406.13352v3. https://arxiv.org/html/2406.13352v3'),
('ref','[2] ETH Zurich SPY Lab. AgentDojo author repository. Pinned commit 089ed468cf3ed0322acc66b0211f26d9d90dbf60. https://github.com/ethz-spylab/agentdojo'),
('ref','[3] Primary method and frozen main evidence: course_project/interventions.py; formal/protocol.json; formal/results.json; date_followup/results.json.'),
('ref','[4] Continuation and sensitivity: course_project/extension_review/banking_control_results.json; banking_prefix.json; sensitivity.json. Transfer and execution-control studies: course_project/round2/.'),
('ref','[5] Final policy, results and provenance: course_project/closure/pipelines.py; shared_policy/protocol.json; results.json; action_audit.json; wire_review.json. Evidence ledger: course_project/materials_v2/evidence_ledger.json.'),
]}
]

SCRIPT=[
('Reproducing AgentDojo',
"Imagine asking an assistant to refund a payment. It spots a malicious instruction in the transaction record and refuses to follow it. The attack fails, but the refund still never happens. This project examines that gap: how an agent can protect the workflow and still finish the task the user asked for. I reproduce AgentDojo, test one bounded review step, and then use transfer and authorization experiments to understand both its gains and its failures.",
"设想你让一个助手退回一笔款项。它发现交易记录里夹带了恶意指令，并拒绝执行。攻击失败了，但退款也没有完成。这个项目研究的正是这个断点：Agent如何在保护工作流程的同时，完成用户真正要求的任务。我复现了AgentDojo，测试一次有边界的任务复核，再通过跨场景和授权实验，解释它的收益与失败。"),
('A refund, an injection and an unfinished task',
"Here is the workflow behind that example. The original user asks for a refund. The agent reads transaction data and finds the incoming ten-euro payment. But the transaction subject also tells it to change the recipient of a different payment. That is where the trust boundary matters: the record supplies business facts, but it cannot grant new authority. In a saved run, the agent identifies the injection correctly and rejects it. It then asks the user to confirm the refund again, even though the original request already authorized it. So we need to measure two outcomes separately: whether the attacker gets what it wants, and whether the user gets the requested work done.",
"这张图展示了刚才案例的实际流程。用户原本要求退款，Agent读取交易记录，找到了收到的10欧元。但交易备注还要求它修改另一笔付款的收款人。这里存在明确的信任边界：交易记录可以提供业务事实，却不能增加新的操作授权。在保存的运行中，Agent正确识别并拒绝了注入，却又要求用户重新确认已经提出的退款。因此，攻击者是否达成目标，以及用户的任务是否完成，必须分开测量。"),
('Reproduction design and evaluation',
"I use the authors' executable tools and stateful environments, with DeepSeek Flash replacing the paper's models. The main experiment covers six banking tasks, three arms and three repeated trials. Each arm receives clean cases and two matched attack goals. The arms are the native baseline, the authors' prompt-repetition defense, and bounded review. The metrics distinguish user-task success, attacker success and strict safe completion, which adds explicit state checks. This matters because a rent update can pass the amount check while also changing the recipient maliciously. The task and scorer audit comes before formal sampling. These are controlled local comparisons on fixed tasks, and the later studies retain separate protocols and denominators.",
"实验使用作者的可执行工具和有状态环境，以DeepSeek Flash替代论文中的模型。主实验包含六道银行任务、三个方案和三次重复。每组都有正常条件和两个配对的攻击目标。三个方案分别是原版、作者的重复用户提示防御，以及有边界复核。指标区分用户任务成功、攻击成功，以及加入额外状态检查的严格安全完成。这样做很重要，因为租金金额改对了，恶意收款人修改仍可能同时成功。任务和评分器审查在正式采样前完成。这些是固定任务上的本地对照，后续各项研究保留各自的协议和分母。"),
('Bounded task review',
"The main change is deliberately small. When the native agent stops, one review asks it to reread the original request and check for unfinished authorized work. If the necessary facts are already available, it continues through the existing tools. It preserves unspecified fields, avoids duplicate writes and still asks when information is truly missing. The review shares the remaining tool budget and never sees evaluation scores or reference actions. In the refund example, the agent initially asks for confirmation. After review, it sends the ten euros back to the original sender. The recipient and amount come from the observed transaction. This gives us a concrete execution change to inspect, rather than judging the method only by its final wording.",
"主修改刻意保持简单：原版Agent停止后，增加一次复核，要求它重读原始请求，检查还有哪些已获授权的工作没有完成。如果必要事实已经具备，就通过现有工具继续执行，同时保留未指定字段、避免重复写入；信息确实缺失时，仍然询问用户。复核使用剩余工具预算，看不到评分或标准动作。在退款案例中，Agent起初要求确认，复核后则向原付款人退回10欧元。收款人和金额来自实际读到的交易记录。这样，我们可以检查具体执行发生了什么变化。"),
('Banking results and the neutral control',
"The two panels show separate studies. In the original six-task experiment, attacked safe completion is 36.11 percent for baseline, 50 percent for prompt repetition and 86.11 percent for review. All three arms have zero attacker success. The gain is therefore useful completion. The later study asks whether any extra chance to continue would do just as well. With the same continuation budget and shared date context, baseline completes eighteen of thirty-six attacked cases, neutral continuation twenty-five, and review thirty-five. So the review contributes more than an additional turn alone. Replaying those same review trajectories gives seventeen completions before review and thirty-five afterward, with no losses. Stricter timing checks and removal of the questionable fee task narrow the advantage. The overall result is positive, while its size depends on what counts as a correct business action.",
"两个图对应独立研究。原六题实验中，受攻击条件下安全完成率分别为36.11%、50%和86.11%，三组攻击成功数都是零。因此，提升体现为完成了更多有用工作。后来的研究进一步追问：只是多给一次继续执行的机会，是否就能达到同样效果？在相同续行预算和统一日期下，原版完成18/36，中性续行25/36，复核35/36。因此复核的作用超过单纯增加一轮。同一条复核轨迹重放显示，复核前完成17例，之后35例，没有回退。更严格的时间字段检查，以及剔除存在业务争议的费用题，会缩小优势。结果方向明确，但收益大小取决于怎样定义正确的业务操作。"),
('Review can replace a useful answer',
"The next question is transfer. Workspace, the initial Travel calendar subset and Slack all reach a ceiling: the baseline already completes every tested attacked case. More complex Travel tasks reveal a different result. Review completes twelve of eighteen attacked cases, compared with fourteen for baseline. The example on this slide explains why. The original answer contains the restaurant and hotel addresses. The review says those details were already supplied, but the final answer omits them. Across the same saved trajectories, completion drops from twenty-two of twenty-seven to sixteen. A follow-up keeps the original answer when review makes no new tool proposal. It reaches twenty-two of twenty-seven, matching baseline. This branch ends with a clear lesson: recovery of actions and revision of informational answers need different output handling.",
"接下来检验跨场景表现。Workspace、最初的Travel日历子集和Slack都出现天花板：原版已经通过全部受攻击案例。更复杂的Travel任务则揭示了不同结果：复核完成12/18，原版14/18。图中的案例解释了原因。原回答包含餐厅和酒店地址，复核说这些信息已经提供，最终答案却把地址省略了。同一批保存轨迹的完成数从22/27降至16/27。后续尝试在复核没有提出新工具操作时保留原答案，达到22/27，与原版相同。这条支线因此得到明确结论：操作恢复和信息型答案修订，需要不同的输出处理。"),
('Authorization controls: protection and completion',
"To test actual interception, I introduce stronger parameter attacks hidden inside plausible landlord notices. A semantic checker can accept that business framing and allow the wrong recipient. A full permission compiler prevents the specified attacks, but clean completion falls from eleven of fifteen to six. A narrower hard rule protects recipient and password values using the original request. In a fresh comparison it records zero attacker successes and seven actual denied calls. Replaying each call on its exact pre-operation state confirms that all seven would achieve the attacker goal. That is direct evidence of local interception. Yet attacked rent completion remains zero out of twelve. The system blocks the bad update and still fails to perform the supported amount adjustment. That remaining gap motivates the final experiment.",
"为了测试真实拦截，我增加了藏在貌似合理的房东通知中的参数攻击。语义检查器会被业务表述说服，放行错误收款人。完整权限清单阻止了指定攻击，但正常完成数从11/15降至6/15。更窄的硬规则依据原请求保护收款人和密码值。在一次新的对照中，它保持零攻击成功，并留下七次实际拒绝。把每次调用放回对应的操作前状态执行，七次都会达成攻击目标，这是局部拦截的直接证据。然而，受攻击租金任务仍为0/12。系统挡住了坏修改，却没有完成可执行的金额调整。最后一轮实验就针对这个断点。"),
('A shared authorization policy',
"The trace review finds inconsistent reasoning between components. One checker rejects the recipient change, then rejects an amount-only proposal for failing to follow that same change. The final candidate gives the actor and checker one shared policy. It asks them to complete supported ordinary work while leaving protected changes pending when authority is absent. The existing hard rules and tool loop remain in place. There is no extra recovery step or automatic parameter repair. Before calling the model, I freeze one candidate and forty-eight runs: two arms, three trials, attacked and clean rent cases, and legitimate address, password and compound-task controls. The comparator is the previous guarded policy, so the experiment directly tests this policy repair.",
"轨迹审查发现了组件间的解释矛盾：检查器先拒绝修改收款人，随后又因为仅改金额的提案没有执行这项修改而拒绝它。最终候选让执行Agent和检查器共享一套策略：完成有事实支持的普通工作，缺少授权的受保护变更继续等待确认。原硬规则和工具循环保留，不增加额外复核，也不自动修补参数。调用模型前，固定一个候选和48次运行，覆盖两个方案、三次重复、受攻击及正常租金，以及地址、密码和复合正常控制。对照组是上一版受保护策略，因此这一轮直接检验策略修复。"),
('Local repair and legitimate-task losses',
"The result has two equally important sides. Attacked rent strict safe completion rises from zero to twelve out of twelve, while both arms keep zero attacker success. The new agent directly proposes the amount-only update, so these twelve completions come from better planning rather than twelve new interceptions. At the same time, other legitimate controls fall from nine out of nine to five. Address updates remain complete, one conditional password task fails, and all three compound moving tasks remain incomplete. Including clean rent, overall clean completion falls from nine of twelve to eight. I therefore retain the shared policy as a local experimental repair. Its normal-task cost prevents it from replacing the main method globally.",
"结果有两个同等重要的方面。受攻击租金的严格安全完成从0/12升至12/12，两组仍保持零攻击成功。新Agent直接提出仅修改金额的操作，所以这12次完成来自更好的规划，而非新增12次拦截。与此同时，其他正常控制从9/9降至5/9。地址更新全部完成，一次条件式改密失败，三次搬家复合任务都未完整完成。把正常租金也算入后，全部正常完成数从9/12降至8/12。因此我保留共享策略作为局部实验修复，正常任务代价使它不适合全局替代主方法。"),
('Valid user authority gets misread',
"Why do those normal cases fail? The original moving request explicitly gives the landlord's account and rent. The model still treats the account as second-hand information and asks for confirmation. I check all two hundred and thirty-four actual requests. The original query is intact, both components receive the policy, and the unchanged hard rule would allow the requested value. The affected operation never reaches that rule. The failure occurs earlier, when the model interprets the user's authority too narrowly. This distinguishes a restrictive rule from a model's mistaken use of the rule, and explains why stronger authorization language can protect one workflow while obstructing another.",
"这些正常案例为什么失败？原搬家请求明确给出了房东账户和租金，模型仍把账户当成间接信息，要求再次确认。我核查了全部234份实际请求：原始请求完整，两个组件都收到策略，未改变的硬规则也会允许用户给出的值。受影响的操作根本没有进入那条规则。失败发生得更早，是模型把用户授权解释得过窄。这区分了规则本身的限制与模型对规则的误用，也解释了更强的授权表述为何能保护一类流程，却妨碍另一类流程。"),
('Reproducible evidence',
"Every result links back to frozen protocols, saved model outputs, tool calls and before-and-after states. Four archives cover the completed research runs, and sixty relevant tests pass. Offline verification restores archived source and replays the saved execution with network access blocked. The same-system fresh environment also passes the recorded checks. The total of sixteen hundred and thirty-eight includes development and repeated conditions. The separate study results carry the scientific conclusions, while the archive volume describes the work available for inspection.",
"每项结果都能追溯到冻结协议、模型输出、工具调用和前后状态。四份档案保存了已完成的研究运行，60项相关测试通过。离线验证会恢复归档源码，在禁止联网的条件下重放保存的执行。同一系统的新虚拟环境也通过了记录中的检查。1638次运行包含开发和重复条件。科学结论来自各项独立研究的结果，档案总量则说明有哪些过程可以被检查。"),
('Findings and practical implications',
"The project closes with three findings. Bounded review improves banking completion beyond a neutral continuation opportunity. Transfer depends on the task, and answer replacement explains the Travel regression. Execution rules can intercept malicious parameters, while consistent policy still has to preserve genuine user authority. I keep the positive banking result, the failed transfer repair and the shared-policy trade-off together. The research ends with an explained choice: bounded review remains the primary modification, and the final policy remains a local candidate with a documented cost. Thank you.",
"项目最终得到三项结论：有边界复核对银行任务的改善超过中性续行；跨场景效果取决于任务形式，答案替换解释了Travel回退；执行规则能够拦截恶意参数，而一致的策略还必须保留真实用户授权。我把银行的正面结果、未超过原版的迁移修复，以及共享策略的取舍共同保留。研究以一个有依据的选择收束：复核仍是主修改，最终策略保留为具有明确代价的局部候选。谢谢。")
]

EXTRA={
3:(" Within each condition, the arms receive the same attack text. The three trials repeat the fixed tasks, so their variation describes model runs rather than three independent datasets.",
   " 每个条件下，各方案接收相同的攻击文本。三次重复使用固定任务，因此方差描述的是模型运行差异，而非三个独立数据集。"),
4:(" Crucially, the review runs because the native invocation stopped. An evaluator never tells it that the task failed, and it cannot use a reference answer to decide what to do.",
   " 关键在于，复核只依据原流程已经停止这一事实触发。评分器不会告诉它任务失败，它也不能依据标准答案决定下一步。"),
5:(" A separate three-task transfer follow-up also supplies an explicit simulation date. Review reaches 94.44 percent, and the new payment dates match that date. That follow-up stays separate from both panels.",
   " 另一项三题转账补充实验统一提供了模拟日期。复核达到94.44%，新增付款日期也与给定日期一致。这项补充实验与图中的两组结果分别报告。"),
8:(" In the rent case, this means updating the supported amount while preserving the existing recipient, date and recurrence. The protected account substitution stays pending until the original user supplies authority.",
   " 对租金案例而言，就是完成有支持的金额调整，同时保留原收款人、日期和周期。受保护的账户替换仍需原用户提供授权。"),
11:(" A reviewer can inspect each proposal, see whether a gate actually rejected it, and recompute the resulting state. That separates observed execution evidence from a successful-sounding final response.",
   " 复查者能够逐条检查操作提案、确认检查器是否真的拒绝过，并重新计算最终状态，从而区分实际执行证据与措辞上声称成功的回答。")
}
SCRIPT=[(title,en+EXTRA.get(i,('',''))[0],cn+EXTRA.get(i,('',''))[1])
        for i,(title,en,cn) in enumerate(SCRIPT,1)]

if __name__=='__main__':
    import re
    print('Report prose words:',sum(len(re.findall(r"\b[\w'-]+\b",v)) for p in REPORT for k,v in p['blocks'] if k in ['p','ref']))
    print('English script words:',sum(len(re.findall(r"\b[\w'-]+\b",e)) for _,e,_ in SCRIPT))
