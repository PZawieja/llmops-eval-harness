# LLMOps Eval Harness

Project 2 of 4 in a series demonstrating AI + Analytics Engineering skill. Project 1,
[`dbt-agentic-engine`](https://github.com/PZawieja/dbt-agentic-engine), is an agent that
chains tool calls over a dbt project and logs a structured execution trace per question.
This project runs that agent's fixed eval set live, scores each answer, tracks token
cost and latency from real runs, and can gate a run against a saved baseline so a future
change to the prompt, toolbelt, or model can't silently make things worse.

See `docs/spec.md` for the full design (scoring methodology, cost/latency tracking,
regression gating) and `docs/decisions.md` for rejected approaches as they come up.

**Build log:** [goldlayer.dev/writing/analytics-agent-eval-harness](https://goldlayer.dev/writing/analytics-agent-eval-harness.html)

## What this adds on top of project 1

Project 1 proved the agent can chain tool calls and log a structured trace per question.
It did not have a repeatable way to check that behavior stays correct or affordable. This
project adds:

- **Deterministic scoring** — lookup and investigation questions scored by fraction of
  expected facts found in the final answer (number-formatting tolerant); unanswerable
  questions scored by a decline-phrase heuristic.
- **Cost tracking from real runs** — per-question and total USD cost computed from actual
  token counts returned by the Anthropic API, not from estimates.
- **Regression gating** — `--gate` compares a run against `results/baseline.json` and
  exits non-zero if accuracy drops more than 5 pp or cost/latency rises more than 20%.
  Thresholds are named constants in `harness/config.py`.
- **Structured JSON output + markdown summary** — every run writes a dated JSON file and a
  human-readable table to `results/`.

## Baseline run (2026-06-26, Claude Sonnet 4.6)

From an actual end-to-end run against all 15 eval questions:

| metric | value |
|---|---|
| accuracy | 46.7% (7/15 passed) |
| total cost | $0.4232 |
| total latency | 182 852 ms |

Passing: all 3 unanswerable questions (correct decline, no fabricated figure); 4/5 lookup
questions. Failing: 6/7 investigation questions — most hit the agent's 6-tool-call cap
before completing cross-mart joins; one lookup question (q04) gave a semantically correct
answer that didn't match the expected-answer substring. See `docs/decisions.md` for detail.

## Usage

```
# run all 15 questions
uv run python -m harness.main

# run a subset
uv run python -m harness.main --questions q01,q02,q03

# compare against baseline; exits non-zero on regression
uv run python -m harness.main --gate

# overwrite baseline with this run
uv run python -m harness.main --update-baseline
```

`AGENT_REPO_PATH` env var controls where project 1 lives (default `../dbt-agentic-engine`).

## Tests

```
uv run pytest
```

Unit tests cover scoring, cost calculation, and gate logic — all without live API calls.
