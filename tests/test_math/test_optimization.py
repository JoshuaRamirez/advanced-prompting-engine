"""Tests for Pareto front computation."""

from advanced_prompting_engine.math.optimization import pareto_front


def test_empty():
    assert pareto_front([]) == []


def test_single_result():
    results = [{"tension": 0.5, "generative": 3}]
    assert pareto_front(results) == results


def test_all_identical():
    results = [{"tension": 0.5, "generative": 3}] * 3
    assert len(pareto_front(results)) == 3


def test_clear_front():
    results = [
        {"tension": 0.1, "generative": 3},  # on front (low tension)
        {"tension": 0.5, "generative": 5},  # on front (high generative)
        {"tension": 0.3, "generative": 2},  # dominated by first (0.1 < 0.3 and 3 > 2)
    ]
    front = pareto_front(results)
    assert len(front) == 2
    tensions = {r["tension"] for r in front}
    assert 0.1 in tensions
    assert 0.5 in tensions
    assert 0.3 not in tensions


def test_no_dominance():
    """No result dominates any other — all on front."""
    results = [
        {"tension": 0.1, "generative": 1},
        {"tension": 0.5, "generative": 5},
        {"tension": 0.3, "generative": 3},
    ]
    front = pareto_front(results)
    assert len(front) == 3
