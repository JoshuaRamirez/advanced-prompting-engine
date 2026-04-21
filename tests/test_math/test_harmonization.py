"""Tests for harmonization scoring — paired face resonance (v2)
with directional resonance added in v4 (ADR-014)."""

from advanced_prompting_engine.graph.schema import CUBE_PAIRS, CUBE_PAIR_DIRECTIONS
from advanced_prompting_engine.math.harmonization import compute_harmonization


class TestComputeHarmonization:
    def test_all_six_pairs_returned(self):
        """compute_harmonization always returns exactly 6 results (one per cube pair)."""
        active = {face: [] for pair in CUBE_PAIRS for face in pair}
        results = compute_harmonization(active)
        assert len(results) == 6
        returned_pairs = [tuple(r["pair"]) for r in results]
        for pair in CUBE_PAIRS:
            assert pair in returned_pairs

    def test_perfect_alignment_high_resonance(self):
        """Same positions on both paired faces → alignment=1.0, high resonance."""
        active = {
            "ontology": [
                {"id": "ontology.5_5", "x": 5, "y": 5, "potency": 1.0},
                {"id": "ontology.3_3", "x": 3, "y": 3, "potency": 1.0},
            ],
            "praxeology": [
                {"id": "praxeology.5_5", "x": 5, "y": 5, "potency": 1.0},
                {"id": "praxeology.3_3", "x": 3, "y": 3, "potency": 1.0},
            ],
            # Other faces empty
            "epistemology": [], "methodology": [],
            "axiology": [], "ethics": [],
            "teleology": [], "heuristics": [],
            "phenomenology": [], "aesthetics": [],
            "semiotics": [], "hermeneutics": [],
        }
        results = compute_harmonization(active)
        onto_prax = next(r for r in results if r["pair"] == ["ontology", "praxeology"])
        assert onto_prax["alignment"] == 1.0
        assert onto_prax["resonance"] > 0

    def test_opposite_positions_low_alignment(self):
        """Maximally distant positions → low alignment, low resonance."""
        active = {
            "ontology": [{"id": "ontology.0_0", "x": 0, "y": 0, "potency": 1.0}],
            "praxeology": [{"id": "praxeology.11_11", "x": 11, "y": 11, "potency": 1.0}],
            "epistemology": [], "methodology": [],
            "axiology": [], "ethics": [],
            "teleology": [], "heuristics": [],
            "phenomenology": [], "aesthetics": [],
            "semiotics": [], "hermeneutics": [],
        }
        results = compute_harmonization(active)
        onto_prax = next(r for r in results if r["pair"] == ["ontology", "praxeology"])
        assert onto_prax["alignment"] < 0.1  # near zero alignment
        assert onto_prax["resonance"] < onto_prax["coverage_a"]  # resonance penalized

    def test_one_face_empty_zero_resonance(self):
        """One face in a pair has no activations → resonance = 0."""
        active = {
            "ontology": [{"id": "ontology.5_5", "x": 5, "y": 5, "potency": 1.0}],
            "praxeology": [],  # empty paired face
            "epistemology": [], "methodology": [],
            "axiology": [], "ethics": [],
            "teleology": [], "heuristics": [],
            "phenomenology": [], "aesthetics": [],
            "semiotics": [], "hermeneutics": [],
        }
        results = compute_harmonization(active)
        onto_prax = next(r for r in results if r["pair"] == ["ontology", "praxeology"])
        assert onto_prax["resonance"] == 0.0
        assert onto_prax["alignment"] == 0.0
        assert onto_prax["coverage_b"] == 0.0

    def test_both_faces_empty_zero_resonance(self):
        """Both faces empty → all zeros."""
        active = {face: [] for pair in CUBE_PAIRS for face in pair}
        results = compute_harmonization(active)
        for r in results:
            assert r["resonance"] == 0.0
            assert r["alignment"] == 0.0

    def test_coverage_scales_with_potency(self):
        """More activated potency → higher coverage ratio."""
        active_small = {
            "epistemology": [{"id": "epistemology.5_5", "x": 5, "y": 5, "potency": 0.5}],
            "methodology": [{"id": "methodology.5_5", "x": 5, "y": 5, "potency": 0.5}],
            "ontology": [], "praxeology": [],
            "axiology": [], "ethics": [],
            "teleology": [], "heuristics": [],
            "phenomenology": [], "aesthetics": [],
            "semiotics": [], "hermeneutics": [],
        }
        active_large = {
            "epistemology": [
                {"id": "epistemology.5_5", "x": 5, "y": 5, "potency": 1.0},
                {"id": "epistemology.3_3", "x": 3, "y": 3, "potency": 1.0},
                {"id": "epistemology.7_7", "x": 7, "y": 7, "potency": 1.0},
            ],
            "methodology": [
                {"id": "methodology.5_5", "x": 5, "y": 5, "potency": 1.0},
                {"id": "methodology.3_3", "x": 3, "y": 3, "potency": 1.0},
                {"id": "methodology.7_7", "x": 7, "y": 7, "potency": 1.0},
            ],
            "ontology": [], "praxeology": [],
            "axiology": [], "ethics": [],
            "teleology": [], "heuristics": [],
            "phenomenology": [], "aesthetics": [],
            "semiotics": [], "hermeneutics": [],
        }
        results_small = compute_harmonization(active_small)
        results_large = compute_harmonization(active_large)
        ep_small = next(r for r in results_small if r["pair"] == ["epistemology", "methodology"])
        ep_large = next(r for r in results_large if r["pair"] == ["epistemology", "methodology"])
        assert ep_large["resonance"] > ep_small["resonance"]

    def test_resonance_requires_both_alignment_and_coverage(self):
        """High alignment with low coverage should produce lower resonance
        than high alignment with high coverage."""
        # High alignment, low coverage (1 point each)
        active_thin = {
            "semiotics": [{"id": "semiotics.5_5", "x": 5, "y": 5, "potency": 0.6}],
            "hermeneutics": [{"id": "hermeneutics.5_5", "x": 5, "y": 5, "potency": 0.6}],
            "ontology": [], "praxeology": [],
            "epistemology": [], "methodology": [],
            "axiology": [], "ethics": [],
            "teleology": [], "heuristics": [],
            "phenomenology": [], "aesthetics": [],
        }
        # High alignment, higher coverage (3 points each, same positions)
        active_thick = {
            "semiotics": [
                {"id": "semiotics.5_5", "x": 5, "y": 5, "potency": 1.0},
                {"id": "semiotics.3_3", "x": 3, "y": 3, "potency": 1.0},
                {"id": "semiotics.8_8", "x": 8, "y": 8, "potency": 1.0},
            ],
            "hermeneutics": [
                {"id": "hermeneutics.5_5", "x": 5, "y": 5, "potency": 1.0},
                {"id": "hermeneutics.3_3", "x": 3, "y": 3, "potency": 1.0},
                {"id": "hermeneutics.8_8", "x": 8, "y": 8, "potency": 1.0},
            ],
            "ontology": [], "praxeology": [],
            "epistemology": [], "methodology": [],
            "axiology": [], "ethics": [],
            "teleology": [], "heuristics": [],
            "phenomenology": [], "aesthetics": [],
        }
        thin = compute_harmonization(active_thin)
        thick = compute_harmonization(active_thick)
        sem_thin = next(r for r in thin if r["pair"] == ["semiotics", "hermeneutics"])
        sem_thick = next(r for r in thick if r["pair"] == ["semiotics", "hermeneutics"])
        assert sem_thick["resonance"] > sem_thin["resonance"]


# ---------------------------------------------------------------------------
# Directional resonance tests (ADR-014, v4 of face-importance-ranking report)
# ---------------------------------------------------------------------------

def _empty_faces() -> dict:
    """Return an all-faces-empty active_constructs dict."""
    return {face: [] for pair in CUBE_PAIRS for face in pair}


class TestCubePairDirections:
    def test_all_six_pairs_have_directions(self):
        """Every cube pair must have a grounding direction defined."""
        assert len(CUBE_PAIR_DIRECTIONS) == 6

    def test_directions_are_valid_faces(self):
        """Each direction mapping uses valid faces from CUBE_PAIRS."""
        all_faces_in_pairs = {f for pair in CUBE_PAIRS for f in pair}
        for grounding, grounded in CUBE_PAIR_DIRECTIONS.items():
            assert grounding in all_faces_in_pairs
            assert grounded in all_faces_in_pairs

    def test_directions_cover_every_pair(self):
        """Each CUBE_PAIR has exactly one of its faces as a grounding key."""
        for face_a, face_b in CUBE_PAIRS:
            a_grounds = CUBE_PAIR_DIRECTIONS.get(face_a) == face_b
            b_grounds = CUBE_PAIR_DIRECTIONS.get(face_b) == face_a
            assert a_grounds or b_grounds, f"No direction for pair ({face_a}, {face_b})"
            assert not (a_grounds and b_grounds), f"Circular direction for pair ({face_a}, {face_b})"

    def test_known_groundings(self):
        """Spot-check known grounding directions per the report."""
        assert CUBE_PAIR_DIRECTIONS["ontology"] == "praxeology"
        assert CUBE_PAIR_DIRECTIONS["epistemology"] == "methodology"
        assert CUBE_PAIR_DIRECTIONS["ethics"] == "axiology"
        assert CUBE_PAIR_DIRECTIONS["teleology"] == "heuristics"
        assert CUBE_PAIR_DIRECTIONS["phenomenology"] == "aesthetics"
        assert CUBE_PAIR_DIRECTIONS["semiotics"] == "hermeneutics"


class TestDirectionalResonance:
    def test_output_includes_directional_fields(self):
        """Every pair result includes directional_resonance and face labels."""
        active = _empty_faces()
        results = compute_harmonization(active)
        for r in results:
            assert "directional_resonance" in r
            assert "grounding_face" in r
            assert "grounded_face" in r

    def test_grounding_face_matches_direction_mapping(self):
        """grounding_face in output matches CUBE_PAIR_DIRECTIONS."""
        active = _empty_faces()
        results = compute_harmonization(active)
        for r in results:
            if r["grounding_face"] is not None:
                assert CUBE_PAIR_DIRECTIONS[r["grounding_face"]] == r["grounded_face"]

    def test_zero_when_grounding_empty(self):
        """If the grounding face has no activations, directional_resonance is 0."""
        active = _empty_faces()
        # praxeology activated, ontology empty (grounded without grounding)
        active["praxeology"] = [{"id": "p1", "x": 5, "y": 5, "potency": 0.8}]
        results = compute_harmonization(active)
        onto_prax = next(r for r in results if r["pair"] == ["ontology", "praxeology"])
        assert onto_prax["directional_resonance"] == 0.0

    def test_zero_when_grounded_empty(self):
        """If the grounded face has no activations, directional_resonance is 0."""
        active = _empty_faces()
        active["ontology"] = [
            {"id": "o1", "x": 5, "y": 5, "potency": 0.9},
            {"id": "o2", "x": 3, "y": 3, "potency": 0.9},
        ]
        results = compute_harmonization(active)
        onto_prax = next(r for r in results if r["pair"] == ["ontology", "praxeology"])
        assert onto_prax["directional_resonance"] == 0.0

    def test_aligned_both_present_high_directional(self):
        """Both present + aligned → directional_resonance > 0."""
        active = _empty_faces()
        active["ontology"] = [{"id": "o1", "x": 5, "y": 5, "potency": 0.9}]
        active["praxeology"] = [{"id": "p1", "x": 5, "y": 5, "potency": 0.9}]
        results = compute_harmonization(active)
        onto_prax = next(r for r in results if r["pair"] == ["ontology", "praxeology"])
        assert onto_prax["directional_resonance"] > 0.0

    def test_inherited_plan_pattern_directional_higher_than_symmetric(self):
        """Field-observation case: ontology heavy + praxeology sparse-but-aligned.
        Directional resonance should be meaningfully higher than the
        symmetric resonance because directional credits the grounding-face
        coverage alone.
        """
        active = _empty_faces()
        # Dense ontology, sparse but aligned praxeology
        active["ontology"] = [
            {"id": f"o{i}", "x": i, "y": i, "potency": 0.8}
            for i in range(2, 10)
        ]
        active["praxeology"] = [
            {"id": "p1", "x": 5, "y": 5, "potency": 0.6},
        ]
        results = compute_harmonization(active)
        onto_prax = next(r for r in results if r["pair"] == ["ontology", "praxeology"])
        # Directional should be noticeably higher because grounding face's
        # high coverage carries the metric even when grounded is sparse.
        assert onto_prax["directional_resonance"] > onto_prax["resonance"]
