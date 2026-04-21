"""Tests for control-type classification and composition aggregation.

Covers the FACE_CONTROL_TYPE schema mapping (v5 of the
face-importance-ranking report), per-face annotation, and aggregate
structural/bias/mixed share computation.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import ALL_FACES, FACE_CONTROL_TYPE
from advanced_prompting_engine.math.control_type import (
    annotate_coordinate,
    compute_control_type_composition,
)


def _coord(**weights: float) -> dict:
    """Build a coordinate dict mapping face -> {x, y, weight}."""
    return {
        face: {"x": 5, "y": 5, "weight": weights.get(face, 0.3)}
        for face in ALL_FACES
    }


class TestFaceControlTypeSchema:
    def test_all_12_faces_classified(self):
        for face in ALL_FACES:
            assert face in FACE_CONTROL_TYPE
            assert FACE_CONTROL_TYPE[face] in {"structural", "bias", "mixed"}

    def test_structural_set(self):
        structural = {f for f, t in FACE_CONTROL_TYPE.items() if t == "structural"}
        assert structural == {"semiotics", "methodology", "ontology", "praxeology"}

    def test_bias_set(self):
        bias = {f for f, t in FACE_CONTROL_TYPE.items() if t == "bias"}
        assert bias == {"ethics", "axiology", "aesthetics", "hermeneutics", "heuristics"}

    def test_mixed_set(self):
        mixed = {f for f, t in FACE_CONTROL_TYPE.items() if t == "mixed"}
        assert mixed == {"epistemology", "phenomenology", "teleology"}

    def test_exhaustive_partition(self):
        counts = {"structural": 0, "bias": 0, "mixed": 0}
        for t in FACE_CONTROL_TYPE.values():
            counts[t] += 1
        assert counts["structural"] == 4
        assert counts["bias"] == 5
        assert counts["mixed"] == 3
        assert sum(counts.values()) == 12


class TestCompositionAggregation:
    def test_empty_coordinate(self):
        result = compute_control_type_composition({})
        assert result["structural_share"] == 0.0
        assert result["bias_share"] == 0.0
        assert result["mixed_share"] == 0.0
        assert result["dominant_control_type"] == "none"

    def test_all_zero_weights(self):
        coord = _coord(**{f: 0.0 for f in ALL_FACES})
        result = compute_control_type_composition(coord)
        assert result["total_weight"] == 0.0
        assert result["dominant_control_type"] == "none"

    def test_engineering_prompt_dominantly_structural(self):
        """Engineering pattern: semiotics/methodology/ontology/praxeology high."""
        coord = _coord(
            semiotics=0.70, methodology=0.65, ontology=0.60, praxeology=0.50,
            ethics=0.10, axiology=0.10, aesthetics=0.10,
            hermeneutics=0.20, heuristics=0.20,
            epistemology=0.40, phenomenology=0.20, teleology=0.25,
        )
        result = compute_control_type_composition(coord)
        assert result["dominant_control_type"] == "structural"
        assert result["structural_share"] > result["bias_share"]
        assert result["structural_share"] > result["mixed_share"]

    def test_policy_prompt_dominantly_bias(self):
        """Policy / moral reasoning: ethics/axiology/hermeneutics high."""
        coord = _coord(
            ethics=0.72, axiology=0.55, hermeneutics=0.50, heuristics=0.30,
            semiotics=0.25, methodology=0.20, ontology=0.20, praxeology=0.20,
            epistemology=0.30, phenomenology=0.20, teleology=0.40,
            aesthetics=0.15,
        )
        result = compute_control_type_composition(coord)
        assert result["dominant_control_type"] == "bias"

    def test_shares_sum_to_one(self):
        coord = _coord(
            semiotics=0.5, methodology=0.4, ethics=0.6, axiology=0.3,
            epistemology=0.5, teleology=0.2,
        )
        result = compute_control_type_composition(coord)
        total = result["structural_share"] + result["bias_share"] + result["mixed_share"]
        assert abs(total - 1.0) < 1e-6

    def test_weight_sums_correct(self):
        coord = _coord(
            semiotics=0.4, methodology=0.3, ontology=0.2, praxeology=0.1,  # struct=1.0
            ethics=0.5, axiology=0.5, aesthetics=0.0, hermeneutics=0.0, heuristics=0.0,  # bias=1.0
            epistemology=0.3, phenomenology=0.4, teleology=0.3,  # mixed=1.0
        )
        result = compute_control_type_composition(coord)
        assert abs(result["structural_weight"] - 1.0) < 1e-4
        assert abs(result["bias_weight"] - 1.0) < 1e-4
        assert abs(result["mixed_weight"] - 1.0) < 1e-4
        assert abs(result["total_weight"] - 3.0) < 1e-4


class TestAnnotateCoordinate:
    def test_per_face_control_type_added(self):
        coord = _coord()
        annotated = annotate_coordinate(coord)
        assert annotated["semiotics"]["control_type"] == "structural"
        assert annotated["ethics"]["control_type"] == "bias"
        assert annotated["epistemology"]["control_type"] == "mixed"

    def test_original_fields_preserved(self):
        coord = _coord(ontology=0.7)
        annotated = annotate_coordinate(coord)
        assert annotated["ontology"]["x"] == 5
        assert annotated["ontology"]["y"] == 5
        assert annotated["ontology"]["weight"] == 0.7

    def test_input_not_mutated(self):
        coord = _coord()
        annotate_coordinate(coord)
        # The original should have no control_type field
        assert "control_type" not in coord["semiotics"]

    def test_empty_input(self):
        assert annotate_coordinate({}) == {}
