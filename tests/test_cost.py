from harness import cost


def test_compute_cost():
    result = cost.compute_cost({"input_tokens": 1_000_000, "output_tokens": 1_000_000})
    assert result["input_cost_usd"] == 3.00
    assert result["output_cost_usd"] == 15.00
    assert result["total_cost_usd"] == 18.00


def test_compute_cost_zero_tokens():
    result = cost.compute_cost({"input_tokens": 0, "output_tokens": 0})
    assert result["total_cost_usd"] == 0.0
