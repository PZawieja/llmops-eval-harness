# LLMOps Eval Harness

Project 2 of 4 in a series demonstrating AI + Analytics Engineering skill. Project 1,
[`dbt-agentic-engine`](https://github.com/PZawieja/dbt-agentic-engine), is an agent that
chains tool calls over a dbt project and logs a structured execution trace per question.
This project runs that agent's fixed eval set live, scores each answer, tracks token
cost and latency from real runs, and can gate a run against a saved baseline so a future
change to the prompt, toolbelt, or model can't silently make things worse.

See `docs/spec.md` for the full design (scoring methodology, cost/latency tracking,
regression gating) and `docs/decisions.md` for rejected approaches as they come up.

Status: scaffolding only — spec written, not yet implemented.
