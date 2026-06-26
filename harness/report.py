"""Human-readable console table and markdown summary, per docs/spec.md.
The JSON report (written by main.py) is the machine-readable artifact;
this module only renders it.
"""

_COLUMNS = ["id", "tier", "pass", "score", "cost_usd", "latency_ms", "tools (actual/est)"]


def _row_values(q: dict) -> list[str]:
    score = "n/a" if q.get("score") is None else f"{q['score']:.2f}"
    passed = "-" if q.get("passed") is None else ("PASS" if q["passed"] else "FAIL")
    if q.get("error"):
        passed = "ERROR"
    cost = "n/a" if q.get("cost") is None else f"{q['cost']['total_cost_usd']:.4f}"
    latency = "n/a" if q.get("latency_ms") is None else f"{q['latency_ms']:.0f}"
    tools = f"{q.get('tool_calls_made', 'n/a')}/{q.get('expected_tool_calls', 'n/a')}"
    return [q["question_id"], q["tier"], passed, score, cost, latency, tools]


def render_console_table(report: dict) -> str:
    rows = [_row_values(q) for q in report["questions"]]
    widths = [
        max(len(_COLUMNS[i]), *(len(r[i]) for r in rows)) if rows else len(_COLUMNS[i])
        for i in range(len(_COLUMNS))
    ]
    lines = []
    header = "  ".join(c.ljust(w) for c, w in zip(_COLUMNS, widths))
    lines.append(header)
    lines.append("  ".join("-" * w for w in widths))
    for r in rows:
        lines.append("  ".join(v.ljust(w) for v, w in zip(r, widths)))
    lines.append("")
    lines.append(
        f"accuracy: {report['accuracy_pct']:.1f}%  "
        f"({report['num_passed']}/{report['num_scored']} scored questions passed)"
    )
    lines.append(f"total cost: ${report['total_cost_usd']:.4f}")
    lines.append(f"total latency: {report['total_latency_ms']:.0f}ms")
    return "\n".join(lines)


def render_markdown(report: dict) -> str:
    lines = [f"# Eval run {report['run_id']}", ""]
    lines.append(f"- started: {report['run_started_at']}")
    lines.append(f"- completed: {report['run_completed_at']}")
    lines.append(
        f"- accuracy: {report['accuracy_pct']:.1f}% "
        f"({report['num_passed']}/{report['num_scored']} scored questions passed)"
    )
    lines.append(f"- total cost: ${report['total_cost_usd']:.4f}")
    lines.append(f"- total latency: {report['total_latency_ms']:.0f}ms")
    lines.append("")
    lines.append("| " + " | ".join(_COLUMNS) + " |")
    lines.append("|" + "|".join(["---"] * len(_COLUMNS)) + "|")
    for q in report["questions"]:
        lines.append("| " + " | ".join(_row_values(q)) + " |")
    return "\n".join(lines) + "\n"
