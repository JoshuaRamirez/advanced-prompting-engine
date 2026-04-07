"""Tests for canonical content generation — v2 (12 faces, 12x12 grids)."""

from collections import Counter

from advanced_prompting_engine.graph.canonical import (
    BASE_QUESTIONS,
    CANONICAL_VERSION,
    CENTRAL_GEM_CONTENT,
    NEXUS_CONTENT,
    build_canonical_graph,
    derive_tags,
    generate_central_gem,
    generate_constructs,
    generate_face_nodes,
    generate_nexus_nodes,
    generate_precedes_edges,
    generate_spectrum_edges,
)
from advanced_prompting_engine.graph.schema import (
    ALL_FACES,
    CUBE_PAIRS,
    DOMAIN_REPLACEMENTS,
    NexusTier,
)


class TestBaseQuestions:
    def test_144_positions_covered(self):
        """Every (x,y) from 0-11 x 0-11 must have a base question."""
        for x in range(12):
            for y in range(12):
                assert (x, y) in BASE_QUESTIONS, f"Missing base question for ({x}, {y})"

    def test_exactly_144(self):
        assert len(BASE_QUESTIONS) == 144

    def test_all_use_domain_placeholder(self):
        for pos, q in BASE_QUESTIONS.items():
            assert "{domain}" in q, f"Question at {pos} missing {{domain}} placeholder"


class TestFaceNodes:
    def test_exactly_12(self):
        faces = generate_face_nodes()
        assert len(faces) == 12

    def test_all_face_names(self):
        faces = generate_face_nodes()
        names = {f["id"] for f in faces}
        assert names == set(ALL_FACES)

    def test_face_properties(self):
        for f in generate_face_nodes():
            assert f["type"] == "face"
            assert f["tier"] == 1
            assert f["provenance"] == "canonical"
            assert f["mutable"] is False
            assert "core_question" in f
            assert "construction_template" in f
            assert "x_axis_name" in f
            assert "y_axis_name" in f
            assert "x_axis_low" in f
            assert "x_axis_high" in f
            assert "y_axis_low" in f
            assert "y_axis_high" in f
            assert isinstance(f["causal_order"], int)


class TestConstructs:
    def test_144_per_face(self):
        constructs = generate_constructs("ontology")
        assert len(constructs) == 144

    def test_1728_total(self):
        nodes, _ = build_canonical_graph()
        count = sum(1 for n in nodes if n["type"] == "construct")
        assert count == 1728

    def test_unique_ids(self):
        nodes, _ = build_canonical_graph()
        construct_ids = [n["id"] for n in nodes if n["type"] == "construct"]
        assert len(construct_ids) == len(set(construct_ids)), "Duplicate construct IDs found"

    def test_id_format(self):
        for c in generate_constructs("epistemology")[:20]:  # spot check
            assert "." in c["id"]
            face, pos = c["id"].split(".")
            assert face in ALL_FACES
            x, y = pos.split("_")
            assert 0 <= int(x) <= 11
            assert 0 <= int(y) <= 11

    def test_classification_present(self):
        for c in generate_constructs("axiology"):
            assert c["classification"] in ("corner", "midpoint", "edge", "center")

    def test_potency_present(self):
        for c in generate_constructs("teleology"):
            assert c["potency"] in (1.0, 0.9, 0.8, 0.6)

    def test_question_parameterized(self):
        """Questions should NOT contain {domain} — should be replaced."""
        for c in generate_constructs("phenomenology"):
            assert "{domain}" not in c["question"], f"{c['id']} has unparameterized question"

    def test_question_contains_face_domain(self):
        """Each question should contain the face's domain replacement."""
        for c in generate_constructs("ethics")[:50]:  # spot check
            domain = DOMAIN_REPLACEMENTS["ethics"]
            assert domain in c["question"], f"{c['id']} question missing domain '{domain}'"

    def test_tags_non_empty(self):
        for c in generate_constructs("aesthetics"):
            assert len(c["tags"]) > 0, f"{c['id']} has empty tags"

    def test_condensed_gems_empty(self):
        for c in generate_constructs("praxeology"):
            assert c["condensed_gems"] == []

    def test_face_attribute(self):
        """Each construct carries a 'face' attribute matching its parent."""
        for c in generate_constructs("hermeneutics"):
            assert c["face"] == "hermeneutics"


class TestNexi:
    def test_66_pairs_in_content(self):
        assert len(NEXUS_CONTENT) == 66

    def test_132_directional_nodes(self):
        nodes, _ = generate_nexus_nodes()
        assert len(nodes) == 132

    def test_unique_ids(self):
        nodes, _ = generate_nexus_nodes()
        ids = [n["id"] for n in nodes]
        assert len(ids) == len(set(ids))

    def test_non_empty_content(self):
        nodes, _ = generate_nexus_nodes()
        for n in nodes:
            assert len(n["content"]) > 0

    def test_directional_pairs(self):
        """Each undirected pair should produce both A->B and B->A."""
        nodes, _ = generate_nexus_nodes()
        ids = {n["id"] for n in nodes}
        for a, b in NEXUS_CONTENT:
            assert f"nexus.{a}.{b}" in ids
            assert f"nexus.{b}.{a}" in ids

    def test_cube_tier_present(self):
        """Every nexus node must have a cube_tier attribute."""
        nodes, _ = generate_nexus_nodes()
        valid_tiers = {t.value for t in NexusTier}
        for n in nodes:
            assert "cube_tier" in n, f"{n['id']} missing cube_tier"
            assert n["cube_tier"] in valid_tiers, f"{n['id']} has invalid cube_tier: {n['cube_tier']}"

    def test_paired_tier_for_cube_pairs(self):
        """Cube pair faces should produce 'paired' tier nexi."""
        nodes, _ = generate_nexus_nodes()
        node_map = {n["id"]: n for n in nodes}
        for a, b in CUBE_PAIRS:
            nid = f"nexus.{a}.{b}"
            assert node_map[nid]["cube_tier"] == "paired", f"{nid} should be paired"

    def test_264_nexus_edges(self):
        """132 nexus nodes x 2 edges each (SOURCE + TARGET) = 264."""
        _, edges = generate_nexus_nodes()
        assert len(edges) == 264

    def test_source_face_and_target_face(self):
        """Each nexus node must have source_face and target_face attributes."""
        nodes, _ = generate_nexus_nodes()
        for n in nodes:
            assert n["source_face"] in ALL_FACES
            assert n["target_face"] in ALL_FACES
            assert n["source_face"] != n["target_face"]


class TestCentralGem:
    def test_exists(self):
        gem, edges = generate_central_gem()
        assert gem["id"] == "central_gem"
        assert gem["type"] == "central_gem"
        assert len(gem["content"]) > 0

    def test_12_links(self):
        """Central gem should connect to all 12 faces."""
        _, edges = generate_central_gem()
        assert len(edges) == 12
        targets = {e["target_id"] for e in edges}
        assert targets == set(ALL_FACES)


class TestPrecedesEdges:
    def test_exactly_11(self):
        edges = generate_precedes_edges()
        assert len(edges) == 11


class TestSpectrumEdges:
    def test_22_per_face(self):
        edges = generate_spectrum_edges("ontology")
        assert len(edges) == 22

    def test_264_total(self):
        total = sum(len(generate_spectrum_edges(f)) for f in ALL_FACES)
        assert total == 264


class TestBuildCanonicalGraph:
    def test_total_nodes_1873(self):
        nodes, _ = build_canonical_graph()
        assert len(nodes) == 1873, f"Expected 1873 nodes, got {len(nodes)}"

    def test_total_edges_2279(self):
        _, edges = build_canonical_graph()
        assert len(edges) == 2279, f"Expected 2279 edges, got {len(edges)}"

    def test_node_type_distribution(self):
        nodes, _ = build_canonical_graph()
        counts = Counter(n["type"] for n in nodes)
        assert counts["face"] == 12
        assert counts["construct"] == 1728
        assert counts["nexus"] == 132
        assert counts["central_gem"] == 1

    def test_edge_type_distribution(self):
        _, edges = build_canonical_graph()
        counts = Counter(e["relation"] for e in edges)
        assert counts["HAS_CONSTRUCT"] == 1728
        assert counts["PRECEDES"] == 11
        assert counts["SPECTRUM_OPPOSITION"] == 264
        assert counts["NEXUS_SOURCE"] == 132
        assert counts["NEXUS_TARGET"] == 132
        assert counts["CENTRAL_GEM_LINK"] == 12

    def test_version(self):
        assert CANONICAL_VERSION == "2.0.0"


class TestTagDerivation:
    def test_includes_face_and_classification(self):
        tags = derive_tags("What possibility anchors truth?", "epistemology", "corner")
        assert "epistemology" in tags
        assert "corner" in tags

    def test_removes_stop_words(self):
        tags = derive_tags("What is the nature of this domain?", "ontology", "edge")
        assert "what" not in tags
        assert "is" not in tags
        assert "the" not in tags

    def test_non_empty_result(self):
        tags = derive_tags("What anchors possibility?", "heuristics", "center")
        assert len(tags) >= 3  # at least: anchor, possib, heuristics, center
