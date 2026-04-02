"""Tests for multi-pass orchestration — stress_test, triangulate, deepen."""

import copy

import networkx as nx
import pytest

from advanced_prompting_engine.cache.embedding import EmbeddingCache
from advanced_prompting_engine.cache.tfidf import TfidfCache
from advanced_prompting_engine.graph.canonical import generate_all_canonical
from advanced_prompting_engine.graph.query import GraphQueryLayer
from advanced_prompting_engine.graph.schema import ALL_BRANCHES, SYMMETRIC_RELATIONS
from advanced_prompting_engine.orchestrator.multi_pass import deepen, stress_test, triangulate
from advanced_prompting_engine.pipeline.runner import PipelineRunner


@pytest.fixture(scope="module")
def engine():
    nodes, edges = generate_all_canonical()
    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["id"], **n)
    for e in edges:
        G.add_edge(e["source_id"], e["target_id"], **e)
        if e.get("relation") in SYMMETRIC_RELATIONS:
            rev = {k: v for k, v in e.items() if k not in ("source_id", "target_id")}
            G.add_edge(e["target_id"], e["source_id"],
                       source_id=e["target_id"], target_id=e["source_id"], **rev)
    query = GraphQueryLayer(G)
    emb = EmbeddingCache(); emb.initialize(G)
    tfidf = TfidfCache(); tfidf.initialize(G)
    pipeline = PipelineRunner(G, query, emb, tfidf)
    return G, pipeline, tfidf


@pytest.fixture
def coord():
    return {b: {"x": 0, "y": 0, "weight": 0.5} for b in ALL_BRANCHES}


class TestStressTest:
    def test_produces_perturbations(self, engine, coord):
        G, pipeline, _ = engine
        result = stress_test(coord, pipeline)
        assert "baseline_tension" in result
        assert "perturbations_tested" in result
        assert result["perturbations_tested"] > 0
        assert "breakpoints" in result
        assert "improvements" in result
        assert "all_results" in result

    def test_perturbations_have_structure(self, engine, coord):
        _, pipeline, _ = engine
        result = stress_test(coord, pipeline)
        for r in result["all_results"][:3]:
            assert "branch" in r
            assert "from" in r
            assert "to" in r
            assert "tension_delta" in r
            assert "coherence_delta" in r


class TestTriangulate:
    def test_produces_intersection(self, engine):
        G, pipeline, _ = engine
        coord_a = {b: {"x": 0, "y": 0, "weight": 1.0} for b in ALL_BRANCHES}
        coord_b = {b: {"x": 9, "y": 9, "weight": 1.0} for b in ALL_BRANCHES}
        result = triangulate(coord_a, coord_b, pipeline, G)
        assert "distance" in result
        assert "intersection" in result
        assert "spoke_comparison" in result
        assert "a_coherence" in result
        assert "b_coherence" in result
        assert len(result["intersection"]) == 10


class TestDeepen:
    def test_does_not_mutate_graph(self, engine, coord):
        G, pipeline, tfidf = engine
        # Snapshot node data before
        node_snapshot = {n: dict(G.nodes[n]) for n in list(G.nodes())[:10]}
        basis = pipeline.run(coord)
        deepen(basis, pipeline, G, tfidf)
        # Verify nodes unchanged
        for n, data in node_snapshot.items():
            for key, val in data.items():
                assert G.nodes[n].get(key) == val, f"Node {n} mutated on key {key}"

    def test_returns_deeper_basis(self, engine, coord):
        G, pipeline, tfidf = engine
        basis = pipeline.run(coord)
        deeper = deepen(basis, pipeline, G, tfidf)
        assert deeper.get("depth", 0) >= 1
        assert "construction_questions" in deeper
        assert len(deeper["construction_questions"]) == 10
