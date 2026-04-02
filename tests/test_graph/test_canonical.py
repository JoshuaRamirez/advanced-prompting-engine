"""Tests for canonical content generation — Gate G1.4 through G1.13."""

from advanced_prompting_engine.graph.canonical import (
    BASE_QUESTIONS,
    CANONICAL_CROSS_BRANCH_EDGES,
    CENTRAL_GEM_CONTENT,
    NEXUS_CONTENT,
    REVISITED_QUESTIONS,
    SPECTRUM_QUESTIONS,
    derive_tags,
    generate_all_branches,
    generate_all_canonical,
    generate_all_constructs,
    generate_all_edges,
    generate_all_nexi,
    generate_central_gem,
)
from advanced_prompting_engine.graph.schema import ALL_BRANCHES, DOMAIN_REPLACEMENTS


class TestBaseQuestions:
    def test_100_positions_covered(self):
        """Every (x,y) from 0-9 × 0-9 must have a base question."""
        for x in range(10):
            for y in range(10):
                assert (x, y) in BASE_QUESTIONS, f"Missing base question for ({x}, {y})"

    def test_all_use_domain_placeholder(self):
        for pos, q in BASE_QUESTIONS.items():
            assert "{domain}" in q, f"Question at {pos} missing {{domain}} placeholder"


class TestBranches:
    def test_exactly_10(self):
        branches = generate_all_branches()
        assert len(branches) == 10

    def test_all_branch_names(self):
        branches = generate_all_branches()
        names = {b["id"] for b in branches}
        assert names == set(ALL_BRANCHES)

    def test_branch_properties(self):
        for b in generate_all_branches():
            assert b["type"] == "branch"
            assert b["tier"] == 1
            assert b["provenance"] == "canonical"
            assert b["mutable"] is False
            assert "core_question" in b
            assert "construction_template" in b
            assert "x_axis_name" in b
            assert "y_axis_name" in b
            assert isinstance(b["causal_order"], int)


class TestConstructs:
    def test_exactly_1000(self):
        constructs = generate_all_constructs()
        assert len(constructs) == 1000

    def test_100_per_branch(self):
        constructs = generate_all_constructs()
        for branch in ALL_BRANCHES:
            count = sum(1 for c in constructs if c["branch"] == branch)
            assert count == 100, f"{branch} has {count} constructs, expected 100"

    def test_unique_ids(self):
        constructs = generate_all_constructs()
        ids = [c["id"] for c in constructs]
        assert len(ids) == len(set(ids)), "Duplicate construct IDs found"

    def test_id_format(self):
        for c in generate_all_constructs()[:20]:  # spot check
            assert "." in c["id"]
            branch, pos = c["id"].split(".")
            assert branch in ALL_BRANCHES
            x, y = pos.split("_")
            assert 0 <= int(x) <= 9
            assert 0 <= int(y) <= 9

    def test_classification_present(self):
        for c in generate_all_constructs():
            assert c["classification"] in ("corner", "midpoint", "edge", "center")

    def test_potency_present(self):
        for c in generate_all_constructs():
            assert c["potency"] in (1.0, 0.9, 0.8, 0.6)

    def test_question_parameterized(self):
        """Questions should NOT contain {domain} — should be replaced."""
        for c in generate_all_constructs():
            assert "{domain}" not in c["question"], f"{c['id']} has unparameterized question"

    def test_question_contains_branch_domain(self):
        """Each question should contain the branch's domain replacement."""
        constructs = generate_all_constructs()
        for c in constructs[:50]:  # spot check
            domain = DOMAIN_REPLACEMENTS[c["branch"]]
            assert domain in c["question"], f"{c['id']} question missing domain '{domain}'"

    def test_tags_non_empty(self):
        for c in generate_all_constructs():
            assert len(c["tags"]) > 0, f"{c['id']} has empty tags"

    def test_question_revisited_only_at_4_4_and_9_9(self):
        for c in generate_all_constructs():
            if (c["x"], c["y"]) in ((4, 4), (9, 9)):
                assert c["question_revisited"] is not None, f"{c['id']} should have question_revisited"
            else:
                assert c["question_revisited"] is None, f"{c['id']} should NOT have question_revisited"

    def test_condensed_gems_empty(self):
        for c in generate_all_constructs():
            assert c["condensed_gems"] == []


class TestNexi:
    def test_exactly_90(self):
        nexi = generate_all_nexi()
        assert len(nexi) == 90

    def test_unique_ids(self):
        nexi = generate_all_nexi()
        ids = [n["id"] for n in nexi]
        assert len(ids) == len(set(ids))

    def test_non_empty_content(self):
        for n in generate_all_nexi():
            assert len(n["content"]) > 0

    def test_directional_pairs(self):
        """Each undirected pair should produce both A→B and B→A."""
        nexi = generate_all_nexi()
        ids = {n["id"] for n in nexi}
        for a, b in NEXUS_CONTENT:
            assert f"nexus.{a}.{b}" in ids
            assert f"nexus.{b}.{a}" in ids


class TestCentralGem:
    def test_exists(self):
        gem = generate_central_gem()
        assert gem["id"] == "central_gem"
        assert gem["type"] == "central_gem"
        assert len(gem["content"]) > 0


class TestEdges:
    def test_total_1629(self):
        edges = generate_all_edges()
        assert len(edges) == 1629, f"Expected 1629 edges, got {len(edges)}"

    def test_edge_type_distribution(self):
        edges = generate_all_edges()
        from collections import Counter
        counts = Counter(e["relation"] for e in edges)
        assert counts["HAS_CONSTRUCT"] == 1000
        assert counts["PRECEDES"] == 9
        assert counts["SPECTRUM_OPPOSITION"] == 180
        assert counts["NEXUS_SOURCE"] == 90
        assert counts["NEXUS_TARGET"] == 90
        assert counts["CENTRAL_GEM_LINK"] == 90


class TestFullCanonical:
    def test_total_nodes_1101(self):
        nodes, edges = generate_all_canonical()
        assert len(nodes) == 1101, f"Expected 1101 nodes, got {len(nodes)}"

    def test_total_edges_1629(self):
        nodes, edges = generate_all_canonical()
        assert len(edges) == 1629, f"Expected 1629 edges, got {len(edges)}"

    def test_node_type_distribution(self):
        nodes, _ = generate_all_canonical()
        from collections import Counter
        counts = Counter(n["type"] for n in nodes)
        assert counts["branch"] == 10
        assert counts["construct"] == 1000
        assert counts["nexus"] == 90
        assert counts["central_gem"] == 1


class TestTagDerivation:
    def test_includes_branch_and_classification(self):
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


class TestCrossBranchEdges:
    """Integrity checks for CANONICAL_CROSS_BRANCH_EDGES."""

    def test_all_source_ids_valid(self):
        nodes, _ = generate_all_canonical()
        node_ids = {n["id"] for n in nodes}
        for src, tgt, rel, strength, nexus_pair, justification in CANONICAL_CROSS_BRANCH_EDGES:
            assert src in node_ids, f"Invalid source_id: {src}"

    def test_all_target_ids_valid(self):
        nodes, _ = generate_all_canonical()
        node_ids = {n["id"] for n in nodes}
        for src, tgt, rel, strength, nexus_pair, justification in CANONICAL_CROSS_BRANCH_EDGES:
            assert tgt in node_ids, f"Invalid target_id: {tgt}"

    def test_no_same_branch_edges(self):
        for src, tgt, rel, strength, nexus_pair, justification in CANONICAL_CROSS_BRANCH_EDGES:
            src_branch = src.split(".")[0]
            tgt_branch = tgt.split(".")[0]
            assert src_branch != tgt_branch, f"Same-branch edge: {src} → {tgt}"

    def test_no_contradictions(self):
        """No pair should have both COMPATIBLE_WITH and TENSIONS_WITH."""
        pairs = {}
        for src, tgt, rel, strength, nexus_pair, justification in CANONICAL_CROSS_BRANCH_EDGES:
            pair = tuple(sorted([src, tgt]))
            if pair not in pairs:
                pairs[pair] = set()
            pairs[pair].add(rel)
        for pair, rels in pairs.items():
            assert not ({"COMPATIBLE_WITH", "TENSIONS_WITH"} <= rels), \
                f"Contradiction: {pair} has both COMPATIBLE_WITH and TENSIONS_WITH"

    def test_every_nexus_pair_represented(self):
        nexus_pairs = {e[4] for e in CANONICAL_CROSS_BRANCH_EDGES}
        # All 45 pairs should be represented
        assert len(nexus_pairs) == 45, f"Expected 45 nexus pairs, got {len(nexus_pairs)}: missing pairs"

    def test_all_relations_valid(self):
        valid = {"COMPATIBLE_WITH", "TENSIONS_WITH", "REQUIRES", "EXCLUDES"}
        for src, tgt, rel, strength, nexus_pair, justification in CANONICAL_CROSS_BRANCH_EDGES:
            assert rel in valid, f"Invalid relation: {rel} on {src} → {tgt}"

    def test_strengths_in_range(self):
        for src, tgt, rel, strength, nexus_pair, justification in CANONICAL_CROSS_BRANCH_EDGES:
            assert 0 < strength <= 1.0, f"Strength {strength} out of range on {src} → {tgt}"

    def test_edge_count(self):
        assert len(CANONICAL_CROSS_BRANCH_EDGES) == 170
