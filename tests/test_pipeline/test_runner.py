"""End-to-end pipeline runner tests — v2 (12 faces, 12x12 grids).

Tests the full 8-stage pipeline with the real canonical graph.
"""

from __future__ import annotations

import networkx as nx
import pytest

from advanced_prompting_engine.cache.tfidf import TfidfCache
from advanced_prompting_engine.graph.canonical import build_canonical_graph
from advanced_prompting_engine.graph.query import GraphQueryLayer
from advanced_prompting_engine.graph.schema import ALL_FACES, SYMMETRIC_RELATIONS
from advanced_prompting_engine.pipeline.runner import PipelineRunner


@pytest.fixture(scope="module")
def full_pipeline():
    """Build the full canonical graph + caches + pipeline. Module-scoped for speed."""
    nodes, edges = build_canonical_graph()

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
    tfidf_cache = TfidfCache()
    tfidf_cache.initialize(G)

    # v2: embedding_cache is optional (pass None)
    runner = PipelineRunner(G, query, None, tfidf_cache)
    return runner


class TestIntentInput:
    def test_basic_intent(self, full_pipeline):
        result = full_pipeline.run("thorough code review with security focus")
        assert result is not None
        assert "coordinate" in result
        assert "active_constructs" in result
        assert "construction_questions" in result

    def test_all_12_faces_in_coordinate(self, full_pipeline):
        result = full_pipeline.run("analyze the ethical implications of this decision")
        for face in ALL_FACES:
            assert face in result["coordinate"]
            entry = result["coordinate"][face]
            assert 0 <= entry["x"] <= 11
            assert 0 <= entry["y"] <= 11
            assert entry["weight"] > 0

    def test_construction_questions_all_faces(self, full_pipeline):
        result = full_pipeline.run("design a learning system")
        assert len(result["construction_questions"]) == 12
        for face in ALL_FACES:
            cq = result["construction_questions"][face]
            assert "template" in cq
            assert "active_question" in cq
            assert "classification" in cq
            assert "potency" in cq
            assert "spoke_profile" in cq

    def test_spokes_all_present(self, full_pipeline):
        result = full_pipeline.run("build a bridge between theory and practice")
        assert len(result["spokes"]) == 12
        for face in ALL_FACES:
            spoke = result["spokes"][face]
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
        assert "positional" in t
        assert "spectrum" in t

    def test_gems_present(self, full_pipeline):
        result = full_pipeline.run("synthesize multiple perspectives")
        assert "gems" in result
        assert isinstance(result["gems"], list)
        # With 12 active faces, should have gems
        if result["gems"]:
            gem = result["gems"][0]
            assert "nexus" in gem
            assert "magnitude" in gem
            assert "type" in gem


class TestCoordinateInput:
    def test_preformed_coordinate(self, full_pipeline):
        coord = {f: {"x": 5, "y": 5, "weight": 0.5} for f in ALL_FACES}
        result = full_pipeline.run(coord)
        assert result is not None
        assert "coordinate" in result
        # Coordinate should pass through unchanged
        for face in ALL_FACES:
            assert result["coordinate"][face]["x"] == 5
            assert result["coordinate"][face]["y"] == 5

    def test_corner_coordinate(self, full_pipeline):
        coord = {f: {"x": 0, "y": 0, "weight": 1.0} for f in ALL_FACES}
        result = full_pipeline.run(coord)
        # All constructs should be corner-classified
        for face in ALL_FACES:
            cq = result["construction_questions"][face]
            assert cq["classification"] == "corner"
            assert cq["potency"] == 1.0


class TestEmptyInput:
    def test_empty_string(self, full_pipeline):
        """Empty string should still produce a valid result (CSP fills all faces)."""
        result = full_pipeline.run("")
        assert result is not None
        assert len(result["coordinate"]) == 12
        assert len(result["construction_questions"]) == 12


class TestCompactOutput:
    def test_compact_has_expected_keys(self, full_pipeline):
        from advanced_prompting_engine.tools.create_prompt_basis import _compact
        coord = {f: {"x": 0, "y": 0, "weight": 1.0} for f in ALL_FACES}
        full = full_pipeline.run(coord)
        compact = _compact(full)
        expected = {"coordinate", "structural_profile", "tensions_summary",
                    "harmonization", "spokes", "central_gem", "construction_questions"}
        assert set(compact.keys()) == expected

    def test_compact_is_small(self, full_pipeline):
        import json
        from advanced_prompting_engine.tools.create_prompt_basis import _compact
        coord = {f: {"x": 5, "y": 5, "weight": 0.5} for f in ALL_FACES}
        full = full_pipeline.run(coord)
        compact = _compact(full)
        compact_size = len(json.dumps(compact))
        full_size = len(json.dumps(full, default=str))
        assert compact_size < 8000, f"Compact output too large: {compact_size} bytes"
        assert compact_size < full_size / 5, "Compact should be >5x smaller than full"

    def test_compact_has_position_summary(self, full_pipeline):
        from advanced_prompting_engine.tools.create_prompt_basis import _compact
        coord = {f: {"x": 0, "y": 0, "weight": 1.0} for f in ALL_FACES}
        full = full_pipeline.run(coord)
        compact = _compact(full)
        for face in ALL_FACES:
            cq = compact["construction_questions"][face]
            assert "position_summary" in cq
            assert cq["position_summary"] is not None
