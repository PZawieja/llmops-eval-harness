# Project Spec — LLMOps Cost & Eval Harness

## What this project is for

Portfolio project #2 in a four-project series demonstrating AI + Analytics Engineering
skill, published at github.com/PZawieja and linked from goldlayer.dev. Series order:

1. dbt-native analytics agent (`dbt-agentic-engine`) — agentic tool-use over a dbt
   project, with a structured execution trace as the differentiator
2. **This project** — runs project 1's fixed eval set against project 1's live agent,
   scores accuracy, tracks token cost/latency, gates a run against a saved baseline
3. Semantic layer agent — NL resolves to dbt-defined metrics (MetricFlow / semantic
   layer), never to ad-hoc SQL synthesis
4. Multi-tenant cost guardrails capstone — per-user budget caps, caching, kill-switch on
   warehouse credit spend

This spec covers project 2 only. Don't build ahead into 3–4.

## The gap this closes

Project 1 proved the agent can chain tool calls and produce a structured trace per
question. It did not prove that behavior stays correct or affordable over time — there
was no scoring, no cost number from an actual run (only per-question token counts), and
no way to tell if a future change to the prompt, toolbelt, or model made things worse.
This project turns "I manually sanity-checked 15 questions once" (project 1's Phase 5)
into a repeatable, scored, cost-aware check that can gate future changes.

## Dependency on project 1

Project 1 (`dbt-agentic-engine`) lives in a sibling directory, path configurable via env
var `AGENT_REPO_PATH` (default `../dbt-agentic-engine`). This project does not import
project 1's Python modules and does not duplicate its eval set or trace format — it:

- reads `${AGENT_REPO_PATH}/eval/questions.yml` directly as the single source of truth
  for the question set
- shells out to `${AGENT_REPO_PATH}/agent/cli.py --question ... --question-id ...` per
  question (added to project 1 specifically for this), capturing its single-line JSON
  result on stdout (same shape `agent_loop.run_question()` returns: `final_answer`,
  `trace`, `tool_calls_made`, `hit_cap`, `stop_reason`, `total_usage`, `run_id`, etc.)

This keeps the two repos coupled only through that CLI contract and the JSON shape — no
shared package, no monorepo.

## Functional requirements

### Scoring (deterministic, no LLM-as-judge in v1)

- **lookup / investigation tiers**: each question in `eval/questions.yml` carries either
  `expected_data` (structured key→value facts, e.g. `mar_mrr: 800.00`) or an
  `expected_answer` string. Score = fraction of expected facts found as substrings in the
  agent's `final_answer`, matching numbers with formatting tolerance (`800` matches
  `800.00` matches `$800`). `expected_tool_calls` / `expected_tools` are recorded as
  informational metrics alongside the score, not used for pass/fail — project 1's
  `docs/decisions.md` already established these are minimum-path estimates, not hard
  requirements, and a meaningful fraction of live runs exceed them for reasons unrelated
  to correctness.
- **unanswerable tier**: pass if the final answer contains no fabricated figure and
  matches a decline heuristic (regex over phrases like "outside the scope," "doesn't
  track," "no model," "not tracked here"). This is a known-fragile heuristic, not
  semantic understanding — documented as a v1 limitation. If it proves too brittle in
  practice (false negatives on a correct decline phrased unexpectedly), the documented
  next step is an LLM-as-judge pass for this tier specifically, not a bigger regex.

### Cost tracking

Each question's CLI result includes `total_usage` (input/output tokens). Multiply by
current Claude Sonnet 4.6 per-token pricing, sourced from Anthropic's pricing page (or
the `claude-api` Claude Code skill) at implementation time — not hardcoded into this
spec, since pricing changes and this document shouldn't go stale. Report per-question and
total run cost.

### Latency tracking

Per-tool-call `latency_ms` (already in every trace record returned by the CLI) plus total
wall time per question, derived the same way project 1's trace summary records already
compute it (`started_at` / `completed_at`).

### Regression gating

First run writes `results/baseline.json`: per-question pass/fail + score, aggregate
accuracy %, total cost, total latency. A `--gate` flag on later runs compares against
that baseline and exits non-zero if accuracy drops or cost/latency rises beyond a
threshold. Thresholds are named constants in one place in the harness code — visible, not
buried, per `CLAUDE.md`'s standing rule that hard caps are config values, not
suggestions. Exact thresholds are a v1 implementation decision, not fixed by this spec.

### Output

A scored report per run (JSON, machine-readable) and a human-readable console/markdown
summary table: question id, tier, pass/fail, score, cost, latency, tool calls actually
used vs. the eval file's estimate.

## Explicit non-goals for v1

- No LLM-as-judge scoring (see "Scoring" above) — deterministic only.
- No CI wiring. Project 1's CI is free (lint + local `dbt build`, no API calls); running
  this harness in CI means a real Anthropic key spending real money on every push. That's
  a cost/credentials decision for Piotr to make explicitly later, not something this
  project assumes.
- No semantic layer / MetricFlow integration (project 3).
- No multi-tenant anything (project 4).
- Does not modify project 1's agent behavior — only adds a CLI entry point to invoke the
  existing, unmodified `run_question()`.

## Definition of done

- `agent/cli.py` exists in project 1, takes `--question` / `--question-id`, prints one
  JSON object matching `run_question()`'s return shape, and still appends to project 1's
  `traces/trace_log.jsonl` exactly as the Streamlit app already does.
- Harness runs all 15 questions in project 1's `eval/questions.yml` live, end to end,
  producing a scored report and a cost/latency total from an actual run (per `CLAUDE.md`:
  "cost and latency are reported, not assumed").
- `results/baseline.json` exists from a real run.
- `--gate` correctly exits non-zero against an injected regression (e.g. a baseline
  edited to claim higher accuracy than the current run achieves) and exits zero when
  nothing has regressed.
- `docs/decisions.md` exists, even if just noting "no rejected approaches yet."
- `README.md` explains what this project adds on top of project 1, in plain terms.
