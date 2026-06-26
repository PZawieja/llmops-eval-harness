"""Shells out to project 1's agent/cli.py per question, per docs/spec.md's
CLI contract. No shared package with project 1 -- only this subprocess
boundary and the JSON shape it prints on stdout.
"""

import json
import subprocess
import time
from datetime import datetime, timezone

from . import config


class AgentInvocationError(RuntimeError):
    pass


def run_question(question_id: str, question_text: str) -> dict:
    started_at = datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    try:
        proc = subprocess.run(
            ["uv", "run", "python", config.CLI_RELATIVE_PATH,
             "--question", question_text, "--question-id", question_id],
            cwd=config.AGENT_DIR,
            capture_output=True,
            text=True,
            timeout=config.SUBPROCESS_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as e:
        raise AgentInvocationError(
            f"agent CLI timed out after {config.SUBPROCESS_TIMEOUT_SECONDS}s "
            f"for {question_id}"
        ) from e
    wall_ms = round((time.monotonic() - start) * 1000, 2)
    completed_at = datetime.now(timezone.utc).isoformat()

    if proc.returncode != 0:
        raise AgentInvocationError(
            f"agent CLI failed for {question_id} (exit {proc.returncode}): "
            f"{proc.stderr.strip()}"
        )

    stdout = proc.stdout.strip()
    if not stdout:
        raise AgentInvocationError(f"agent CLI produced no output for {question_id}")
    try:
        result = json.loads(stdout.splitlines()[-1])
    except json.JSONDecodeError as e:
        raise AgentInvocationError(
            f"could not parse agent CLI output for {question_id}: {e}"
        ) from e

    result["_harness_started_at"] = started_at
    result["_harness_completed_at"] = completed_at
    result["_harness_wall_ms"] = wall_ms
    return result
