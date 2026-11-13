"""A continuous spoken narrative, with deliberately written paragraph boundaries."""
from textwrap import dedent

def speech(text):
    return dedent(text).strip()

SCRIPT=[
('Reproducing AgentDojo',speech('''
Let me start with a simple situation. You ask an assistant to refund a payment, and it notices a malicious instruction hidden in the transaction record. It refuses that instruction, which sounds like a successful defense. But then it stops, and your refund never happens.

That gap is what led me to this project. Using AgentDojo, I investigated whether one bounded review could help the agent finish the legitimate task, and then followed the results to understand where that approach breaks down.
'''),speech('''
我想先从一个很简单的情境说起。你让一个助手退回一笔款项，它发现交易记录里藏着恶意指令，于是拒绝执行。听起来，防御已经成功了。但接下来，它却停住了，你要的退款也没有完成。

正是这个断点，让我开始了这项研究。我以AgentDojo为基础，检验增加一次有边界的复核，能否帮助Agent继续完成合法任务，再沿着实验结果，追问这种做法会在什么地方失效。
''')),
('A refund, an injection and an unfinished task',speech('''
If we follow the example on the left, the agent finds an incoming ten-euro payment, just as the user requested. The problem is that the same record also tells it to change the recipient of another payment.

The diagram on the right shows the distinction it needs to make. Transaction data can tell the agent how much arrived and who sent it, but it cannot authorize an unrelated account change. In the saved run, the agent understands that distinction well enough to reject the injection. Yet it then asks the user to confirm the refund again.

So, throughout the experiments, I kept two questions separate: did the attacker succeed, and did the agent actually finish the user's task? Here's how I measured them.
'''),speech('''
顺着左边的例子看，Agent按照用户的请求，找到了收到的10欧元。问题在于，同一条记录还要求它修改另一笔付款的收款人。

右边的图展示了它必须分清的两件事：交易数据可以告诉它收到了多少钱、是谁付的，却不能授权它修改无关账户。在保存的运行中，Agent确实分清了这一点，也拒绝了注入；但随后，它又要求用户重新确认退款。

因此，在整个实验中，我始终分开考察两个问题：攻击者有没有成功，以及Agent有没有真正完成用户的任务。接下来，我先说明怎样测量这两件事。
''')),
('Reproduction design and evaluation',speech('''
I started with the authors' executable tools and stateful environments, replacing the original models with DeepSeek Flash. For the main comparison, I used six banking tasks and three approaches: the native agent, the authors' prompt-repetition defense, and my bounded review. Each approach faced clean cases and two matched attack goals, with three repeated trials and identical attack text within each condition.

Before running that comparison, though, I checked what the scores actually meant. A rent update, for example, can pass the amount check even if the agent also changes the recipient maliciously. That's why I measured user-task success and attacker success separately, then added explicit state checks for strict safe completion.

With those measurements in place, I could test a small change to the workflow.
'''),speech('''
我先使用作者提供的可执行工具和有状态环境，把原模型替换为DeepSeek Flash。主对照实验选取六道银行任务，比较原版Agent、作者的重复用户提示防御，以及我加入的有边界复核。每个方案都有正常条件和两个配对的攻击目标，各重复三次；同一条件下，各方案接收相同的攻击文本。

不过，在正式运行前，我先检查了这些分数到底代表什么。比如，一次租金修改可能通过金额检查，但Agent同时也恶意修改了收款人。因此，我把用户任务成功与攻击成功分开统计，再加入明确的状态检查，得到严格安全完成指标。

有了这套测量方式，接下来就可以检验工作流程中的一个小改动。
''')),
('Bounded task review',speech('''
The change is to add one review when the native agent stops. At that point, the agent rereads the original request and checks whether any authorized work remains unfinished. If the facts are already available, it continues through the existing tools. If something essential is genuinely missing, it can still ask the user.

Importantly, this uses the remaining tool budget rather than starting a new one. It also asks the agent to preserve unspecified fields and avoid repeating completed writes, without giving it scores or reference answers.

Now, remember the refund. Before review, the agent asks for confirmation. After review, it sends the ten euros back to the original sender using the transaction it already found. That gives us a concrete example of recovery. The next step was to see whether it happened consistently.
'''),speech('''
这个改动，就是在原版Agent停止时增加一次复核。到了这一步，Agent会重读原始请求，检查是否还有已经获得授权、却没有完成的工作。如果必要事实已经具备，就通过现有工具继续执行；如果确实缺少关键资料，仍然可以询问用户。

这里有一个重要约束：它使用剩余的工具预算，而不是重新获得一套预算。同时，提示要求它保留未指定字段，避免重复已经完成的写操作，也不会向它提供评分或标准答案。

再回到刚才的退款例子。复核前，Agent要求确认；复核后，它依据已经找到的交易，向原付款人退回了10欧元。这样，我们就有了一个具体的任务恢复实例。接下来要检验的，是这种恢复能否稳定地出现在更多运行中。
''')),
('Banking results and the neutral control',speech('''
On the left, safe completion under attack rises from 36.11 percent for baseline to 86.11 percent for review, with prompt repetition at 50 percent. Since attacker success is zero in every arm, what improves here is completion of the user's work.

That raised a follow-up question: perhaps the agent simply needed another chance to continue. The separate study on the right tests that explanation. With the same continuation budget and date context, baseline completes eighteen of thirty-six attacked cases, neutral continuation twenty-five, and review thirty-five. So the review adds more than an extra turn alone. Replaying those same review trajectories also shows completion increasing from seventeen to thirty-five, with no losses.

Timing-preservation checks and excluding the questionable fee task narrow the advantage. A separate dated-transfer follow-up reaches 94.44 percent for review. Taken together, these results support the banking gain, but they also make the next question important: what happens outside banking?
'''),speech('''
先看左图。受攻击条件下，安全完成率从原版的36.11%提高到复核版的86.11%，重复提示防御则是50%。由于三组的攻击成功数都是零，这里的改善，具体体现为完成了更多用户要求的工作。

这也引出了一个后续问题：Agent会不会只是需要再多一次继续执行的机会？右边的独立研究就是用来检验这个解释的。在相同的续行预算和日期条件下，原版完成18/36，中性续行25/36，复核35/36。所以，复核的作用超过单纯增加一轮。对同一批复核轨迹进行重放，也能看到完成数从17例增加到35例，而且没有损失已经完成的任务。

要求保留时间字段、以及剔除存在业务争议的费用题后，优势会缩小。另一项统一日期的转账补充实验中，复核达到94.44%。合起来看，这些证据支持银行任务中的收益，也自然引出了下一个问题：离开银行场景以后，情况又会怎样？
''')),
('Review can replace a useful answer',speech('''
I first expanded to Workspace, Travel calendar tasks and Slack, but the baseline already passed every tested attacked case in those subsets. That left no room to demonstrate a gain, so I moved to more complex Travel tasks, where review actually performed worse: twelve of eighteen attacked cases completed, compared with fourteen for baseline.

The example shows what went wrong. The original answer includes both requested addresses. During review, however, the agent says it already provided those details and replaces the answer with a confirmation that omits them. Across those same review trajectories, completion falls from twenty-two of twenty-seven to sixteen.

Keeping the original answer when review proposes no new tool call avoids that replacement. In a fresh follow-up, it matches baseline at twenty-two of twenty-seven. This explains why action recovery and informational answers need different output handling.
'''),speech('''
我先把测试扩展到Workspace、Travel日历任务和Slack，但在这些子集中，原版已经通过全部受攻击案例，没有空间展示进一步提升。于是，我又选择了更复杂的Travel任务。这一次，复核反而表现更差：受攻击条件下完成12/18，而原版是14/18。

图中的例子说明了问题出在哪里。原回答本来包含用户要求的两个地址；但复核时，Agent认为自己已经给过这些细节，就把完整回答替换成了一段确认，结果地址反而被省略了。在同一批复核轨迹中，完成数因此从22/27降至16/27。

针对这个问题，我尝试在复核没有提出新工具调用时保留原答案。新的补充运行达到22/27，与原版相同。这样，这条支线就解释清楚了：操作恢复和信息型回答，需要不同的输出处理方式。
''')),
('Authorization controls: protection and completion',speech('''
Alongside that transfer question, I also wanted direct evidence that the system could intercept a malicious operation. For that, I used stronger attacks that disguised a recipient change as part of a landlord notice.

A semantic checker could still accept that business framing. Compiling a full permission list prevented the specified attacks, but clean completion fell from eleven of fifteen to six. I therefore tried narrower hard rules, checking protected recipient and password values against the original request.

In a fresh comparison, this produced zero attacker successes and seven actual hard denials after semantic approval. Replaying each denied call on its saved pre-operation state showed that all seven would achieve the attacker goal. That establishes local interception. But rent completion under attack remained zero out of twelve, so blocking the harmful update still wasn't enough to finish the task. That became the focus of the final experiment.
'''),speech('''
除了跨场景表现，我还希望获得直接证据，说明系统确实能够拦截恶意操作。为此，我使用了更强的攻击，把收款人修改伪装成房东通知中的正常业务要求。

语义检查器仍会接受这种业务表述。把允许的操作编译成完整权限清单，虽然阻止了指定攻击，但正常完成数也从11/15降至6/15。因此，我进一步尝试更窄的硬规则，依据原始请求检查受保护的收款人和密码值。

在一次新的对照中，这个方案保持零攻击成功，并且留下七次先通过语义检查、再被硬规则实际拒绝的调用。把每次调用放回对应的操作前状态执行，七次都会达成攻击目标。这就建立了局部拦截的直接证据。不过，受攻击租金任务仍然是0/12：挡住有害修改以后，任务还是没有完成。这个断点，就成了最后一轮实验的重点。
''')),
('A shared authorization policy',speech('''
Looking back through the rent traces, I found an inconsistency between components. A checker could reject the recipient change, then reject an amount-only update because it omitted that very change.

To address this, I gave the actor and checker one shared policy: complete supported ordinary work while leaving protected changes pending when authority is missing. For rent, that means adjusting the supported amount while preserving the recipient, date and recurrence. The hard rules and existing tool loop stay unchanged, with no additional recovery stage or automatic parameter repair.

I then froze one candidate and forty-eight runs, covering rent and legitimate address, password and compound-task controls over three trials. Here, the comparator is the previous guarded policy, which lets us examine this repair directly. Let's look at the result.
'''),speech('''
回过头检查租金轨迹时，我发现了组件之间的一处矛盾：检查器可能先拒绝修改收款人，随后又因为仅改金额的提案没有执行同一项收款人修改，而再次拒绝它。

针对这个问题，我让执行Agent和检查器共享同一套策略：完成有事实支持的普通工作，缺少授权的受保护变更则继续等待确认。对于租金案例，就是调整有支持的金额，同时保留收款人、日期和周期。原有硬规则和工具循环保留，不增加额外恢复步骤，也不自动修补参数。

随后，我固定了一个候选和48次运行，覆盖租金，以及地址、密码和复合正常控制，各重复三次。这里的对照组是上一版受保护策略，因此可以直接检验这项修复。接下来，我们一起看它的结果。
''')),
('Local repair and legitimate-task losses',speech('''
Starting with rent, the shared policy raises strict safe completion from zero to twelve out of twelve, while both arms retain zero attacker success. The agent now proposes the amount-only update directly, so the improvement comes from better planning, rather than twelve new interceptions.

However, the same policy reduces the other legitimate controls from nine of nine to five. Address updates still complete, but one conditional password case and all three compound moving cases fail to finish. Even after including the clean rent improvement, overall clean completion falls from nine of twelve to eight.

That combination led me to keep the shared policy as a local repair, rather than a global replacement. To understand the cost, though, we need to look more closely at how the agent interpreted the user's authority.
'''),speech('''
先看租金结果。共享策略把严格安全完成从0/12提高到12/12，同时两组仍保持零攻击成功。现在，Agent会直接提出仅修改金额的操作，因此，这里的改善来自更好的规划，而不是新增了12次拦截。

不过，同一套策略也把其他正常控制的完成数从9/9降到了5/9。地址更新依然全部完成，但一次条件式改密，以及三次搬家复合任务，都没有完整完成。即使算上正常租金的改善，全部正常条件的完成数仍从9/12降至8/12。

正是这组同时存在的收益和代价，让我决定把共享策略保留为局部修复，而不全局替换原方案。不过，要解释这项代价，还需要进一步看Agent到底怎样理解了用户的授权。
''')),
('Valid user authority gets misread',speech('''
Notice the original request on the left: the user explicitly supplies the new landlord's account and rent. Yet, on the right, the model treats that account as second-hand information and asks for confirmation again.

I checked all two hundred and thirty-four actual requests to find out whether information had gone missing. It hadn't: the original query was intact, both components received the policy, and the existing hard rule would allow the requested value. Instead, the model withheld the affected operation before the rule could evaluate it.

So the remaining failure was an overly narrow interpretation of genuine user authority. Distinguishing that from an actual tool rejection is exactly why I kept the request-level records, as well as the final scores.
'''),speech('''
请注意左边的原始请求：用户已经明确给出了新房东账户和租金。但看右边，模型却把这个账户当成间接信息，要求用户再次确认。

为了判断是不是信息在传输中丢失了，我核查了全部234份实际请求。结果表明，信息并没有丢失：原始请求完整，两个组件都收到了策略，现有硬规则也会允许用户要求的值。真正发生的是，模型在规则评估之前，就没有提出受影响的那项操作。

因此，剩余失败来自对真实用户授权的过窄解释。为了分清这种情况与真正的工具拒绝，我才会在最终分数之外，保留请求层面的完整记录。
''')),
('Reproducible evidence',speech('''
Those records also make the findings checkable. The four archives connect frozen protocols and saved model responses to actual tool calls and before-and-after states. Offline verification replays that execution with the network blocked, while sixty relevant tests and the recorded fresh-environment checks support the implementation.

The archives cover sixteen hundred and thirty-eight completed runs, including development and repeated conditions. Their value is that someone else can trace a result back to what the agent proposed, what a gate rejected and what actually changed.

That gave me a basis for bringing the project to a close with an explanation of both the gains and the failures.
'''),speech('''
这些记录，也让研究结论能够被复查。四份档案把冻结协议、保存的模型回答、实际工具调用和前后状态连接起来。离线验证会在禁止联网的条件下重放这些执行，另外还有60项相关测试和已经记录的新环境检查，支持实现本身的可靠性。

档案涵盖1638次完成运行，其中包括开发和重复条件。它们的价值在于，其他人能够从一个结果追溯回去，看清Agent提出了什么、检查器拒绝了什么，以及环境到底发生了什么变化。

有了这些依据，我就能够带着对收益和失败的解释，让整个项目形成收束。
''')),
('Findings and practical implications',speech('''
Putting it all together, bounded review improves the tested banking workflows beyond a neutral chance to continue. But the Travel result shows why I would treat informational answers differently: another review can remove details the user still needs.

The authorization experiments take that lesson further. Even when a rule intercepts malicious parameters, the agent still has to finish the allowed work and recognize authority the user genuinely supplied.

My final choice is therefore to retain bounded review as the main modification and document the shared policy as a local repair with a clear cost. The project closes with a measured improvement and an explanation of where it stops helping. Thank you.
'''),speech('''
把这些结果放在一起看，有边界复核对所测银行流程的改善，超过了单纯增加一次中性续行机会。不过，Travel结果也说明，信息型回答需要区别处理，因为再做一次复核，反而可能删掉用户仍然需要的细节。

授权实验又把这个认识推进了一步：即使规则能够拦截恶意参数，Agent仍然需要完成被允许的工作，也需要识别用户已经真实给出的授权。

因此，我最终保留有边界复核作为主要改动，把共享策略记录为具有明确代价的局部修复。这个项目以一个测量得到的改善，以及对它何时不再有效的解释，完成了闭环。谢谢。
''')),
]
