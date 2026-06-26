"""Harness entry point: runs project 1's eval set live against project 1's
agent CLI, scores it, tracks cost/latency, and optionally gates against a
saved baseline. See docs/spec.md for the full design.
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import yaml

from . import config, cost, gate, report, scoring
from .runner import AgentInvocationError, run_question


def load_questions() -> list[dict]:
    with open(config.QUESTIONS_PATH) as f:
        data = yaml.safe_load(f)
    return data["questions"]


def run_one(question: dict) -> dict:
    question_id = question["id"]
    try:
        result = run_question(question_id, question["question"])
    except AgentInvocationError as e:
        return {
            "question_id": question_id,
            "tier": question["tier"],
            "question": question["question"],
            "error": str(e),
            "score": None,
            "passed": False,
            "cost": None,
            "latency_ms": None,
            "tool_calls_made": None,
            "expected_tool_calls": question.get("expected_tool_calls"),
        }

    final_answer = result["final_answer"]
    score_info = scoring.score_question(question, final_answer)
    cost_info = cost.compute_cost(result["total_usage"])
    tool_call_latency_sum = sum(t.get("latency_ms", 0) for t in result["trace"])

    return {
        "question_id": question_id,
        "tier": question["tier"],
        "question": question["question"],
        "final_answer": final_answer,
        "error": None,
        "run_id": result["run_id"],
        "tool_calls_made": result["tool_calls_made"],
        "expected_tool_calls": question.get("expected_tool_calls"),
        "expected_tools": question.get("expected_tools"),
        "hit_cap": result["hit_cap"],
        "stop_reason": result["stop_reason"],
        "cost": cost_info,
        "latency_ms": result["_harness_wall_ms"],
        "tool_call_latency_ms_sum": tool_call_latency_sum,
        **score_info,
    }


def build_report(question_records: list[dict], started_at: str) -> dict:
    completed_at = datetime.now(timezone.utc).isoformat()
    scored = [q for q in question_records if q.get("score") is not None]
    num_passed = sum(1 for q in scored if q["passed"])
    accuracy_pct = 100 * num_passed / len(scored) if scored else 0.0
    total_cost_usd = sum(
        q["cost"]["total_cost_usd"] for q in question_records if q.get("cost")
    )
    total_latency_ms = sum(
        q["latency_ms"] for q in question_records if q.get("latency_ms") is not None
    )

    return {
        "run_id": "run_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "run_started_at": started_at,
        "run_completed_at": completed_at,
        "num_questions": len(question_records),
        "num_scored": len(scored),
        "num_passed": num_passed,
        "accuracy_pct": accuracy_pct,
        "total_cost_usd": total_cost_usd,
        "total_latency_ms": total_latency_ms,
        "questions": question_records,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--questions",
        help="Comma-separated question IDs to run (default: all questions in questions.yml)",
    )
    parser.add_argument(
        "--gate",
        action="store_true",
        help="Exit non-zero if this run regresses against results/baseline.json",
    )
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Overwrite results/baseline.json with this run's aggregate",
    )
    args = parser.parse_args()

    all_questions = load_questions()
    if args.questions:
        wanted = set(args.questions.split(","))
        all_questions = [q for q in all_questions if q["id"] in wanted]
        if not all_questions:
            print(f"no questions matched: {args.questions}", file=sys.stderr)
            sys.exit(2)

    started_at = datetime.now(timezone.utc).isoformat()
    question_records = []
    for q in all_questions:
        print(f"running {q['id']} ({q['tier']})...", file=sys.stderr)
        record = run_one(q)
        if record.get("error"):
            print(f"  ERROR: {record['error']}", file=sys.stderr)
        question_records.append(record)

    eval_report = build_report(question_records, started_at)

    config.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_path = config.RESULTS_DIR / f"{eval_report['run_id']}.json"
    run_path.write_text(json.dumps(eval_report, indent=2))
    md_path = config.RESULTS_DIR / f"{eval_report['run_id']}.md"
    md_path.write_text(report.render_markdown(eval_report))

    print()
    print(report.render_console_table(eval_report))
    print(f"\nwrote {run_path}")

    baseline_existed = config.BASELINE_PATH.exists()
    if args.update_baseline or not baseline_existed:
        config.BASELINE_PATH.write_text(json.dumps(eval_report, indent=2))
        print(f"wrote {config.BASELINE_PATH} ({'updated' if baseline_existed else 'first run'})")

    if args.gate:
        if not baseline_existed:
            print("no prior baseline to gate against -- this run became the baseline")
            sys.exit(0)
        baseline = json.loads(config.BASELINE_PATH.read_text())
        if args.update_baseline:
            print("--gate has no effect together with --update-baseline on the same run")
            sys.exit(0)
        result = gate.evaluate_gate(eval_report, baseline)
        if result["passed"]:
            print("gate: PASS")
            sys.exit(0)
        print("gate: FAIL")
        for reason in result["reasons"]:
            print(f"  - {reason}")
        sys.exit(1)


if __name__ == "__main__":
    main()
