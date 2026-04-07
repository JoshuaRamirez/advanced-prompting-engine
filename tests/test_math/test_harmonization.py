"""Tests for harmonization scoring — paired face resonance (v2)."""

from advanced_prompting_engine.graph.schema import CUBE_PAIRS
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
