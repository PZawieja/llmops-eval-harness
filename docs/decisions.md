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

**Baseline run accuracy 46.7% (7/15) — root causes documented, not scoring bugs.**
First live run (2026-06-26) produced 46.7% accuracy. Two independent causes:

1. *Investigation questions hit the 6-tool-call cap.* q06 and q07 hit the cap before
   completing cross-mart joins and returned the partial-findings fallback string, scoring
   0. q08 hit the cap mid-query after a wrong column name (`mrr` instead of `mrr_amount`)
   burned two of six calls. q10–q12 used 5–6 calls and scored 0.40–0.75. This is an agent
   limitation (project 1's cap is intentionally conservative); it is not a harness scoring
   bug. Do not raise the cap here — it's a project-1 config value.

2. *`expected_answer` substring matching fails on semantically correct but differently
   phrased answers.* q04 expected "Yes — all 7 tests pass (6 not_null tests on
   month_date/new_mrr/...)" as a literal substring; the agent said "Yes, all 7 tests
   currently pass for `fct_mrr_bridge_monthly`..." — correct answer, zero score. q09
   expected "No — all tests pass across all three marts"; agent said "All three marts are
   fully clean" — same problem. The fix is to use `expected_data` (structured key→value)
   for questions where specific phrasing can vary. Do not add more regex to the scorer;
   the spec documents this as a known v1 limitation and names LLM-as-judge as the next
   step only for the unanswerable tier.
