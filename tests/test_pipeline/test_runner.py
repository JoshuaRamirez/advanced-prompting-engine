"""End-to-end pipeline runner tests — CHECKPOINT 4.

Tests the full 8-stage pipeline with the real canonical graph.
"""

from __future__ import annotations

import networkx as nx
import pytest

from advanced_prompting_engine.cache.embedding import EmbeddingCache
from advanced_prompting_engine.cache.tfidf import TfidfCache
from advanced_prompting_engine.graph.canonical import generate_all_canonical
from advanced_prompting_engine.graph.query import GraphQueryLayer
from advanced_prompting_engine.graph.schema import ALL_BRANCHES, SYMMETRIC_RELATIONS
from advanced_prompting_engine.pipeline.runner import PipelineRunner


@pytest.fixture(scope="module")
def full_pipeline():
    """Build the full canonical graph + caches + pipeline. Module-scoped for speed."""
    nodes, edges = generate_all_canonical()

    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["id"], **n)
    for e in edges:
        G.add_edge(e["source_id"], e["target_id"], **e)
        # Add reverse for symmetric relations
        if e.get("relation") in SYMMETRIC_RELATIONS:
            rev = {k: v for k, v in e.items() if k not in ("source_id", "target_id")}
            G.add_edge(e["target_id"], e["source_id"],
                       source_id=e["target_id"], target_id=e["source_id"], **rev)

    query = GraphQueryLayer(G)
    emb_cache = EmbeddingCache()
    emb_cache.initialize(G)
    tfidf_cache = TfidfCache()
    tfidf_cache.initialize(G)

    runner = PipelineRunner(G, query, emb_cache, tfidf_cache)
    return runner


class TestIntentInput:
    def test_basic_intent(self, full_pipeline):
        result = full_pipeline.run("thorough code review with security focus")
        assert result is not None
        assert "coordinate" in result
        assert "active_constructs" in result
        assert "construction_questions" in result

    def test_all_10_branches_in_coordinate(self, full_pipeline):
        result = full_pipeline.run("analyze the ethical implications of this decision")
        for branch in ALL_BRANCHES:
            assert branch in result["coordinate"]
            entry = result["coordinate"][branch]
            assert 0 <= entry["x"] <= 9
            assert 0 <= entry["y"] <= 9
            assert entry["weight"] > 0

    def test_construction_questions_all_branches(self, full_pipeline):
        result = full_pipeline.run("design a learning system")
        assert len(result["construction_questions"]) == 10
        for branch in ALL_BRANCHES:
            cq = result["construction_questions"][branch]
            assert "template" in cq
            assert "active_question" in cq
            assert "classification" in cq
            assert "potency" in cq
            assert "spoke_profile" in cq

    def test_spokes_all_present(self, full_pipeline):
        result = full_pipeline.run("build a bridge between theory and practice")
        assert len(result["spokes"]) == 10
        for branch in ALL_BRANCHES:
            spoke = result["spokes"][branch]
            assert "strength" in spoke
            assert "consistency" in spoke
            assert "polarity" in spoke
            assert "contribution" in spoke
            assert "classification" in spoke
            assert spoke["classification"] in (
                "coherent", "dominant", "fragmented", "moderate", "weakly_integrated"
            )

    def test_central_gem_present(self, full_pipeline):
        result = full_pipeline.run("test intent")
        assert "central_gem" in result
        cg = result["central_gem"]
        assert "coherence" in cg
        assert "classification" in cg

    def test_structural_profile(self, full_pipeline):
        result = full_pipeline.run("explore fundamental questions of existence")
        sp = result["structural_profile"]
        assert "edge_count" in sp
        assert "center_count" in sp
        assert "edge_ratio" in sp
        assert "mean_potency" in sp

    def test_tensions_structure(self, full_pipeline):
        result = full_pipeline.run("evaluate competing priorities")
        t = result["tensions"]
        assert "total_magnitude" in t
        assert "direct" in t
        assert "spectrum" in t
        assert "cascading" in t

    def test_gems_present(self, full_pipeline):
        result = full_pipeline.run("synthesize multiple perspectives")
        assert "gems" in result
        assert isinstance(result["gems"], list)
        # With 10 active branches, should have gems
        if result["gems"]:
            gem = result["gems"][0]
            assert "nexus" in gem
            assert "magnitude" in gem
            assert "type" in gem


class TestCoordinateInput:
    def test_preformed_coordinate(self, full_pipeline):
        coord = {b: {"x": 5, "y": 5, "weight": 0.5} for b in ALL_BRANCHES}
        result = full_pipeline.run(coord)
        assert result is not None
        assert "coordinate" in result
        # Coordinate should pass through unchanged
        for branch in ALL_BRANCHES:
            assert result["coordinate"][branch]["x"] == 5
            assert result["coordinate"][branch]["y"] == 5

    def test_corner_coordinate(self, full_pipeline):
        coord = {b: {"x": 0, "y": 0, "weight": 1.0} for b in ALL_BRANCHES}
        result = full_pipeline.run(coord)
        # All constructs should be corner-classified
        for branch in ALL_BRANCHES:
            cq = result["construction_questions"][branch]
            assert cq["classification"] == "corner"
            assert cq["potency"] == 1.0


class TestEmptyInput:
    def test_empty_string(self, full_pipeline):
        """Empty string should still produce a valid result (CSP fills all branches)."""
        result = full_pipeline.run("")
        assert result is not None
        assert len(result["coordinate"]) == 10
        assert len(result["construction_questions"]) == 10
