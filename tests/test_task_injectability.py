import pytest

from agentdojo.task_suite.task_suite import is_task_injectable


@pytest.mark.parametrize("content", ["prefix CANARY suffix", [{"type": "text", "content": "prefix CANARY suffix"}]])
def test_injectability_supports_legacy_and_current_messages(content):
    assert is_task_injectable([{"role": "tool", "content": content}], ["CANARY"])


def test_injectability_does_not_count_user_or_assistant_text():
    assert not is_task_injectable([
        {"role": "user", "content": [{"type": "text", "content": "CANARY"}]},
        {"role": "assistant", "content": [{"type": "text", "content": "CANARY"}]},
        {"role": "tool", "content": None},
    ], ["CANARY"])
