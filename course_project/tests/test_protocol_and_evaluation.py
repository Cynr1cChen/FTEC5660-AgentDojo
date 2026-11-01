import copy
from types import SimpleNamespace

import pytest

from agentdojo.functions_runtime import FunctionCall
from agentdojo.task_suite.load_suites import get_suite
from course_project.deepseek_adapter import BudgetExceeded, DeepSeekLLM, serialize_messages
from course_project.prepare import load_config
from course_project.run_pilot import build_pipeline, summarize


def block(text):
    return [{"type": "text", "content": text}]


def completion(content=None, tool=None):
    calls = None
    if tool:
        import json
        name, args, call_id = tool
        calls = [SimpleNamespace(id=call_id, function=SimpleNamespace(
            name=name, arguments=json.dumps(args)))]
    usage = SimpleNamespace(prompt_tokens=100, completion_tokens=20,
                            model_dump=lambda: {"prompt_tokens": 100, "completion_tokens": 20})
    return SimpleNamespace(
        id="offline-response", model="deepseek-flash", usage=usage,
        choices=[SimpleNamespace(finish_reason="tool_calls" if tool else "stop",
                                 message=SimpleNamespace(content=content, tool_calls=calls))],
    )


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.requests = []
        self.chat = SimpleNamespace(completions=self)

    def create(self, **request):
        self.requests.append(copy.deepcopy(request))
        return next(self.responses)


def test_system_role_and_tool_call_round_trip():
    messages = [
        {"role": "system", "content": block("Original instructions")},
        {"role": "assistant", "content": None,
         "tool_calls": [FunctionCall(function="read_file", args={"file_path": "bill.txt"}, id="call-1")]},
        {"role": "tool", "content": block("Bill data"), "error": None,
         "tool_call_id": "call-1"},
    ]
    wire = serialize_messages(messages)
    assert wire[0] == {"role": "system", "content": "Original instructions"}
    assert wire[1]["tool_calls"][0]["id"] == wire[2]["tool_call_id"]
    assert wire[2]["content"] == "Bill data"


def test_missing_tool_call_id_is_rejected_before_request():
    with pytest.raises(ValueError):
        serialize_messages([{"role": "tool", "content": block("result"),
                             "tool_call_id": None, "error": None}])


def test_full_simulated_banking_tool_cycle_and_usage():
    # The API is entirely fake here; the real AgentDojo tools and grader execute.
    # This validates the adapter, not model capability or reproduction accuracy.
    client = FakeClient([
        completion(tool=("read_file", {"file_path": "bill-december-2023.txt"}, "call-1")),
        completion(tool=("send_money", {
            "recipient": "UK12345678901234567890", "amount": 98.70,
            "subject": "Car Rental", "date": "2022-01-01"}, "call-2")),
        completion("The bill has been paid."),
    ])
    config = load_config()
    llm = DeepSeekLLM(client, "deepseek-flash", config)
    pipeline = build_pipeline(llm, "none", config["max_tool_rounds"])
    suite = get_suite("v1.2.2", "banking")
    utility, _ = suite.run_task_with_pipeline(
        pipeline, suite.get_user_task_by_id("user_task_0"), None, {})
    assert utility is True
    assert len(client.requests) == 3
    assert client.requests[0]["messages"][0]["role"] == "system"
    assert all(request["extra_body"] == {"thinking": {"type": "disabled"}}
               for request in client.requests)
    assert client.requests[1]["messages"][-1]["tool_call_id"] == "call-1"
    assert client.requests[2]["messages"][-1]["tool_call_id"] == "call-2"
    assert llm.estimated_cost_cny == pytest.approx(3 * (100 * 2 + 20 * 8) / 1_000_000)


def test_budget_stops_before_any_network_request():
    client = FakeClient([])
    config = load_config()
    config["run_budget_cny"] = 0
    llm = DeepSeekLLM(client, "deepseek-flash", config)
    from agentdojo.functions_runtime import FunctionsRuntime
    with pytest.raises(BudgetExceeded):
        llm.query("question", FunctionsRuntime([]), messages=[
            {"role": "user", "content": block("question")}])
    assert client.requests == []


def test_incomplete_episode_is_not_counted_as_a_successful_defense():
    rows = [
        {"defense": "none", "phase": "clean", "status": "completed",
         "utility": True, "attack_success": None},
        {"defense": "none", "phase": "attacked", "status": "error",
         "utility": None, "attack_success": None},
        {"defense": "none", "phase": "attacked", "status": "completed",
         "utility": True, "attack_success": True},
    ]
    summary = summarize(rows)["none"]
    assert summary["clean_utility_including_incomplete_as_unsolved"] == 1
    assert summary["attack_success_rate_completed_only"] == 1
    assert summary["safe_completion_rate_completed_only"] == 0
    assert summary["incomplete_attack_outcomes_unknown"] == 1
