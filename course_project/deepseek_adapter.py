"""DeepSeek protocol adapter; this is setup, not the experimental defense.

Preserves AgentDojo's prompts, tools, parser and runtime. Uses system roles,
plain-text message content and explicitly disabled thinking for compatibility.
"""

import json
import time
from pathlib import Path

from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement
from agentdojo.agent_pipeline.llms.openai_llm import (
    _function_to_openai,
    _openai_to_assistant_message,
    _tool_call_to_openai,
)
from agentdojo.functions_runtime import EmptyEnv
from agentdojo.types import get_text_content_as_str

# CNY / million tokens, conservative peak rates without cache discounts.
# Checked 2026-11-01: https://api-docs.deepseek.com/zh-cn/quick_start/pricing/
RATES = {"deepseek-flash": (2.0, 8.0), "deepseek-v4-pro": (9.0, 27.0)}


class BudgetExceeded(RuntimeError):
    pass


def serialize_messages(messages):
    result = []
    for message in messages:
        content = message["content"]
        text = get_text_content_as_str(content) if content is not None else None
        item = {"role": message["role"], "content": text}
        if message["role"] == "assistant" and message.get("tool_calls"):
            item["tool_calls"] = [_tool_call_to_openai(call) for call in message["tool_calls"]]
        elif message["role"] == "tool":
            if not message["tool_call_id"]:
                raise ValueError("Tool result is missing tool_call_id")
            item["tool_call_id"] = message["tool_call_id"]
            item["content"] = message.get("error") or text or ""
        elif message["role"] in ("system", "user"):
            item["content"] = text or ""
        result.append(item)
    return result


class DeepSeekLLM(BasePipelineElement):
    def __init__(self, client, model, config, usage_path=None, previous_cost_cny=0.0):
        if model not in RATES:
            raise ValueError("Unknown model pricing; configure a supported model before running")
        self.client = client
        self.model = model
        self.name = model
        self.config = config
        self.usage_path = Path(usage_path) if usage_path else None
        self.previous_cost_cny = previous_cost_cny
        self.records = []
        self.context = {}

    @property
    def estimated_cost_cny(self):
        return sum(record["estimated_cost_cny"] for record in self.records)

    def query(self, query, runtime, env=EmptyEnv(), messages=(), extra_args=None):
        wire_messages = serialize_messages(messages)
        tools = [_function_to_openai(tool) for tool in runtime.functions.values()]
        input_rate, output_rate = RATES[self.model]
        # Byte length plus per-message overhead is deliberately conservative.
        # This is a local estimate, not a provider-enforced spending limit.
        estimated_input_bound = len(json.dumps(
            {"messages": wire_messages, "tools": tools}, ensure_ascii=False
        ).encode("utf-8")) + 64 * len(wire_messages) + 512
        reserve = (estimated_input_bound * input_rate +
                   self.config["max_output_tokens"] * output_rate) / 1_000_000
        if len(self.records) >= self.config["max_api_calls"]:
            raise BudgetExceeded("Pilot API call limit reached")
        if self.estimated_cost_cny + reserve > self.config["run_budget_cny"]:
            raise BudgetExceeded("Pilot estimated spending limit reached")
        if self.previous_cost_cny + self.estimated_cost_cny + reserve > self.config.get("project_budget_cny", 100):
            raise BudgetExceeded("Project estimated spending limit reached")

        request = {
            "model": self.model,
            "messages": wire_messages,
            "max_tokens": self.config["max_output_tokens"],
            "temperature": self.config["temperature"],
            "extra_body": {"thinking": {"type": "disabled"}},
        }
        if tools:
            request.update(tools=tools, tool_choice="auto")
        started = time.monotonic()
        record = {
            **self.context, "model_requested": self.model,
            "thinking": "disabled", "status": "error",
            "estimated_cost_cny": reserve,
            "estimate_basis": "conservative reservation; usage unavailable",
        }
        try:
            completion = self.client.chat.completions.create(**request)
            record["model_returned"] = completion.model
            record["response_id"] = completion.id
            record["system_fingerprint"] = getattr(completion, "system_fingerprint", None)
            usage = completion.usage
            if usage is None:
                raise ValueError("API returned no token usage; stop rather than undercount spending")
            record["usage"] = usage.model_dump()
            record["estimated_cost_cny"] = (
                usage.prompt_tokens * input_rate + usage.completion_tokens * output_rate
            ) / 1_000_000
            record["estimate_basis"] = "reported tokens at recorded peak rates, no cache discount"
            choice = completion.choices[0]
            record["finish_reason"] = choice.finish_reason
            if choice.finish_reason not in ("stop", "tool_calls"):
                raise ValueError("Generation did not finish normally")
            output = _openai_to_assistant_message(choice.message)
            record["status"] = "ok"
        except Exception as exc:
            # Do not persist exception bodies, headers or credentials.
            record["error_type"] = type(exc).__name__
            record["http_status"] = getattr(exc, "status_code", None)
            raise
        finally:
            record["duration_seconds"] = time.monotonic() - started
            self.records.append(record)
            if self.usage_path:
                with self.usage_path.open("a") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        return query, runtime, env, [*messages, output], extra_args or {}
