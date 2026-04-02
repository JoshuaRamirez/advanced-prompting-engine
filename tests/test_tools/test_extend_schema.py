"""Tests for extend_schema tool handler."""

import os
import tempfile

import networkx as nx
import pytest

from advanced_prompting_engine.graph.mutation import GraphMutationLayer
from advanced_prompting_engine.graph.store import SqliteStore
from advanced_prompting_engine.tools.extend_schema import handle_extend_schema


@pytest.fixture
def env():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = SqliteStore(db_path=path)
    store.create_tables()

    G = nx.DiGraph()
    G.add_node("ontology", type="branch", tier=1)
    G.add_node("ontology.0_0", type="construct", branch="ontology", x=0, y=0,
               classification="corner", potency=1.0, provenance="canonical")
    G.add_node("ontology.9_9", type="construct", branch="ontology", x=9, y=9,
               classification="corner", potency=1.0, provenance="canonical")
    G.add_edge("ontology.0_0", "ontology.9_9", relation="TENSIONS_WITH",
               strength=0.5, provenance="canonical")

    layer = GraphMutationLayer(G, store)
    yield layer
    store.close()
    os.unlink(path)


class TestAddConstruct:
    def test_success(self, env):
        result = handle_extend_schema(env, "add_construct",
                                      branch="ontology", x=3, y=3,
                                      question="Test?", tags=["test"],
                                      description="Test construct")
        assert result["status"] == "created"

    def test_collision(self, env):
        result = handle_extend_schema(env, "add_construct",
                                      branch="ontology", x=0, y=0,
                                      question="Dup?", tags=[], description="Dup")
        assert result["status"] == "error"
        assert "already exists" in result["message"]

    def test_invalid_branch(self, env):
        result = handle_extend_schema(env, "add_construct",
                                      branch="nonexistent", x=0, y=0,
                                      question="Q?", tags=[], description="D")
        assert result["status"] == "error"


class TestAddRelation:
    def test_success(self, env):
        result = handle_extend_schema(env, "add_relation",
                                      source_id="ontology.0_0",
                                      target_id="ontology.9_9",
                                      relation_type="GENERATES", strength=0.5)
        assert result["status"] == "created"

    def test_contradiction(self, env):
        result = handle_extend_schema(env, "add_relation",
                                      source_id="ontology.0_0",
                                      target_id="ontology.9_9",
                                      relation_type="COMPATIBLE_WITH", strength=0.5)
        assert result["status"] == "contradiction"
        assert "options" in result

    def test_missing_params(self, env):
        result = handle_extend_schema(env, "add_relation")
        assert result["status"] == "error"
