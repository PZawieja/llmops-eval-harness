# Decisions Log

Append-only. Every time an approach is tried and rejected — by Piotr or after testing
proves it wrong — log it here with a one-line reason. Check this file before proposing a
fix to a recurring class of problem. Never propose something already rejected here.

Carried over from the series (do not reintroduce):
- Subqueries in WHERE clauses — rejected on style grounds, use CTE reordering + JOIN
  instead.
- `FILTER (WHERE ...)` on aggregates — not supported in Snowflake, breaks in production
  even if it works in dev. Use `CASE WHEN ... THEN ... ELSE NULL END` inside the
  aggregate.
- Investigation-tier `expected_tool_calls` minimums in project 1's eval set are
  minimum-path estimates, not hard requirements — a meaningful fraction of live runs
  exceed them due to model stochasticity, not agent bugs. Don't score against them as
  pass/fail (see `docs/spec.md`).

## llmops-eval-harness

No rejected approaches yet.
