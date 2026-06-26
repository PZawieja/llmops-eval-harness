"""Deterministic scoring, per docs/spec.md. No LLM-as-judge in v1.

lookup / investigation: score = fraction of expected facts found as
substrings in the agent's final_answer, with formatting tolerance on
numbers (800 matches 800.00 matches $800). expected_tool_calls /
expected_tools are recorded as informational metrics elsewhere, never
scored here -- see docs/decisions.md.

unanswerable: pass if the answer matches a decline-phrase heuristic and
contains no fabricated figure. Known-fragile heuristic, not semantic
understanding -- a documented v1 limitation (see README.md).
"""

import re

_WHITESPACE_RE = re.compile(r"\s+")
_NUMBER_RE = re.compile(r"^-?\d+(\.\d+)?$")

DECLINE_PATTERNS = [
    r"outside (the |this )?scope",
    r"doesn'?t track",
    r"do(es)? ?not track",
    r"no (model|data|entity|table|field|column)",
    r"not tracked( here)?",
    r"isn'?t tracked",
    r"is not tracked",
    r"doesn'?t (have|contain)",
    r"does not (have|contain)",
    r"can'?t (find|locate|determine)",
    r"cannot (find|locate|determine)",
    r"unable to (find|determine|answer)",
    r"this (project|data(set)?) (doesn'?t|does not) (track|have)",
]
_DECLINE_RE = re.compile("|".join(DECLINE_PATTERNS), re.IGNORECASE)

# Heuristic for a fabricated number: a dollar figure or a percentage.
_FABRICATED_FIGURE_RE = re.compile(r"\$\s?\d|\d+(\.\d+)?\s*%")


def _normalize(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text).strip().lower()


def _is_numberlike(value: str) -> bool:
    cleaned = value.strip().lstrip("$").replace(",", "")
    return bool(_NUMBER_RE.match(cleaned))


def _number_variants(value: str) -> set[str]:
    cleaned = value.strip().lstrip("$").replace(",", "")
    num = float(cleaned)
    bases = {f"{num:.2f}"}
    if num == int(num):
        bases.add(str(int(num)))
        bases.add(f"{int(num):,}")
    bases.add(f"{num:,.2f}")
    variants = set()
    for b in bases:
        variants.add(b)
        variants.add(f"${b}")
    return variants


def fact_found(fact: str, answer_text: str) -> bool:
    fact = str(fact).strip()
    if not fact:
        return True
    norm_answer = _normalize(answer_text)
    if _is_numberlike(fact):
        return any(v.lower() in norm_answer for v in _number_variants(fact))
    return _normalize(fact) in norm_answer


def split_expected_answer(expected_answer: str) -> list[str]:
    text = expected_answer.strip().rstrip(".")
    parts = [p.strip().rstrip(".") for p in text.split(",")]
    return [p for p in parts if p]


def _facts_for(question: dict) -> list[str]:
    if "expected_data" in question:
        return [str(v) for v in question["expected_data"].values()]
    return split_expected_answer(question.get("expected_answer", ""))


def score_unanswerable(final_answer: str) -> dict:
    declines = bool(_DECLINE_RE.search(final_answer))
    fabricated = bool(_FABRICATED_FIGURE_RE.search(final_answer))
    passed = declines and not fabricated
    return {
        "score": 1.0 if passed else 0.0,
        "passed": passed,
        "declines": declines,
        "fabricated_figure_detected": fabricated,
    }


def score_question(question: dict, final_answer: str) -> dict:
    if question["tier"] == "unanswerable":
        return score_unanswerable(final_answer)

    facts = _facts_for(question)
    if not facts:
        return {"score": None, "passed": None, "facts_total": 0, "facts_found": 0}

    found = sum(1 for f in facts if fact_found(f, final_answer))
    score = found / len(facts)
    return {
        "score": score,
        "passed": score == 1.0,
        "facts_total": len(facts),
        "facts_found": found,
    }
