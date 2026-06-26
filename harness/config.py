import os
from pathlib import Path

AGENT_REPO_PATH = Path(
    os.environ.get("AGENT_REPO_PATH", "../dbt-agentic-engine")
).resolve()
AGENT_DIR = AGENT_REPO_PATH / "agent"
CLI_RELATIVE_PATH = "cli.py"
QUESTIONS_PATH = AGENT_REPO_PATH / "eval" / "questions.yml"

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
BASELINE_PATH = RESULTS_DIR / "baseline.json"

# Claude Sonnet 4.6 pricing per docs/spec.md -- sourced via the claude-api skill,
# 2026-06-23. Re-check before publishing a cost number; pricing changes.
INPUT_PRICE_PER_MTOK = 3.00
OUTPUT_PRICE_PER_MTOK = 15.00

# Per docs/spec.md and CLAUDE.md: hard caps are config values, not buried.
SUBPROCESS_TIMEOUT_SECONDS = 120

# Regression gate thresholds (--gate). Percentage points for accuracy, percent
# increase over baseline for cost/latency.
MAX_ACCURACY_DROP_PCT = 5.0
MAX_COST_INCREASE_PCT = 20.0
MAX_LATENCY_INCREASE_PCT = 20.0
