"""Tests for v2 gem magnitude computation — potency-weighted activation."""

from advanced_prompting_engine.graph.schema import GRID_SIZE, NexusTier
from advanced_prompting_engine.math.gem import TIER_GEM_MODIFIERS, compute_gem


class TestComputeGem:
    def test_balanced_activation(self):
        """Both faces active → nonzero magnitude via harmonic mean."""
        active = {
            "ontology": [{"id": "ontology.0_0", "x": 0, "y": 0, "potency": 1.0}],
            "epistemology": [{"id": "epistemology.0_0", "x": 0, "y": 0, "potency": 1.0}],
        }
        gem = compute_gem("ontology", "epistemology", active, NexusTier.ADJACENT.value)
        assert gem["nexus"] == "nexus.ontology.epistemology"
        assert gem["magnitude"] > 0
        assert gem["source_energy"] > 0
        assert gem["target_energy"] > 0

    def test_inactive_gem(self):
        """No constructs on either face → zero magnitude, inactive type."""
        active = {"ontology": [], "epistemology": []}
        gem = compute_gem("ontology", "epistemology", active, NexusTier.ADJACENT.value)
        assert gem["magnitude"] == 0.0
        assert gem["type"] == "inactive"

    def test_one_face_empty(self):
        """One face activated, the other empty → harmonic mean = 0, inactive type."""
        active = {
            "ontology": [{"id": "ontology.5_5", "x": 5, "y": 5, "potency": 0.8}],
            "epistemology": [],
        }
        gem = compute_gem("ontology", "epistemology", active, NexusTier.ADJACENT.value)
        # Harmonic mean of (something, 0) = 0
        assert gem["magnitude"] == 0.0
        assert gem["type"] == "inactive"


class TestCubeTierModulation:
    def test_paired_gets_bonus(self):
        """Paired tier applies 1.3x modifier."""
        active = {
            "ontology": [{"id": "ontology.5_5", "x": 5, "y": 5, "potency": 1.0}],
            "praxeology": [{"id": "praxeology.5_5", "x": 5, "y": 5, "potency": 1.0}],
        }
        gem_paired = compute_gem("ontology", "praxeology", active, NexusTier.PAIRED.value)
        gem_adjacent = compute_gem("ontology", "praxeology", active, NexusTier.ADJACENT.value)
        assert abs(gem_paired["magnitude"] / gem_adjacent["magnitude"] - 1.3) < 1e-6

    def test_opposite_gets_reduction(self):
        """Opposite tier applies 0.8x modifier."""
        active = {
            "ontology": [{"id": "ontology.5_5", "x": 5, "y": 5, "potency": 1.0}],
            "ethics": [{"id": "ethics.5_5", "x": 5, "y": 5, "potency": 1.0}],
        }
        gem_opposite = compute_gem("ontology", "ethics", active, NexusTier.OPPOSITE.value)
        gem_adjacent = compute_gem("ontology", "ethics", active, NexusTier.ADJACENT.value)
        assert abs(gem_opposite["magnitude"] / gem_adjacent["magnitude"] - 0.8) < 1e-6

    def test_modifier_values(self):
        """Verify exact modifier values from TIER_GEM_MODIFIERS."""
        assert TIER_GEM_MODIFIERS[NexusTier.PAIRED.value] == 1.3
        assert TIER_GEM_MODIFIERS[NexusTier.ADJACENT.value] == 1.0
        assert TIER_GEM_MODIFIERS[NexusTier.OPPOSITE.value] == 0.8


class TestGemTypeClassification:
    def test_harmonious_same_position(self):
        """Same positions on both faces → positional distance near 0 → harmonious."""
        active = {
            "ontology": [{"id": "ontology.3_3", "x": 3, "y": 3, "potency": 1.0}],
            "epistemology": [{"id": "epistemology.3_3", "x": 3, "y": 3, "potency": 1.0}],
        }
        gem = compute_gem("ontology", "epistemology", active, NexusTier.ADJACENT.value)
        assert gem["type"] == "harmonious"

    def test_conflicting_distant_positions(self):
        """Opposite corners → high positional distance → conflicting."""
        active = {
            "ontology": [{"id": "ontology.0_0", "x": 0, "y": 0, "potency": 1.0}],
            "epistemology": [{"id": "epistemology.11_11", "x": 11, "y": 11, "potency": 1.0}],
        }
        gem = compute_gem("ontology", "epistemology", active, NexusTier.ADJACENT.value)
        assert gem["type"] == "conflicting"

    def test_paired_bias_toward_harmony(self):
        """Paired tier has lower threshold (0.4) for harmony classification.

        A distance between 0.4 and 0.5 is classified as:
        - conflicting under adjacent (threshold 0.5)
        - harmonious under paired (threshold 0.4)

        dx=5, dy=6 → raw = sqrt(61) ≈ 7.81 → norm ≈ 7.81 / (sqrt(2)*11) ≈ 0.502
        Just above the 0.5 adjacent threshold but also above 0.4 paired threshold.
        We need to find the sweet spot: 0.4 <= norm < 0.5.
        dx=5, dy=4 → raw = sqrt(41) ≈ 6.40 → norm ≈ 0.412
        """
        # norm ≈ 0.412: above paired threshold (0.4) but below adjacent threshold (0.5)
        active_mid = {
            "ontology": [{"id": "ontology.0_0", "x": 0, "y": 0, "potency": 1.0}],
            "praxeology": [{"id": "praxeology.5_4", "x": 5, "y": 4, "potency": 1.0}],
        }
        gem_adjacent = compute_gem("ontology", "praxeology", active_mid, NexusTier.ADJACENT.value)
        gem_paired = compute_gem("ontology", "praxeology", active_mid, NexusTier.PAIRED.value)
        # Adjacent sees it as harmonious (0.412 < 0.5)
        assert gem_adjacent["type"] == "harmonious"
        # Paired ALSO sees it as conflicting (0.412 > 0.4)
        assert gem_paired["type"] == "conflicting"

        # Slightly closer: dx=4, dy=3 → raw = sqrt(25) = 5.0 → norm ≈ 0.321
        # Below both thresholds → harmonious for both tiers
        active_close = {
            "ontology": [{"id": "ontology.0_0", "x": 0, "y": 0, "potency": 1.0}],
            "praxeology": [{"id": "praxeology.4_3", "x": 4, "y": 3, "potency": 1.0}],
        }
        gem_paired_close = compute_gem("ontology", "praxeology", active_close, NexusTier.PAIRED.value)
        assert gem_paired_close["type"] == "harmonious"
