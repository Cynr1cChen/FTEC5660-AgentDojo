# FTEC5660: AgentDojo reproducibility project

选题已确定为 AgentDojo。当前已完成环境准备和 6 次真实 DeepSeek 开发运行，用于费用校准；尚未完成正式基线或防御评测。费用见 [COST_ESTIMATE.md](COST_ESTIMATE.md)。

## 当前范围

- 主场景：banking；benchmark 显式固定为 `v1.2.2`。
- 上游提交：`089ed468cf3ed0322acc66b0211f26d9d90dbf60`；本地分支：`course-project`。
- 模型提供商：DeepSeek 官方 API；首轮默认 `deepseek-flash`、非思考模式。
- 复现目标：测量工具调用 Agent 在无注入／有注入情况下的任务完成与攻击成功行为。
- 主要修改候选：执行有外部影响的工具调用前，检查行动及参数是否与用户任务一致。先完成基线诊断，再锁定设计。

论文模型与当前模型不同，benchmark 也包含后续修订，结果不与原论文数字直接等同。首轮 3 个用户任务、2 个攻击目标仅为开发试跑，不能当作正式结论。

## 目录

| 路径 | 用途 |
|---|---|
| `PROJECT_PLAN.md` | 研究问题、阶段任务和验收条件 |
| `DEBUG_DIARY.md` | 环境问题、证据和处理记录 |
| `pilot_config.json` | 明确限定的首轮试跑配置 |
| `deepseek_adapter.py` | DeepSeek 接口兼容、usage 与费用估算 |
| `prepare.py` | 无 API 的参考执行、任务目录与攻击生成检查 |
| `run_pilot.py` | 使用上游评测器的真实小样本运行入口 |
| `requirements.lock.txt` | 本机实际安装版本，包含可编辑安装 `-e .` |
| `artifacts/` | 离线检查记录；这些不是模型复现成绩 |
| `presentation_assets/` | 真实案例配图、来源快照与后续汇报素材清单 |
| `../runs/course_project/` | 真实 API 运行的独立日志目录 |

## 环境

本机已创建 `.venv`，使用 Python 3.12.14，无需本地 GPU。后续命令从仓库根目录执行。

在其他电脑重建时：

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r course_project/requirements.lock.txt
```

版本文件记录 macOS arm64 上已验证的版本；其他平台仍需重新验证。使用 pip 时，在激活的虚拟环境内执行 `pip install -r course_project/requirements.lock.txt`。

## 配置 DeepSeek

仓库根目录已有本地 `.env`，已被 Git 忽略。在编辑器内填写：

```dotenv
DEEPSEEK_API_KEY=你的实际密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-flash
```

只在本机填写，不粘贴到聊天、README 或提交。`.env.example` 为不含密钥的模板。这里假定使用 DeepSeek 官方平台密钥；其他服务商的 DeepSeek 模型需单独核查。

当前 API 文档列出的模型为 `deepseek-flash` 和 `deepseek-v4-pro`；首轮使用 Flash。明确关闭思考模式，以固定实验条件，并避免额外的推理历史协议差异。此处是基础适配，所有对照条件共用，不作为新增防御贡献。

## 离线检查

```bash
.venv/bin/python -m course_project.prepare
.venv/bin/python -m pytest course_project/tests tests/test_task_injectability.py tests/test_agent_pipeline/test_prompting_llm.py tests/test_functions_runtime/test_functions_runtime.py tests/test_benchmark.py tests/test_workspace_user_tasks.py -q
```

离线流程使用作者提供的参考工具序列检查环境和评分器，不调用模型。测试中的假 API 响应仅验证接口和执行链，不能用于报告模型准确率。

## 真实首轮试跑

```bash
.venv/bin/python -m course_project.run_pilot
```

配置安排 2 次攻击目标能力检查、3 次无攻击任务、6 次有攻击任务，共 11 个 episode，单次试跑，不做随机性结论。每个 episode 在新的模拟环境中运行。

本地限制为最多 100 次 API 请求、每次最多 2,048 个输出 token、峰值费率估算 2 元的首轮预算。累计运行日志也会检查 100 元项目预算。费用估算按 2026-11-01 官方人民币峰值费率、无缓存折扣计算，未将本地模拟工具计为 DeepSeek 搜索服务；这些估算不是平台硬限额，最终扣费以控制台为准。客户端自动重试关闭，基础设施错误会停止本轮并单独标记。

每轮保留 `manifest.json`、`usage.jsonl`、`episodes.jsonl`、`summary.json` 与逐任务对话轨迹。请求模型、实际返回模型、token 用量、参数、耗时均记录；API Key 和请求头不记录。每轮使用新的目录，避免误将缓存重放当作新试验。

注意上游的 `security` 字段在攻击评测中代表**攻击目标是否成功**，并非“系统是否安全”。本入口显式转为 `attack_success`；正常任务中的占位值不用于计算攻击成功率。接口错误和未运行任务的攻击结果保持未知。

## 基线完成后的决定

检查正常任务是否可完成、攻击是否实际进入模型读取的数据、攻击目标是否能作为直接用户请求执行，以及是否存在可分析的成功／失败轨迹。之后固定正式数据范围和 3–5 次重复试验配置，再实现一个主要防御修改。

最终提交仍需报告、包含清晰提交历史的 GitHub 仓库、Zoom 录屏链接。当前代码和离线检查只是这些成果的基础。

## 官方来源

- [AgentDojo 论文](https://proceedings.nips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html)
- [AgentDojo 执行流程](https://agentdojo.spylab.ai/concepts/agent_pipeline/)
- [DeepSeek 工具调用](https://api-docs.deepseek.com/guides/tool_calls/)
- [DeepSeek 思考模式](https://api-docs.deepseek.com/guides/thinking_mode/)
- [DeepSeek 模型与人民币价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)
