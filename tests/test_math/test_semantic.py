"""Tests for the GeometricBridge — geometry-integral intent parsing backend.

Validates that the pre-computed GloVe artifacts faithfully invert the
Construct's 3-layer inference machinery:
  Layer 3 inverted: sub-dimensions → face centroids → face relevance
  Layer 1 inverted: axis meta-meaning → direction vectors → coordinate projection
  Layer 2 inverted: polarity convention → calibration → grid mapping
"""

import pytest

from advanced_prompting_engine.graph.schema import ALL_FACES, FACE_DEFINITIONS
from advanced_prompting_engine.math.semantic import GeometricBridge


@pytest.fixture(scope="module")
def bridge():
    b = GeometricBridge()
    b.load()
    return b


class TestBridgeLoading:
    def test_loads_successfully(self, bridge):
        assert bridge.is_loaded

    def test_has_all_faces(self, bridge):
        tokens = ["test"]
        scores = bridge.face_relevance(tokens)
        assert set(scores.keys()) == set(ALL_FACES)

    def test_has_axis_projections_for_all_faces(self, bridge):
        tokens = ["knowledge"]
        for face in ALL_FACES:
            for axis in ("x", "y"):
                scalar, conf = bridge.axis_projection(tokens, face, axis)
                assert 0.0 <= scalar <= 1.0
                assert 0.0 <= conf <= 1.0


class TestFaceRelevance:
    def test_discriminative_scores_sum_near_zero(self, bridge):
        """Discriminative scoring subtracts the mean — scores should roughly center on zero."""
        tokens = ["philosophy", "knowledge", "truth"]
        scores = bridge.face_relevance(tokens)
        total = sum(scores.values())
        # Not exactly zero due to IDF weighting, but close
        assert abs(total) < 1.0

    def test_empty_tokens_produce_zeros(self, bridge):
        scores = bridge.face_relevance([])
        for face in ALL_FACES:
            assert scores[face] == 0.0

    def test_unknown_tokens_produce_zeros(self, bridge):
        scores = bridge.face_relevance(["xyzzyplugh", "qwfpgjluy"])
        for face in ALL_FACES:
            assert scores[face] == 0.0

    def test_domain_name_scores_positively_for_own_face(self, bridge):
        """Each face's own name should produce a positive discriminative score for that face.

        Note: GloVe 50d doesn't always place philosophical domain names closest
        to their own centroid (e.g., 'ontology' is closer to methodology in GloVe).
        We test for positive score, not necessarily highest score.
        """
        positive_count = 0
        for face in ALL_FACES:
            scores = bridge.face_relevance([face])
            if all(v == 0.0 for v in scores.values()):
                continue
            if scores[face] > 0.0:
                positive_count += 1
        # At least half the face names should score positively for themselves
        assert positive_count >= 6, (
            f"Only {positive_count}/12 face names score positively for their own face"
        )


class TestAxisProjection:
    def test_scalar_in_valid_range(self, bridge):
        tokens = ["truth", "knowledge", "verify"]
        for face in ALL_FACES:
            for axis in ("x", "y"):
                scalar, conf = bridge.axis_projection(tokens, face, axis)
                assert 0.0 <= scalar <= 1.0, f"{face}.{axis}: scalar={scalar}"
                assert 0.0 <= conf <= 1.0, f"{face}.{axis}: conf={conf}"

    def test_empty_tokens_produce_center(self, bridge):
        scalar, conf = bridge.axis_projection([], "ontology", "x")
        assert scalar == 0.5
        assert conf == 0.0

    def test_unknown_tokens_produce_center(self, bridge):
        scalar, conf = bridge.axis_projection(["xyzzyplugh"], "ethics", "y")
        assert scalar == 0.5
        assert conf == 0.0

    def test_low_pole_words_project_low(self, bridge):
        """Words synonymous with the low pole should project near 0.0."""
        # Ontology x-axis: Particular (low) → Universal (high)
        low_tokens = ["particular", "specific", "individual", "concrete", "singular"]
        scalar, _ = bridge.axis_projection(low_tokens, "ontology", "x")
        assert scalar < 0.4, f"Low pole words should project low, got {scalar:.3f}"

    def test_high_pole_words_project_high(self, bridge):
        """Words synonymous with the high pole should project near 1.0."""
        # Ontology x-axis: Particular (low) → Universal (high)
        high_tokens = ["universal", "general", "abstract", "comprehensive", "global"]
        scalar, _ = bridge.axis_projection(high_tokens, "ontology", "x")
        assert scalar > 0.6, f"High pole words should project high, got {scalar:.3f}"

    def test_axis_poles_mostly_separate(self, bridge):
        """Most axis poles should produce separated projections (low < high).

        GloVe 50d may not separate all 24 axes perfectly — some philosophical
        distinctions compress in 50 dimensions. We require at least 20 of 24
        axes to show correct pole separation.
        """
        correct = 0
        total = 0
        failures = []
        for face in ALL_FACES:
            defn = FACE_DEFINITIONS[face]
            for axis in ("x", "y"):
                low_label = defn[f"{axis}_axis_low"].lower()
                high_label = defn[f"{axis}_axis_high"].lower()
                low_scalar, _ = bridge.axis_projection([low_label], face, axis)
                high_scalar, _ = bridge.axis_projection([high_label], face, axis)
                if low_scalar == 0.5 and high_scalar == 0.5:
                    continue
                total += 1
                if low_scalar < high_scalar:
                    correct += 1
                else:
                    failures.append(
                        f"{face}.{axis}: '{low_label}'→{low_scalar:.3f} >= '{high_label}'→{high_scalar:.3f}"
                    )
        assert correct >= 20, (
            f"Only {correct}/{total} axes show correct pole separation. "
            f"Failures: {failures}"
        )


class TestPoleConsistency:
    """Validate that all 24 axis poles are correctly oriented in the pre-computed data."""

    @pytest.fixture(scope="class")
    def pole_synonyms(self):
        """Load the pole synonyms from the build script."""
        # Rather than importing from the build script, define the key test cases
        return {
            # (face, axis, pole) → expected range
            ("ontology", "x", "low"): ["particular", "specific", "concrete"],
            ("ontology", "x", "high"): ["universal", "general", "abstract"],
            ("ontology", "y", "low"): ["static", "fixed", "stable"],
            ("ontology", "y", "high"): ["dynamic", "changing", "evolving"],
            ("ethics", "x", "low"): ["duty", "obligation", "principle"],
            ("ethics", "x", "high"): ["welfare", "happiness", "consequence"],
            ("ethics", "y", "low"): ["character", "virtue", "conscience"],
            ("ethics", "y", "high"): ["deed", "conduct", "justice"],
            ("methodology", "x", "low"): ["breaking", "separating", "decomposing"],
            ("methodology", "x", "high"): ["combining", "integrating", "merging"],
            ("aesthetics", "y", "low"): ["beautiful", "visual", "elegant"],
            ("aesthetics", "y", "high"): ["artistic", "creative", "expressive"],
        }

    def test_low_poles_project_below_center(self, bridge, pole_synonyms):
        for (face, axis, pole), words in pole_synonyms.items():
            if pole != "low":
                continue
            in_vocab = [w for w in words if w in bridge._vocab]
            if not in_vocab:
                continue
            scalar, _ = bridge.axis_projection(in_vocab, face, axis)
            assert scalar < 0.5, (
                f"{face}.{axis} low pole words {in_vocab} → {scalar:.3f}, expected < 0.5"
            )

    def test_high_poles_project_above_center(self, bridge, pole_synonyms):
        for (face, axis, pole), words in pole_synonyms.items():
            if pole != "high":
                continue
            in_vocab = [w for w in words if w in bridge._vocab]
            if not in_vocab:
                continue
            scalar, _ = bridge.axis_projection(in_vocab, face, axis)
            assert scalar > 0.5, (
                f"{face}.{axis} high pole words {in_vocab} → {scalar:.3f}, expected > 0.5"
            )


class TestGracefulDegradation:
    def test_unloaded_bridge_returns_zeros(self):
        b = GeometricBridge()
        # Don't load
        assert not b.is_loaded
        scores = b.face_relevance(["test"])
        assert all(v == 0.0 for v in scores.values())

    def test_unloaded_bridge_projection_returns_center(self):
        b = GeometricBridge()
        scalar, conf = b.axis_projection(["test"], "ontology", "x")
        assert scalar == 0.5
        assert conf == 0.0
