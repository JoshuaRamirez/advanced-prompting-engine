"""Tests for v2 positional tension computation."""

from advanced_prompting_engine.graph.schema import GRID_SIZE, NexusTier
from advanced_prompting_engine.math.tension import (
    compute_tensions,
    positional_distance,
    positional_tension,
)


class TestPositionalDistance:
    def test_same_point(self):
        assert positional_distance(0, 0, 0, 0) == 0.0

    def test_max_distance(self):
        """Opposite corners of a 12x12 grid (0,0)→(11,11) = 1.0."""
        d = positional_distance(0, 0, GRID_SIZE - 1, GRID_SIZE - 1)
        assert abs(d - 1.0) < 1e-6

    def test_partial_distance(self):
        d = positional_distance(0, 0, GRID_SIZE - 1, 0)
        # Should be 11 / (sqrt(2)*11) = 1/sqrt(2) ≈ 0.7071
        assert 0.70 < d < 0.72

    def test_symmetric(self):
        d1 = positional_distance(2, 3, 8, 5)
        d2 = positional_distance(8, 5, 2, 3)
        assert abs(d1 - d2) < 1e-10


class TestPositionalTension:
    def test_paired_dampens(self):
        """Paired tier (0.4 weight) produces lower tension than adjacent (1.0)."""
        t_paired = positional_tension(0, 0, 1.0, 11, 11, 1.0, NexusTier.PAIRED.value)
        t_adjacent = positional_tension(0, 0, 1.0, 11, 11, 1.0, NexusTier.ADJACENT.value)
        assert t_paired < t_adjacent

    def test_opposite_amplifies(self):
        """Opposite tier (1.5 weight) produces higher tension than adjacent (1.0)."""
        t_opposite = positional_tension(0, 0, 1.0, 11, 11, 1.0, NexusTier.OPPOSITE.value)
        t_adjacent = positional_tension(0, 0, 1.0, 11, 11, 1.0, NexusTier.ADJACENT.value)
        assert t_opposite > t_adjacent

    def test_same_position_zero(self):
        """Same position = zero distance = zero tension regardless of tier."""
        t = positional_tension(5, 5, 1.0, 5, 5, 1.0, NexusTier.OPPOSITE.value)
        assert t == 0.0

    def test_potency_weighting(self):
        """Tension scales with potency product."""
        t_full = positional_tension(0, 0, 1.0, 11, 11, 1.0, NexusTier.ADJACENT.value)
        t_half = positional_tension(0, 0, 0.5, 11, 11, 0.5, NexusTier.ADJACENT.value)
        assert abs(t_half - t_full * 0.25) < 1e-6

    def test_tier_weight_values(self):
        """Verify exact tier ratios: paired=0.4, adjacent=1.0, opposite=1.5."""
        base_args = (0, 0, 1.0, 11, 11, 1.0)
        t_p = positional_tension(*base_args, NexusTier.PAIRED.value)
        t_a = positional_tension(*base_args, NexusTier.ADJACENT.value)
        t_o = positional_tension(*base_args, NexusTier.OPPOSITE.value)
        assert abs(t_p / t_a - 0.4) < 1e-6
        assert abs(t_o / t_a - 1.5) < 1e-6


class TestComputeTensions:
    def test_single_face_no_tensions(self):
        """One face alone produces no inter-face tensions."""
        active = {"ontology": [{"id": "ontology.0_0", "x": 0, "y": 0, "potency": 1.0}]}
        nexus_tiers = {}
        result = compute_tensions(active, nexus_tiers)
        assert result["total_magnitude"] == 0.0
        assert result["tensions"] == []

    def test_two_faces_produces_tensions(self):
        """Constructs on two faces at opposite corners produce nonzero tension."""
        active = {
            "ontology": [{"id": "ontology.0_0", "x": 0, "y": 0, "potency": 1.0}],
            "epistemology": [{"id": "epistemology.11_11", "x": 11, "y": 11, "potency": 1.0}],
        }
        nexus_tiers = {("ontology", "epistemology"): NexusTier.ADJACENT.value}
        result = compute_tensions(active, nexus_tiers)
        assert result["total_magnitude"] > 0
        assert len(result["tensions"]) == 1
        t = result["tensions"][0]
        assert t["cube_tier"] == NexusTier.ADJACENT.value
        assert abs(t["positional_distance"] - 1.0) < 1e-6

    def test_paired_tier_used(self):
        """Verify paired tier lookup works through compute_tensions."""
        active = {
            "ontology": [{"id": "ontology.0_0", "x": 0, "y": 0, "potency": 1.0}],
            "praxeology": [{"id": "praxeology.11_11", "x": 11, "y": 11, "potency": 1.0}],
        }
        nexus_tiers = {("ontology", "praxeology"): NexusTier.PAIRED.value}
        result = compute_tensions(active, nexus_tiers)
        assert len(result["tensions"]) == 1
        assert result["tensions"][0]["cube_tier"] == NexusTier.PAIRED.value
        # Paired has 0.4 weight, so magnitude = 1.0 * 1.0 * 1.0 * 0.4
        assert abs(result["tensions"][0]["magnitude"] - 0.4) < 1e-6

    def test_same_position_below_threshold(self):
        """Same grid position on two faces produces zero distance, filtered out."""
        active = {
            "ontology": [{"id": "ontology.5_5", "x": 5, "y": 5, "potency": 1.0}],
            "epistemology": [{"id": "epistemology.5_5", "x": 5, "y": 5, "potency": 1.0}],
        }
        nexus_tiers = {("ontology", "epistemology"): NexusTier.ADJACENT.value}
        result = compute_tensions(active, nexus_tiers)
        assert result["total_magnitude"] == 0.0
        assert result["tensions"] == []

    def test_multiple_constructs_cross_product(self):
        """Two constructs on each face = 4 tension pairs."""
        active = {
            "ontology": [
                {"id": "ontology.0_0", "x": 0, "y": 0, "potency": 1.0},
                {"id": "ontology.11_11", "x": 11, "y": 11, "potency": 1.0},
            ],
            "epistemology": [
                {"id": "epistemology.0_0", "x": 0, "y": 0, "potency": 1.0},
                {"id": "epistemology.11_11", "x": 11, "y": 11, "potency": 1.0},
            ],
        }
        nexus_tiers = {("ontology", "epistemology"): NexusTier.ADJACENT.value}
        result = compute_tensions(active, nexus_tiers)
        # (0,0)-(0,0)=0 filtered, (0,0)-(11,11)=1.0, (11,11)-(0,0)=1.0, (11,11)-(11,11)=0 filtered
        assert len(result["tensions"]) == 2
