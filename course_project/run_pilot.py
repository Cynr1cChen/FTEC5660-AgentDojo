"""Small measured baseline using upstream evaluation and a DeepSeek adapter."""

import argparse
import hashlib
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv
from openai import OpenAI

from agentdojo.agent_pipeline.agent_pipeline import AgentPipeline, PipelineConfig
from agentdojo.agent_pipeline.tool_execution import ToolsExecutionLoop
from agentdojo.attacks import load_attack
from agentdojo.benchmark import run_task_with_injection_tasks, run_task_without_injection_tasks
from agentdojo.logging import NullLogger
from agentdojo.models import MODEL_NAMES
from agentdojo.task_suite.load_suites import get_suite

from course_project.deepseek_adapter import DeepSeekLLM
from course_project.prepare import CONFIG_PATH, ROOT, environment_metadata, load_config


def build_pipeline(llm, defense, max_tool_rounds):
    # Attack templates address models by name; upstream has no DeepSeek entry.
    # This supplies metadata only and does not change payload logic or evaluators.
    MODEL_NAMES[llm.model] = "DeepSeek"
    pipeline = AgentPipeline.from_config(PipelineConfig(
        llm=llm, model_id=None, defense=None if defense == "none" else defense,
        system_message_name=None, system_message=None,
    ))
    for element in pipeline.elements:
        if isinstance(element, ToolsExecutionLoop):
            element.max_iters = max_tool_rounds
    return pipeline


def previous_spending():
    total = 0.0
    for path in (ROOT / "runs/course_project").glob("*/usage.jsonl"):
        for line in path.read_text().splitlines():
            if line.strip():
                total += json.loads(line)["estimated_cost_cny"]
    return total


def summarize(rows):
    summary = {}
    for defense in sorted({row["defense"] for row in rows}):
        selected = [row for row in rows if row["defense"] == defense]
        clean = [row for row in selected if row["phase"] == "clean"]
        attacked = [row for row in selected if row["phase"] == "attacked"]
        completed_attacked = [row for row in attacked if row["status"] == "completed"]
        def rate(data, field):
            return sum(row[field] is True for row in data) / len(data) if data else None
        summary[defense] = {
            "clean_scheduled": len(clean),
            "clean_completed": sum(row["status"] == "completed" for row in clean),
            "clean_utility_including_incomplete_as_unsolved": rate(clean, "utility"),
            "attacked_scheduled": len(attacked),
            "attacked_completed": len(completed_attacked),
            "attack_success_rate_completed_only": rate(completed_attacked, "attack_success"),
            "attacked_utility_completed_only": rate(completed_attacked, "utility"),
            "safe_completion_rate_completed_only": (
                sum(row["utility"] is True and row["attack_success"] is False
                    for row in completed_attacked) / len(completed_attacked)
                if completed_attacked else None),
            "incomplete_attack_outcomes_unknown": len(attacked) - len(completed_attacked),
            "capability_controls": [row for row in selected if row["phase"] == "attack_capability"],
        }
    return summary


def run(config_path):
    config = load_config(config_path)
    load_dotenv(ROOT / ".env", override=False)
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise SystemExit("Missing DEEPSEEK_API_KEY. Set it in the git-ignored .env file; do not send it in chat.")
    model = os.environ.get("DEEPSEEK_MODEL", "deepseek-flash")
    base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    if base_url.rstrip("/") not in ("https://api.deepseek.com", "https://api.deepseek.com/v1"):
        raise SystemExit("This pilot is configured for the official DeepSeek endpoint only.")
    if config["thinking"] != "disabled":
        raise SystemExit("Thinking mode requires a different history adapter; this baseline disables it.")

    suite = get_suite(config["benchmark_version"], config["suite"])
    for task_id in config["user_tasks"]:
        suite.get_user_task_by_id(task_id)
    for task_id in config["injection_tasks"]:
        suite.get_injection_task_by_id(task_id)
    previous = previous_spending()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "runs/course_project" / run_id
    output.mkdir(parents=True, exist_ok=False)
    manifest = {
        **environment_metadata(), "run_id": run_id, "config": config,
        "config_sha256": hashlib.sha256(Path(config_path).read_bytes()).hexdigest(),
        "provider": "DeepSeek", "base_url": base_url, "model": model,
        "price_source": "https://api-docs.deepseek.com/zh-cn/quick_start/pricing/",
        "price_checked_date": "2026-11-01",
        "estimated_previous_project_cost_cny": previous,
        "comparability": "Different LLM and benchmark version from the 2024 paper; no direct numerical equivalence claimed.",
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    client = OpenAI(api_key=key, base_url=base_url, max_retries=0,
                    timeout=httpx.Timeout(45.0, connect=10.0))
    llm = DeepSeekLLM(client, model, config, output / "usage.jsonl", previous)
    rows = []
    halted = False

    def episode(pipeline, phase, task_id, trial, defense, injection_id=None, attack=None):
        nonlocal halted
        row = {"phase": phase, "task_id": task_id, "injection_id": injection_id,
               "trial": trial, "defense": defense, "status": "not_run",
               "utility": None, "attack_success": None}
        start = len(llm.records)
        if not halted:
            llm.context = {key: row[key] for key in ("phase", "task_id", "injection_id", "trial", "defense")}
            try:
                with NullLogger() as logger:
                    logger.logdir = str(output / f"trial_{trial}" / "traces")
                    if phase != "attacked":
                        task = (suite.get_injection_task_by_id(task_id) if phase == "attack_capability"
                                else suite.get_user_task_by_id(task_id))
                        utility, _ = run_task_without_injection_tasks(
                            suite, pipeline, task, output, True, config["benchmark_version"])
                        attack_success = None  # Clean runs return a sentinel, not an ASR observation.
                    else:
                        utilities, attacks = run_task_with_injection_tasks(
                            suite, pipeline, suite.get_user_task_by_id(task_id), attack,
                            output, True, [injection_id], config["benchmark_version"])
                        utility = utilities[(task_id, injection_id)]
                        attack_success = attacks[(task_id, injection_id)]
                if any(record["status"] != "ok" for record in llm.records[start:]):
                    raise RuntimeError("An upstream-caught API error makes the episode incomplete")
                row.update(status="completed", utility=bool(utility), attack_success=attack_success)
            except Exception as exc:
                row.update(status="error", error_type=type(exc).__name__)
                # Stop on infrastructure/protocol failures. Never interpret them as a successful defense.
                halted = True
        row["api_calls"] = len(llm.records) - start
        row["estimated_cost_cny"] = sum(record["estimated_cost_cny"] for record in llm.records[start:])
        rows.append(row)
        with (output / "episodes.jsonl").open("a") as stream:
            stream.write(json.dumps(row) + "\n")
        print(json.dumps(row), flush=True)

    try:
        for trial in range(config["trials"]):
            random.seed(trial)
            for defense in config["defenses"]:
                pipeline = build_pipeline(llm, defense, config["max_tool_rounds"])
                attack = load_attack(config["attack"], suite, pipeline)
                if config["attack_capability_controls"]:
                    for task_id in config["injection_tasks"]:
                        episode(pipeline, "attack_capability", task_id, trial, defense)
                for task_id in config["user_tasks"]:
                    episode(pipeline, "clean", task_id, trial, defense)
                for task_id in config["user_tasks"]:
                    for injection_id in config["injection_tasks"]:
                        episode(pipeline, "attacked", task_id, trial, defense, injection_id, attack)
    finally:
        client.close()
        report = {"run_id": run_id, "is_development_pilot": True,
                  "halted_on_error": halted, "estimated_cost_cny": llm.estimated_cost_cny,
                  "metrics": summarize(rows)}
        (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"Results: {output}", flush=True)
    if halted:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    args = parser.parse_args()
    run(args.config)
