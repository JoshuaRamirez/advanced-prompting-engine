"""Tests for the create_prompt_basis MCP tool handler.

Validates intent-to-basis pipeline invocation, error handling for
mutually exclusive parameters, and compact output structure.
"""

import networkx as nx
import pytest

from advanced_prompting_engine.graph.canonical import build_canonical_graph
from advanced_prompting_engine.graph.schema import ALL_FACES, SYMMETRIC_RELATIONS
from advanced_prompting_engine.graph.query import GraphQueryLayer
from advanced_prompting_engine.cache.embedding import EmbeddingCache
from advanced_prompting_engine.cache.tfidf import TfidfCache
from advanced_prompting_engine.pipeline.runner import PipelineRunner
from advanced_prompting_engine.tools.create_prompt_basis import (
    handle_create_prompt_basis,
    _compact,
)


@pytest.fixture(scope="module")
def pipeline():
    """Build the full graph + pipeline once for the module."""
    nodes, edges = build_canonical_graph()
    G = nx.DiGraph()
    for n in nodes:
        G.add_node(n["id"], **n)
    for e in edges:
        G.add_edge(e["source_id"], e["target_id"], **e)
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
    return PipelineRunner(G, ql, ec, tc)


class TestCreatePromptBasis:
    def test_intent_produces_success(self, pipeline):
        result = handle_create_prompt_basis(pipeline, intent="What is truth?")
        assert result["status"] == "success"
        assert "construction_basis" in result

    def test_both_intent_and_coordinate_is_error(self, pipeline):
        coord = {f: {"x": 5, "y": 5, "weight": 0.5} for f in ALL_FACES}
        result = handle_create_prompt_basis(
            pipeline, intent="What is truth?", coordinate=coord
        )
        assert result["status"] == "error"
        assert "not both" in result["message"]

    def test_neither_is_error(self, pipeline):
        result = handle_create_prompt_basis(pipeline)
        assert result["status"] == "error"
        assert "either" in result["message"].lower() or "Provide" in result["message"]

    def test_compact_includes_harmonization(self, pipeline):
        result = handle_create_prompt_basis(
            pipeline, intent="Build something meaningful", compact=True
        )
        assert result["status"] == "success"
        basis = result["construction_basis"]
        assert "harmonization" in basis
        assert len(basis["harmonization"]) == 6

    def test_compact_includes_all_keys(self, pipeline):
        result = handle_create_prompt_basis(
            pipeline, intent="Explore ethics and morality", compact=True
        )
        assert result["status"] == "success"
        basis = result["construction_basis"]
        expected_keys = {
            "coordinate", "tensions_summary", "harmonization",
            "spokes", "central_gem", "construction_questions",
        }
        for key in expected_keys:
            assert key in basis, f"Missing key '{key}' in compact output"

    def test_coordinate_input_produces_success(self, pipeline):
        coord = {f: {"x": 5, "y": 5, "weight": 0.5} for f in ALL_FACES}
        result = handle_create_prompt_basis(pipeline, coordinate=coord)
        assert result["status"] == "success"
