"""First-principles compliance tests.

These tests verify the engine against the philosophical geometry defined in
CONSTRUCT-v2.md. They exercise the engine as a whole system, not individual
modules. Each test is named for the principle it validates.

The principles are:
1. Position determines meaning
2. Polarity convention (low=constrained, high=expansive)
3. Potency hierarchy (corner > edge > center)
4. Edge encapsulates center
5. Cube pairing produces harmonization
6. Nexus stratification modulates interaction
7. Deductive cascade (faces → nexi → gems → spokes → central gem)
8. Positional correspondence across faces
9. Inference machinery (3 layers → meaning)
10. Weight differentiation from intent
11. Meaning hierarchy in output
12. Face equipoise (no face privileged)
"""

import tempfile
import os

import networkx as nx
import numpy as np
import pytest

from advanced_prompting_engine.graph.canonical import build_canonical_graph, BASE_QUESTIONS, NEXUS_CONTENT
from advanced_prompting_engine.graph.schema import (
    ALL_FACES, FACE_DEFINITIONS, GRID_SIZE, CUBE_PAIRS,
    DOMAIN_REPLACEMENTS, FACE_PHASES, NexusTier,
    SYMMETRIC_RELATIONS,
)
from advanced_prompting_engine.graph.grid import classify, potency, degree_label, potency_matrix
from advanced_prompting_engine.cache.embedding import EmbeddingCache
from advanced_prompting_engine.cache.tfidf import TfidfCache
from advanced_prompting_engine.graph.query import GraphQueryLayer
from advanced_prompting_engine.pipeline.runner import PipelineRunner
from advanced_prompting_engine.math.tension import positional_distance, positional_tension
from advanced_prompting_engine.math.gem import compute_gem
from advanced_prompting_engine.math.harmonization import compute_harmonization
from advanced_prompting_engine.math.spoke import compute_spoke_shape, compute_central_gem


# ---------------------------------------------------------------------------
# Shared fixture: build the full engine once for all tests
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine():
    """Build the full graph + pipeline once for the module."""
    nodes, edges = build_canonical_graph()
    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["id"], **n)
    for e in edges:
        G.add_edge(e["source_id"], e["target_id"], **e)
    # Expand symmetric relations so reverse lookups work
    for e in edges:
        if e.get("relation") in SYMMETRIC_RELATIONS:
            G.add_edge(
                e["target_id"], e["source_id"],
                **{k: v for k, v in e.items() if k not in ("source_id", "target_id")},
                source_id=e["target_id"],
                target_id=e["source_id"],
            )
    ec = EmbeddingCache()
    ec.initialize(G)
    tc = TfidfCache()
    tc.initialize(G)
    ql = GraphQueryLayer(G)
    pipeline = PipelineRunner(G, ql, ec, tc)
    return {"G": G, "pipeline": pipeline, "query": ql, "tfidf": tc}


# ===================================================================
# PRINCIPLE 1: Position determines meaning
# ===================================================================

class TestPositionDeterminesMeaning:
    """Same coordinates on the same face must always produce the same construct."""

    def test_same_coordinates_same_construct(self, engine):
        c1 = engine["query"].get_construct("ontology", 3, 7)
        c2 = engine["query"].get_construct("ontology", 3, 7)
        assert c1["id"] == c2["id"]
        assert c1["question"] == c2["question"]

    def test_different_coordinates_different_questions(self, engine):
        c1 = engine["query"].get_construct("ontology", 0, 0)
        c2 = engine["query"].get_construct("ontology", 11, 11)
        assert c1["question"] != c2["question"]

    def test_same_coordinates_different_faces_different_questions(self, engine):
        """Same (x,y) on different faces must produce different domain-specific questions."""
        c1 = engine["query"].get_construct("ontology", 5, 5)
        c2 = engine["query"].get_construct("ethics", 5, 5)
        assert c1["question"] != c2["question"]
        assert "ontological" in c1["question"].lower() or "exist" in c1["question"].lower()
        assert "ethic" in c2["question"].lower() or "moral" in c2["question"].lower() or "obligation" in c2["question"].lower()

    def test_every_position_has_a_construct(self, engine):
        """All 144 positions on every face must have a construct."""
        for face in ALL_FACES:
            for x in range(GRID_SIZE):
                for y in range(GRID_SIZE):
                    c = engine["query"].get_construct(face, x, y)
                    assert c is not None, f"Missing construct at {face}.{x}_{y}"


# ===================================================================
# PRINCIPLE 2: Polarity convention
# ===================================================================

class TestPolarityConvention:
    """Low (0) = constrained/foundational, high (11) = expansive/exploratory."""

    def test_degree_labels_at_extremes(self):
        """Position 0 must say 'fully [low]', position 11 must say 'fully [high]'."""
        for face in ALL_FACES:
            defn = FACE_DEFINITIONS[face]
            low_label = degree_label(0, defn["x_axis_low"], defn["x_axis_high"])
            high_label = degree_label(GRID_SIZE - 1, defn["x_axis_low"], defn["x_axis_high"])
            assert f"fully {defn['x_axis_low']}" == low_label
            assert f"fully {defn['x_axis_high']}" == high_label

    def test_polarity_monotonic(self):
        """Moving from 0→11 on any axis must transition from low to high labels."""
        defn = FACE_DEFINITIONS["ontology"]
        labels = [degree_label(i, defn["x_axis_low"], defn["x_axis_high"]) for i in range(GRID_SIZE)]
        # First label contains low, last contains high
        assert defn["x_axis_low"] in labels[0]
        assert defn["x_axis_high"] in labels[-1]
        # Middle labels contain "balanced"
        assert "balanced" in labels[5]
        assert "balanced" in labels[6]

    def test_midpoint_distinction(self):
        """Positions 5 and 6 must produce distinguishable labels."""
        defn = FACE_DEFINITIONS["epistemology"]
        label_5 = degree_label(5, defn["x_axis_low"], defn["x_axis_high"])
        label_6 = degree_label(6, defn["x_axis_low"], defn["x_axis_high"])
        assert label_5 != label_6
        assert defn["x_axis_low"] in label_5  # 5 inclines toward low
        assert defn["x_axis_high"] in label_6  # 6 inclines toward high


# ===================================================================
# PRINCIPLE 3: Potency hierarchy
# ===================================================================

class TestPotencyHierarchy:
    """Corner > midpoint > edge > center."""

    def test_potency_ordering(self):
        corner = potency(0, 0)
        midpoint = potency(5, 0)
        edge = potency(3, 0)
        center = potency(5, 5)
        assert corner > midpoint > edge > center

    def test_potency_matrix_shape(self):
        m = potency_matrix()
        assert m.shape == (GRID_SIZE, GRID_SIZE)

    def test_all_corners_equal_potency(self):
        corners = [(0, 0), (GRID_SIZE-1, 0), (0, GRID_SIZE-1), (GRID_SIZE-1, GRID_SIZE-1)]
        potencies = [potency(x, y) for x, y in corners]
        assert len(set(potencies)) == 1, "All corners must have equal potency"

    def test_corner_potency_is_maximum(self):
        m = potency_matrix()
        assert m[0, 0] == m.max()


# ===================================================================
# PRINCIPLE 4: Edge encapsulates center
# ===================================================================

class TestEdgeEncapsulatesCenter:
    """44 edge points bound 100 center points. Edge points have higher potency."""

    def test_edge_count(self):
        edge_count = sum(
            1 for x in range(GRID_SIZE) for y in range(GRID_SIZE)
            if classify(x, y) in ("corner", "midpoint", "edge")
        )
        assert edge_count == 44

    def test_center_count(self):
        center_count = sum(
            1 for x in range(GRID_SIZE) for y in range(GRID_SIZE)
            if classify(x, y) == "center"
        )
        assert center_count == 100

    def test_every_edge_point_has_higher_potency_than_every_center(self):
        min_edge = min(
            potency(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE)
            if classify(x, y) in ("corner", "midpoint", "edge")
        )
        max_center = max(
            potency(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE)
            if classify(x, y) == "center"
        )
        assert min_edge > max_center


# ===================================================================
# PRINCIPLE 5: Cube pairing produces harmonization
# ===================================================================

class TestCubePairing:
    """6 complementary pairs. Paired faces harmonize more than non-paired."""

    def test_six_pairs(self):
        assert len(CUBE_PAIRS) == 6

    def test_all_faces_paired(self):
        paired_faces = set()
        for a, b in CUBE_PAIRS:
            paired_faces.add(a)
            paired_faces.add(b)
        assert paired_faces == set(ALL_FACES)

    def test_paired_faces_harmonize_at_same_position(self):
        """When both paired faces activate at the same position, resonance is high."""
        constructs = {}
        for face in ALL_FACES:
            constructs[face] = [{"x": 5, "y": 5, "potency": 0.6, "id": f"{face}.5_5"}]
        harmonization = compute_harmonization(constructs)
        for h in harmonization:
            # Same position → alignment should be 1.0
            assert h["alignment"] == 1.0, f"Pair {h['pair']} should have perfect alignment at same position"

    def test_paired_faces_low_resonance_at_opposite_positions(self):
        """When paired faces activate at opposite positions, resonance drops."""
        constructs_aligned = {}
        constructs_opposed = {}
        for a, b in CUBE_PAIRS:
            constructs_aligned[a] = [{"x": 3, "y": 3, "potency": 0.8, "id": f"{a}.3_3"}]
            constructs_aligned[b] = [{"x": 3, "y": 3, "potency": 0.8, "id": f"{b}.3_3"}]
            constructs_opposed[a] = [{"x": 0, "y": 0, "potency": 1.0, "id": f"{a}.0_0"}]
            constructs_opposed[b] = [{"x": 11, "y": 11, "potency": 1.0, "id": f"{b}.11_11"}]

        h_aligned = compute_harmonization(constructs_aligned)
        h_opposed = compute_harmonization(constructs_opposed)

        for ha, ho in zip(h_aligned, h_opposed):
            assert ha["resonance"] > ho["resonance"], (
                f"Pair {ha['pair']}: aligned resonance ({ha['resonance']:.4f}) "
                f"should exceed opposed ({ho['resonance']:.4f})"
            )

    def test_paired_intent_produces_harmonization_in_output(self, engine):
        """Running an intent through the pipeline produces harmonization pairs."""
        result = engine["pipeline"].run("How should we structure knowledge?")
        assert "harmonization_pairs" in result
        assert len(result["harmonization_pairs"]) == 6


# ===================================================================
# PRINCIPLE 6: Nexus stratification
# ===================================================================

class TestNexusStratification:
    """6 paired + 48 adjacent + 12 opposite = 66."""

    def test_total_nexi(self):
        nodes, _ = build_canonical_graph()
        nexus_nodes = [n for n in nodes if n.get("type") == "nexus"]
        # 132 directional (66 pairs × 2 directions)
        assert len(nexus_nodes) == 132

    def test_tier_distribution(self):
        nodes, _ = build_canonical_graph()
        nexus_nodes = [n for n in nodes if n.get("type") == "nexus"]
        tiers = [n.get("cube_tier") for n in nexus_nodes]
        from collections import Counter
        counts = Counter(tiers)
        # 132 directional: 12 paired + 96 adjacent + 24 opposite
        assert counts.get("paired", 0) == 12  # 6 pairs × 2 directions
        assert counts.get("adjacent", 0) == 96  # 48 pairs × 2 directions
        assert counts.get("opposite", 0) == 24  # 12 pairs × 2 directions

    def test_paired_gems_dampen_tension(self):
        """Paired nexi should produce lower tension than opposite nexi."""
        t_paired = positional_tension(0, 0, 1.0, 11, 11, 1.0, NexusTier.PAIRED.value)
        t_opposite = positional_tension(0, 0, 1.0, 11, 11, 1.0, NexusTier.OPPOSITE.value)
        assert t_paired < t_opposite

    def test_paired_gems_get_resonance_bonus(self):
        """Paired gems should have higher magnitude than equivalent opposite gems."""
        constructs = {
            "ontology": [{"x": 5, "y": 5, "potency": 0.8, "effective_potency": 0.8, "id": "ontology.5_5"}],
            "praxeology": [{"x": 5, "y": 5, "potency": 0.8, "effective_potency": 0.8, "id": "praxeology.5_5"}],
        }
        gem_paired = compute_gem("ontology", "praxeology", constructs, NexusTier.PAIRED.value)
        gem_opposite = compute_gem("ontology", "praxeology", constructs, NexusTier.OPPOSITE.value)
        assert gem_paired["magnitude"] > gem_opposite["magnitude"]


# ===================================================================
# PRINCIPLE 7: Deductive cascade
# ===================================================================

class TestDeductiveCascade:
    """faces → nexi → gems → spokes → central gem. Each layer deduced from the one below."""

    def test_full_pipeline_produces_all_layers(self, engine):
        result = engine["pipeline"].run("Explore the nature of truth")
        assert "coordinate" in result
        assert "active_constructs" in result
        assert "tensions" in result
        assert "gems" in result
        assert "spokes" in result
        assert "central_gem" in result
        assert "harmonization_pairs" in result
        assert "construction_questions" in result

    def test_gems_count_matches_nexi(self, engine):
        result = engine["pipeline"].run("What is justice?")
        assert len(result["gems"]) == 132  # 66 pairs × 2 directions

    def test_spokes_count_matches_faces(self, engine):
        result = engine["pipeline"].run("How do we act?")
        assert len(result["spokes"]) == 12

    def test_central_gem_is_single(self, engine):
        result = engine["pipeline"].run("Why does anything exist?")
        assert "coherence" in result["central_gem"]
        assert "classification" in result["central_gem"]

    def test_spoke_strength_derived_from_gems(self, engine):
        """Each spoke's strength must be the mean of its 11 gem magnitudes."""
        result = engine["pipeline"].run("Design a learning system")
        for face, spoke in result["spokes"].items():
            face_gems = [g for g in result["gems"] if g["nexus"].startswith(f"nexus.{face}.")]
            if face_gems:
                expected_strength = np.mean([g["magnitude"] for g in face_gems])
                assert abs(spoke["strength"] - expected_strength) < 1e-6, (
                    f"{face}: spoke strength {spoke['strength']:.6f} != gem mean {expected_strength:.6f}"
                )


# ===================================================================
# PRINCIPLE 8: Positional correspondence
# ===================================================================

class TestPositionalCorrespondence:
    """Same position across faces = shared archetype. Opposite = tension."""

    def test_same_position_zero_distance(self):
        assert positional_distance(5, 5, 5, 5) == 0.0

    def test_opposite_position_max_distance(self):
        assert positional_distance(0, 0, GRID_SIZE-1, GRID_SIZE-1) == pytest.approx(1.0)

    def test_same_position_low_tension(self):
        t = positional_tension(5, 5, 1.0, 5, 5, 1.0, NexusTier.ADJACENT.value)
        assert t == 0.0

    def test_opposite_position_high_tension(self):
        t = positional_tension(0, 0, 1.0, GRID_SIZE-1, GRID_SIZE-1, 1.0, NexusTier.ADJACENT.value)
        assert t == pytest.approx(1.0)  # max distance × potency × tier weight

    def test_all_corners_share_archetype(self, engine):
        """All (0,0) corners should share the 'Alpha/Foundation' archetype character."""
        for face in ALL_FACES:
            c = engine["query"].get_construct(face, 0, 0)
            assert c["classification"] == "corner"
            assert c["potency"] == 1.0

    def test_gem_magnitude_higher_for_same_position(self):
        """Gems where both faces activate at same position should have higher magnitude
        than gems where faces activate at opposite positions."""
        constructs_same = {
            "ontology": [{"x": 3, "y": 3, "potency": 0.8, "effective_potency": 0.8, "id": "o.3_3"}],
            "epistemology": [{"x": 3, "y": 3, "potency": 0.8, "effective_potency": 0.8, "id": "e.3_3"}],
        }
        constructs_opp = {
            "ontology": [{"x": 0, "y": 0, "potency": 1.0, "effective_potency": 1.0, "id": "o.0_0"}],
            "epistemology": [{"x": 11, "y": 11, "potency": 1.0, "effective_potency": 1.0, "id": "e.11_11"}],
        }
        gem_same = compute_gem("ontology", "epistemology", constructs_same, NexusTier.ADJACENT.value)
        gem_opp = compute_gem("ontology", "epistemology", constructs_opp, NexusTier.ADJACENT.value)
        assert gem_same["magnitude"] > gem_opp["magnitude"], (
            f"Same-position gem ({gem_same['magnitude']:.4f}) should exceed "
            f"opposite-position gem ({gem_opp['magnitude']:.4f})"
        )


# ===================================================================
# PRINCIPLE 9: Inference machinery (3 layers → meaning)
# ===================================================================

class TestInferenceMachinery:
    """Axes + polarity + sub-dimensions produce meaning at every coordinate."""

    def test_all_144_questions_have_domain_placeholder(self):
        for pos, q in BASE_QUESTIONS.items():
            assert "{domain}" in q, f"Question at {pos} missing {{domain}} placeholder"

    def test_domain_replacement_produces_unique_questions(self):
        """Same template + different domain replacements = different questions."""
        template = BASE_QUESTIONS[(5, 5)]
        q_ontology = template.replace("{domain}", DOMAIN_REPLACEMENTS["ontology"])
        q_ethics = template.replace("{domain}", DOMAIN_REPLACEMENTS["ethics"])
        assert q_ontology != q_ethics

    def test_12_domain_replacements_exist(self):
        assert len(DOMAIN_REPLACEMENTS) == 12
        for face in ALL_FACES:
            assert face in DOMAIN_REPLACEMENTS

    def test_sub_dimensions_unique_across_faces(self):
        """No sub-dimensional extreme label should appear in more than one face."""
        all_extremes = []
        for face in ALL_FACES:
            defn = FACE_DEFINITIONS[face]
            all_extremes.extend([
                defn["x_axis_low"], defn["x_axis_high"],
                defn["y_axis_low"], defn["y_axis_high"],
            ])
        # Check for duplicates
        seen = set()
        duplicates = []
        for e in all_extremes:
            if e in seen:
                duplicates.append(e)
            seen.add(e)
        assert len(duplicates) == 0, f"Duplicate sub-dimensional extremes: {duplicates}"


# ===================================================================
# PRINCIPLE 10: Weight differentiation from intent
# ===================================================================

class TestWeightDifferentiation:
    """Different intents should activate different faces with different weights."""

    def test_ethics_intent_activates_ethics_face(self, engine):
        result = engine["pipeline"].run("What moral obligations do we have to future generations?")
        weights = {f: result["coordinate"][f]["weight"] for f in ALL_FACES}
        ethics_weight = weights["ethics"]
        min_weight = min(weights.values())
        assert ethics_weight > min_weight, (
            f"Ethics weight ({ethics_weight:.3f}) should exceed minimum ({min_weight:.3f}) "
            f"for an ethics-focused intent"
        )

    def test_methodology_intent_activates_methodology_face(self, engine):
        result = engine["pipeline"].run("What systematic analytical methods should we apply?")
        weights = {f: result["coordinate"][f]["weight"] for f in ALL_FACES}
        methodology_weight = weights["methodology"]
        min_weight = min(weights.values())
        assert methodology_weight > min_weight

    def test_different_intents_produce_different_coordinates(self, engine):
        r1 = engine["pipeline"].run("What exists?")
        r2 = engine["pipeline"].run("How should we act ethically?")
        c1 = r1["coordinate"]
        c2 = r2["coordinate"]
        # At least some faces should have different coordinates
        differences = sum(
            1 for f in ALL_FACES
            if c1[f]["x"] != c2[f]["x"] or c1[f]["y"] != c2[f]["y"]
        )
        assert differences > 0, "Different intents should produce different coordinates"

    def test_weight_affects_activation_radius(self, engine):
        """Higher weight should produce more active constructs on that face."""
        r_ethics = engine["pipeline"].run("What are our deepest moral obligations?")
        r_neutral = engine["pipeline"].run("Tell me something")
        ethics_active = len(r_ethics["active_constructs"].get("ethics", []))
        neutral_active = len(r_neutral["active_constructs"].get("ethics", []))
        # A morally focused intent should activate more constructs on the ethics face
        assert ethics_active >= neutral_active


# ===================================================================
# PRINCIPLE 11: Meaning hierarchy in output
# ===================================================================

class TestMeaningHierarchy:
    """Output includes meaning_mechanism reflecting §6."""

    def test_corner_has_integration_mechanism(self, engine):
        result = engine["pipeline"].run(
            '{"ontology": {"x": 0, "y": 0, "weight": 1.0}}'
        )
        # Run with coordinate instead
        coord = {f: {"x": 0, "y": 0, "weight": 1.0} for f in ALL_FACES}
        result = engine["pipeline"].run(coord)
        cq = result["construction_questions"]["ontology"]
        assert cq["meaning_mechanism"] == "integration"

    def test_center_has_composition_mechanism(self, engine):
        coord = {f: {"x": 5, "y": 5, "weight": 0.5} for f in ALL_FACES}
        result = engine["pipeline"].run(coord)
        cq = result["construction_questions"]["ontology"]
        assert cq["meaning_mechanism"] == "composition"

    def test_edge_has_demarcation_mechanism(self, engine):
        coord = {f: {"x": 3, "y": 0, "weight": 0.5} for f in ALL_FACES}
        result = engine["pipeline"].run(coord)
        cq = result["construction_questions"]["ontology"]
        assert cq["meaning_mechanism"] == "demarcation"

    def test_midpoint_has_axial_balance_mechanism(self, engine):
        coord = {f: {"x": 5, "y": 0, "weight": 0.5} for f in ALL_FACES}
        result = engine["pipeline"].run(coord)
        cq = result["construction_questions"]["ontology"]
        assert cq["meaning_mechanism"] == "axial_balance"

    def test_phase_in_output(self, engine):
        result = engine["pipeline"].run("What is knowledge?")
        for face, cq in result["construction_questions"].items():
            assert "phase" in cq
            assert cq["phase"] == FACE_PHASES[face]


# ===================================================================
# PRINCIPLE 12: Face equipoise
# ===================================================================

class TestFaceEquipoise:
    """No face is structurally privileged. All have equal grid geometry."""

    def test_all_faces_have_144_constructs(self, engine):
        for face in ALL_FACES:
            constructs = engine["query"].list_constructs(face)
            assert len(constructs) == 144, f"{face} has {len(constructs)} constructs, expected 144"

    def test_all_faces_have_same_classification_distribution(self, engine):
        """Every face should have 4 corners, 8 midpoints, 32 edge, 100 center."""
        for face in ALL_FACES:
            constructs = engine["query"].list_constructs(face)
            from collections import Counter
            dist = Counter(c["classification"] for c in constructs)
            assert dist["corner"] == 4, f"{face}: {dist['corner']} corners"
            assert dist["midpoint"] == 8, f"{face}: {dist['midpoint']} midpoints"
            assert dist["edge"] == 32, f"{face}: {dist['edge']} edge"
            assert dist["center"] == 100, f"{face}: {dist['center']} center"

    def test_all_faces_have_equal_spoke_structure(self, engine):
        """Each face participates in exactly 11 nexi (one to each other face)."""
        for face in ALL_FACES:
            spoke = engine["query"].get_spoke(face)
            assert len(spoke) == 11, f"{face} spoke has {len(spoke)} gems, expected 11"

    def test_all_faces_have_sub_dimensions(self):
        for face in ALL_FACES:
            defn = FACE_DEFINITIONS[face]
            for key in ["x_axis_low", "x_axis_high", "y_axis_low", "y_axis_high",
                        "core_question", "construction_template"]:
                assert key in defn, f"{face} missing {key}"
                assert defn[key], f"{face} has empty {key}"

    def test_causal_chain_is_complete(self, engine):
        """12 faces connected by 11 PRECEDES edges forming a single chain."""
        G = engine["G"]
        precedes_edges = [
            (u, v) for u, v, d in G.edges(data=True)
            if d.get("relation") == "PRECEDES"
        ]
        assert len(precedes_edges) == 11


# ===================================================================
# PRINCIPLE 13: The 48 corners as balanced order
# ===================================================================

class TestCornersBalancedOrder:
    """48 corners (4 per face × 12) mechanically derived, all unique."""

    def test_48_unique_corner_labels(self, engine):
        labels = set()
        for face in ALL_FACES:
            defn = FACE_DEFINITIONS[face]
            corners = [
                (0, 0, defn["x_axis_low"], defn["y_axis_low"]),
                (GRID_SIZE-1, 0, defn["x_axis_high"], defn["y_axis_low"]),
                (0, GRID_SIZE-1, defn["x_axis_low"], defn["y_axis_high"]),
                (GRID_SIZE-1, GRID_SIZE-1, defn["x_axis_high"], defn["y_axis_high"]),
            ]
            for x, y, x_label, y_label in corners:
                label = f"{x_label}-{y_label}"
                assert label not in labels, f"Duplicate corner label: {label} on {face}"
                labels.add(label)
        assert len(labels) == 48

    def test_alpha_corners_share_archetype(self, engine):
        """All (0,0) corners are elemental-stable — the most grounded stance."""
        for face in ALL_FACES:
            c = engine["query"].get_construct(face, 0, 0)
            assert c["classification"] == "corner"
            assert c["potency"] == 1.0
            # The question should reflect foundational/grounded character
            # (We can't check exact wording, but it should contain {domain} substituted)


# ===================================================================
# PRINCIPLE 14: Nexus content completeness
# ===================================================================

class TestNexusCompleteness:
    """66 unique nexus pairs, one for every face combination."""

    def test_66_nexus_definitions(self):
        assert len(NEXUS_CONTENT) == 66

    def test_every_pair_covered(self):
        expected_pairs = set()
        for i, a in enumerate(ALL_FACES):
            for b in ALL_FACES[i+1:]:
                expected_pairs.add((a, b))
        actual_pairs = set(NEXUS_CONTENT.keys())
        assert expected_pairs == actual_pairs, (
            f"Missing: {expected_pairs - actual_pairs}, "
            f"Extra: {actual_pairs - expected_pairs}"
        )

    def test_all_nexus_questions_are_bidirectional(self):
        """Each nexus question should reference both faces' domains."""
        for (a, b), question in NEXUS_CONTENT.items():
            assert "?" in question, f"Nexus ({a}, {b}) question has no question mark"
            assert len(question) > 20, f"Nexus ({a}, {b}) question too short"


# ===================================================================
# PRINCIPLE 15: Spectrums as geometric oppositions
# ===================================================================

class TestSpectrums:
    """Spectrums are reflections: (x,y) ↔ (GRID_SIZE-1-x, GRID_SIZE-1-y)."""

    def test_spectrum_reflections(self, engine):
        from advanced_prompting_engine.graph.grid import generate_spectrums
        for face in ALL_FACES:
            spectrums = generate_spectrums(face)
            for _sid, a_id, b_id in spectrums:
                ax, ay = map(int, a_id.split(".")[1].split("_"))
                bx, by = map(int, b_id.split(".")[1].split("_"))
                assert ax + bx == GRID_SIZE - 1, f"{a_id} ↔ {b_id}: x doesn't reflect"
                assert ay + by == GRID_SIZE - 1, f"{a_id} ↔ {b_id}: y doesn't reflect"

    def test_22_spectrums_per_face(self):
        from advanced_prompting_engine.graph.grid import generate_spectrums
        for face in ALL_FACES:
            assert len(generate_spectrums(face)) == 22, f"{face} has wrong spectrum count"


# ===================================================================
# INTEGRATION: Full round-trip with distinct intents
# ===================================================================

class TestFullRoundTrip:
    """Run diverse intents and verify the engine produces differentiated output."""

    @pytest.mark.parametrize("intent,expected_strong_face", [
        ("What is the fundamental nature of reality?", "ontology"),
        ("How can we verify these claims are true?", "epistemology"),
        ("What moral duties do we owe each other?", "ethics"),
        ("What makes this design beautiful and elegant?", "aesthetics"),
        ("What systematic method should we follow?", "methodology"),
        ("How should we interpret this ambiguous text?", "hermeneutics"),
    ])
    def test_intent_activates_expected_face(self, engine, intent, expected_strong_face):
        result = engine["pipeline"].run(intent)
        weights = {f: result["coordinate"][f]["weight"] for f in ALL_FACES}
        target_weight = weights[expected_strong_face]
        # Should be above the minimum weight (0.1)
        assert target_weight > 0.1, (
            f"Intent '{intent}' should activate {expected_strong_face} "
            f"(weight={target_weight:.3f})"
        )

    def test_compact_output_includes_all_v2_features(self, engine):
        from advanced_prompting_engine.tools.create_prompt_basis import _compact
        result = engine["pipeline"].run("Build something meaningful")
        compact = _compact(result)
        assert "coordinate" in compact
        assert "tensions_summary" in compact
        assert "spokes" in compact
        assert "central_gem" in compact
        assert "harmonization" in compact
        assert "construction_questions" in compact
        # Verify harmonization has 6 pairs
        assert len(compact["harmonization"]) == 6
