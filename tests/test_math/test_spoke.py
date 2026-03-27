"""Tests for spoke shape computation and central gem coherence."""

from advanced_prompting_engine.math.spoke import (
    classify_coherence,
    classify_spoke,
    compute_central_gem,
    compute_contributions,
    compute_spoke_shape,
)


def test_empty_gems_guard():
    """Empty gem list must NOT produce NaN."""
    spoke = compute_spoke_shape([])
    assert spoke["strength"] == 0.0
    assert spoke["consistency"] == 1.0
    assert spoke["polarity"] == 0.0
    assert spoke["gems"] == []


def test_single_gem():
    spoke = compute_spoke_shape([{"magnitude": 0.8, "type": "harmonious"}])
    assert spoke["strength"] == 0.8
    assert spoke["polarity"] == 0.0


def test_mixed_gems():
    gems = [
        {"magnitude": 0.9, "type": "harmonious"},
        {"magnitude": 0.3, "type": "conflicting"},
        {"magnitude": 0.6, "type": "harmonious"},
    ]
    spoke = compute_spoke_shape(gems)
    assert abs(spoke["strength"] - 0.6) < 1e-6
    assert abs(spoke["polarity"] - 1 / 3) < 1e-6


def test_contributions():
    spokes = {
        "a": {"strength": 0.6, "consistency": 0.8, "polarity": 0.0, "gems": []},
        "b": {"strength": 0.4, "consistency": 0.7, "polarity": 0.0, "gems": []},
    }
    compute_contributions(spokes)
    assert abs(spokes["a"]["contribution"] - 0.6) < 1e-6
    assert abs(spokes["b"]["contribution"] - 0.4) < 1e-6


def test_classify_coherent():
    spoke = {"strength": 0.7, "consistency": 0.8, "contribution": 0.1}
    assert classify_spoke(spoke) == "coherent"


def test_classify_fragmented():
    spoke = {"strength": 0.7, "consistency": 0.3, "contribution": 0.1}
    assert classify_spoke(spoke) == "fragmented"


def test_classify_dominant():
    spoke = {"strength": 0.7, "consistency": 0.5, "contribution": 0.2}
    assert classify_spoke(spoke) == "dominant"


def test_classify_weakly_integrated():
    spoke = {"strength": 0.1, "consistency": 0.9, "contribution": 0.05}
    assert classify_spoke(spoke) == "weakly_integrated"


def test_classify_moderate():
    spoke = {"strength": 0.35, "consistency": 0.5, "contribution": 0.1}
    assert classify_spoke(spoke) == "moderate"


def test_central_gem_coherence():
    spokes = {
        "a": {"strength": 0.5, "consistency": 0.8, "contribution": 0.5},
        "b": {"strength": 0.5, "consistency": 0.8, "contribution": 0.5},
    }
    cg = compute_central_gem(spokes)
    assert cg["coherence"] > 0
    assert cg["classification"] in (
        "highly_coherent", "moderately_coherent", "weakly_coherent", "incoherent"
    )


def test_coherence_thresholds():
    assert classify_coherence(0.1) == "highly_coherent"
    assert classify_coherence(0.08) == "highly_coherent"
    assert classify_coherence(0.06) == "moderately_coherent"
    assert classify_coherence(0.03) == "weakly_coherent"
    assert classify_coherence(0.01) == "incoherent"
