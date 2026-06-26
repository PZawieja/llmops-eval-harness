"""Regression gate: compare a run's aggregate against results/baseline.json.
Thresholds live in config.py, per CLAUDE.md's standing rule that hard caps
are config values, not buried.
"""

from . import config


def evaluate_gate(report: dict, baseline: dict) -> dict:
    reasons = []

    accuracy_drop = baseline["accuracy_pct"] - report["accuracy_pct"]
    if accuracy_drop > config.MAX_ACCURACY_DROP_PCT:
        reasons.append(
            f"accuracy dropped {accuracy_drop:.1f} points "
            f"({baseline['accuracy_pct']:.1f}% -> {report['accuracy_pct']:.1f}%), "
            f"exceeds max allowed drop of {config.MAX_ACCURACY_DROP_PCT}"
        )

    if baseline["total_cost_usd"] > 0:
        cost_increase_pct = (
            (report["total_cost_usd"] - baseline["total_cost_usd"])
            / baseline["total_cost_usd"]
            * 100
        )
        if cost_increase_pct > config.MAX_COST_INCREASE_PCT:
            reasons.append(
                f"total cost rose {cost_increase_pct:.1f}% "
                f"(${baseline['total_cost_usd']:.4f} -> ${report['total_cost_usd']:.4f}), "
                f"exceeds max allowed increase of {config.MAX_COST_INCREASE_PCT}%"
            )

    if baseline["total_latency_ms"] > 0:
        latency_increase_pct = (
            (report["total_latency_ms"] - baseline["total_latency_ms"])
            / baseline["total_latency_ms"]
            * 100
        )
        if latency_increase_pct > config.MAX_LATENCY_INCREASE_PCT:
            reasons.append(
                f"total latency rose {latency_increase_pct:.1f}% "
                f"({baseline['total_latency_ms']:.0f}ms -> {report['total_latency_ms']:.0f}ms), "
                f"exceeds max allowed increase of {config.MAX_LATENCY_INCREASE_PCT}%"
            )

    return {"passed": not reasons, "reasons": reasons}
