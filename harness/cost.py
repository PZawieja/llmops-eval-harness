"""Token cost from an actual run's total_usage, per docs/spec.md: cost is
reported, not assumed.
"""

from . import config


def compute_cost(total_usage: dict) -> dict:
    input_tokens = total_usage["input_tokens"]
    output_tokens = total_usage["output_tokens"]
    input_cost = input_tokens / 1_000_000 * config.INPUT_PRICE_PER_MTOK
    output_cost = output_tokens / 1_000_000 * config.OUTPUT_PRICE_PER_MTOK
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost_usd": round(input_cost, 6),
        "output_cost_usd": round(output_cost, 6),
        "total_cost_usd": round(input_cost + output_cost, 6),
    }
