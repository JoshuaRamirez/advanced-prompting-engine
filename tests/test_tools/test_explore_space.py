"""Tests for the explore_space MCP tool handler.

Validates list_faces, list_branches alias, unknown operation handling,
and parameter validation for get_construct.
"""

import networkx as nx
import pytest

from advanced_prompting_engine.graph.canonical import build_canonical_graph
from advanced_prompting_engine.graph.schema import ALL_FACES, SYMMETRIC_RELATIONS
from advanced_prompting_engine.graph.query import GraphQueryLayer
from advanced_prompting_engine.cache.embedding import EmbeddingCache
from advanced_prompting_engine.cache.tfidf import TfidfCache
from advanced_prompting_engine.pipeline.runner import PipelineRunner
from advanced_prompting_engine.tools.explore_space import handle_explore_space


@pytest.fixture(scope="module")
def env():
    """Build the full graph + pipeline + query layer once for the module."""
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
    pipeline = PipelineRunner(G, ql, ec, tc)
    return {"query": ql, "pipeline": pipeline}


class TestListFaces:
    def test_list_faces_returns_12(self, env):
        result = handle_explore_space(env["query"], env["pipeline"], "list_faces")
        assert result["status"] == "success"
        assert len(result["faces"]) == 12

    def test_list_branches_alias_works(self, env):
        """The deprecated 'list_branches' alias should produce the same result."""
        result_faces = handle_explore_space(env["query"], env["pipeline"], "list_faces")
        result_branches = handle_explore_space(env["query"], env["pipeline"], "list_branches")
        assert result_faces["status"] == "success"
        assert result_branches["status"] == "success"
        assert len(result_faces["faces"]) == len(result_branches["faces"])


class TestUnknownOperation:
    def test_unknown_operation_error(self, env):
        result = handle_explore_space(
            env["query"], env["pipeline"], "nonexistent_op"
        )
        assert result["status"] == "error"
        assert "Unknown operation" in result["message"]


class TestGetConstruct:
    def test_get_construct_requires_face(self, env):
        result = handle_explore_space(
            env["query"], env["pipeline"], "get_construct", x=0, y=0
        )
        assert result["status"] == "error"
        assert "required" in result["message"].lower()

    def test_get_construct_requires_x_and_y(self, env):
        result = handle_explore_space(
            env["query"], env["pipeline"], "get_construct", face="ontology"
        )
        assert result["status"] == "error"

    def test_get_construct_success(self, env):
        result = handle_explore_space(
            env["query"], env["pipeline"], "get_construct",
            face="ontology", x=0, y=0
        )
        assert result["status"] == "success"
        assert "construct" in result
        assert result["construct"]["classification"] == "corner"

    def test_get_construct_not_found(self, env):
        """Request a construct on a face that doesn't exist as a node."""
        result = handle_explore_space(
            env["query"], env["pipeline"], "get_construct",
            face="nonexistent_face", x=0, y=0
        )
        assert result["status"] == "error"
