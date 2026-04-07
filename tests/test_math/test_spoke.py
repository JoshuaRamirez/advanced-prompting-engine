"""Tests for spoke shape computation and central gem coherence (v2 12-face system)."""

from advanced_prompting_engine.math.spoke import (
    SPOKE_THRESHOLDS,
    classify_coherence,
    classify_spoke,
    compute_central_gem,
    compute_contributions,
    compute_spoke_shape,
)


class TestSpokeShape:
    def test_empty_gems_guard(self):
        """Empty gem list must produce safe defaults, not NaN."""
        spoke = compute_spoke_shape([])
        assert spoke["strength"] == 0.0
        assert spoke["consistency"] == 1.0
        assert spoke["polarity"] == 0.0
        assert spoke["gems"] == []

    def test_single_gem(self):
        spoke = compute_spoke_shape([{"magnitude": 0.8, "type": "harmonious"}])
        assert spoke["strength"] == 0.8
        assert spoke["polarity"] == 0.0  # no conflicting gems

    def test_mixed_gems(self):
        gems = [
            {"magnitude": 0.9, "type": "harmonious"},
            {"magnitude": 0.3, "type": "conflicting"},
            {"magnitude": 0.6, "type": "harmonious"},
        ]
        spoke = compute_spoke_shape(gems)
        assert abs(spoke["strength"] - 0.6) < 1e-6
        assert abs(spoke["polarity"] - 1 / 3) < 1e-6

    def test_all_conflicting(self):
        gems = [
            {"magnitude": 0.5, "type": "conflicting"},
            {"magnitude": 0.5, "type": "conflicting"},
        ]
        spoke = compute_spoke_shape(gems)
        assert spoke["polarity"] == 1.0

    def test_eleven_gems(self):
        """12-face system produces 11 gems per spoke (one per other face)."""
        gems = [{"magnitude": 0.4, "type": "harmonious"} for _ in range(11)]
        spoke = compute_spoke_shape(gems)
        assert abs(spoke["strength"] - 0.4) < 1e-6
        assert spoke["consistency"] == 1.0  # zero std → perfect consistency


class TestContributions:
    def test_proportional_contribution(self):
        spokes = {
            "ontology": {"strength": 0.6, "consistency": 0.8, "polarity": 0.0, "gems": []},
            "epistemology": {"strength": 0.4, "consistency": 0.7, "polarity": 0.0, "gems": []},
        }
        compute_contributions(spokes)
        assert abs(spokes["ontology"]["contribution"] - 0.6) < 1e-6
        assert abs(spokes["epistemology"]["contribution"] - 0.4) < 1e-6

    def test_equal_contribution(self):
        spokes = {
            "ontology": {"strength": 0.5, "consistency": 0.8, "polarity": 0.0, "gems": []},
            "epistemology": {"strength": 0.5, "consistency": 0.8, "polarity": 0.0, "gems": []},
        }
        compute_contributions(spokes)
        assert abs(spokes["ontology"]["contribution"] - 0.5) < 1e-6

    def test_zero_strength(self):
        spokes = {
            "ontology": {"strength": 0.0, "consistency": 1.0, "polarity": 0.0, "gems": []},
        }
        compute_contributions(spokes)
        assert spokes["ontology"]["contribution"] == 0.0


class TestClassifySpoke:
    """Thresholds calibrated for 12-face system:
    high_strength=0.5, high_consistency=0.65, high_contribution=0.12, low_strength=0.25.
    """

    def test_coherent(self):
        spoke = {"strength": 0.7, "consistency": 0.8, "contribution": 0.1}
        assert classify_spoke(spoke) == "coherent"

    def test_fragmented(self):
        spoke = {"strength": 0.7, "consistency": 0.3, "contribution": 0.05}
        assert classify_spoke(spoke) == "fragmented"

    def test_dominant(self):
        spoke = {"strength": 0.7, "consistency": 0.5, "contribution": 0.15}
        assert classify_spoke(spoke) == "dominant"

    def test_weakly_integrated(self):
        spoke = {"strength": 0.1, "consistency": 0.9, "contribution": 0.05}
        assert classify_spoke(spoke) == "weakly_integrated"

    def test_moderate(self):
        spoke = {"strength": 0.35, "consistency": 0.5, "contribution": 0.08}
        assert classify_spoke(spoke) == "moderate"

    def test_threshold_values(self):
        """Verify 12-face calibrated thresholds."""
        assert SPOKE_THRESHOLDS["high_strength"] == 0.5
        assert SPOKE_THRESHOLDS["high_consistency"] == 0.65
        assert SPOKE_THRESHOLDS["high_contribution"] == 0.12
        assert SPOKE_THRESHOLDS["low_strength"] == 0.25


class TestCentralGem:
    def test_differentiated_spokes_coherent(self):
        """Spokes with varied strengths produce high CV → coherent."""
        spokes = {
            "ontology": {"strength": 0.8, "consistency": 0.9, "contribution": 0.6},
            "epistemology": {"strength": 0.1, "consistency": 0.5, "contribution": 0.1},
            "axiology": {"strength": 0.4, "consistency": 0.7, "contribution": 0.3},
        }
        cg = compute_central_gem(spokes)
        assert cg["coherence"] > 0.3
        assert cg["classification"] in (
            "highly_coherent", "moderately_coherent",
        )

    def test_identical_spokes_incoherent(self):
        """Identical spoke strengths → CV = 0 → incoherent (no differentiation)."""
        spokes = {
            "ontology": {"strength": 0.5, "consistency": 0.8, "contribution": 0.5},
            "epistemology": {"strength": 0.5, "consistency": 0.8, "contribution": 0.5},
        }
        cg = compute_central_gem(spokes)
        assert cg["coherence"] == 0.0
        assert cg["classification"] == "incoherent"

    def test_zero_strength_incoherent(self):
        """Zero-strength spokes → incoherent."""
        spokes = {
            "ontology": {"strength": 0.0, "consistency": 0.0, "contribution": 0.0},
        }
        cg = compute_central_gem(spokes)
        assert cg["coherence"] == 0.0
        assert cg["classification"] == "incoherent"


class TestCoherenceThresholds:
    """CV-based thresholds: >= 0.5 highly, >= 0.3 moderately, >= 0.1 weakly, else incoherent."""

    def test_highly_coherent(self):
        assert classify_coherence(0.7) == "highly_coherent"
        assert classify_coherence(0.5) == "highly_coherent"

    def test_moderately_coherent(self):
        assert classify_coherence(0.45) == "moderately_coherent"
        assert classify_coherence(0.3) == "moderately_coherent"

    def test_weakly_coherent(self):
        assert classify_coherence(0.2) == "weakly_coherent"
        assert classify_coherence(0.1) == "weakly_coherent"

    def test_incoherent(self):
        assert classify_coherence(0.05) == "incoherent"
        assert classify_coherence(0.0) == "incoherent"
