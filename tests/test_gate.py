from harness import gate


def _baseline(accuracy=100.0, cost=1.0, latency=10_000.0):
    return {"accuracy_pct": accuracy, "total_cost_usd": cost, "total_latency_ms": latency}


def test_gate_passes_when_unchanged():
    baseline = _baseline()
    report = _baseline()
    result = gate.evaluate_gate(report, baseline)
    assert result["passed"] is True
    assert result["reasons"] == []


def test_gate_fails_on_accuracy_regression():
    baseline = _baseline(accuracy=100.0)
    report = _baseline(accuracy=80.0)  # 20-point drop, exceeds 5-point max
    result = gate.evaluate_gate(report, baseline)
    assert result["passed"] is False
    assert any("accuracy" in r for r in result["reasons"])


def test_gate_passes_within_accuracy_tolerance():
    baseline = _baseline(accuracy=100.0)
    report = _baseline(accuracy=97.0)  # 3-point drop, within 5-point max
    result = gate.evaluate_gate(report, baseline)
    assert result["passed"] is True


def test_gate_fails_on_cost_regression():
    baseline = _baseline(cost=1.0)
    report = _baseline(cost=2.0)  # 100% increase, exceeds 20% max
    result = gate.evaluate_gate(report, baseline)
    assert result["passed"] is False
    assert any("cost" in r for r in result["reasons"])


def test_gate_fails_on_latency_regression():
    baseline = _baseline(latency=10_000.0)
    report = _baseline(latency=15_000.0)  # 50% increase, exceeds 20% max
    result = gate.evaluate_gate(report, baseline)
    assert result["passed"] is False
    assert any("latency" in r for r in result["reasons"])
