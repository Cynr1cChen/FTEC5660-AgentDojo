"""Inspect real task definitions and ground-truth executability without an LLM."""

import hashlib
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path
from types import SimpleNamespace

from agentdojo.attacks import load_attack
from agentdojo.models import MODEL_NAMES
from agentdojo.task_suite.load_suites import get_suite

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_COMMIT = "089ed468cf3ed0322acc66b0211f26d9d90dbf60"
CONFIG_PATH = ROOT / "course_project/pilot_config.json"


def load_config(path=CONFIG_PATH):
    return json.loads(Path(path).read_text())


def environment_metadata():
    return {
        "upstream_url": "https://github.com/ethz-spylab/agentdojo",
        "upstream_commit": UPSTREAM_COMMIT,
        "working_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": {name: importlib.metadata.version(name)
                     for name in ("agentdojo", "openai", "pydantic", "pytest")},
    }


def prepare():
    config = load_config()
    report = {"kind": "offline_setup_validation_not_model_reproduction",
              "environment": environment_metadata(), "config": config, "suites": {}}
    for name in ("banking", "workspace"):
        suite = get_suite(config["benchmark_version"], name)
        ok, (users, injections) = suite.check(check_injectable=True)
        report["suites"][name] = {
            "user_task_count": len(suite.user_tasks),
            "injection_task_count": len(suite.injection_tasks),
            "tool_count": len(suite.tools),
            "ground_truth_checks_passed": ok,
            "user_task_checks": users,
            "injection_task_checks": injections,
            "user_tasks": [{"id": task.ID, "prompt": task.PROMPT,
                            "reference_tool_names": [call.function for call in task.ground_truth(
                                task.init_environment(suite.load_and_inject_default_environment({})))]}
                           for task in suite.user_tasks.values()],
            "tools": [tool.name for tool in suite.tools],
        }
    suite_dir = ROOT / "src/agentdojo/data/suites" / config["suite"]
    report["data_file_sha256"] = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(suite_dir.rglob("*.yaml"))
    }
    suite = get_suite(config["benchmark_version"], config["suite"])
    MODEL_NAMES["deepseek-flash"] = "DeepSeek"
    attack = load_attack(config["attack"], suite, SimpleNamespace(name="deepseek-flash"))
    report["pilot_attack_generation"] = []
    for user_id in config["user_tasks"]:
        for injection_id in config["injection_tasks"]:
            payload = attack.attack(suite.get_user_task_by_id(user_id),
                                    suite.get_injection_task_by_id(injection_id))
            report["pilot_attack_generation"].append({
                "user_task": user_id, "injection_task": injection_id,
                "injection_vectors": sorted(payload),
                "payload_sha256": hashlib.sha256(json.dumps(
                    payload, sort_keys=True).encode()).hexdigest(),
            })
    target = ROOT / "course_project/artifacts/offline_setup.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"report": str(target), "checks": {
        name: {key: value for key, value in details.items()
               if key.endswith("count") or key == "ground_truth_checks_passed"}
        for name, details in report["suites"].items()}}, indent=2))


if __name__ == "__main__":
    prepare()
