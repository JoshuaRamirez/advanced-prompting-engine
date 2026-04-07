"""Tests for extend_schema tool handler (v2 — face-based, 12x12 grid)."""

import os
import tempfile

import networkx as nx
import pytest

from advanced_prompting_engine.graph.mutation import GraphMutationLayer
from advanced_prompting_engine.graph.schema import GRID_SIZE
from advanced_prompting_engine.graph.store import SqliteStore
from advanced_prompting_engine.tools.extend_schema import handle_extend_schema


@pytest.fixture
def env():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = SqliteStore(db_path=path)
    store.create_tables()

    G = nx.DiGraph()
    G.add_node("ontology", type="face", tier=1)
    G.add_node("ontology.0_0", type="construct", face="ontology", x=0, y=0,
               classification="corner", potency=1.0, provenance="canonical")
    max_coord = GRID_SIZE - 1  # 11
    G.add_node(f"ontology.{max_coord}_{max_coord}", type="construct",
               face="ontology", x=max_coord, y=max_coord,
               classification="corner", potency=1.0, provenance="canonical")
    G.add_edge("ontology.0_0", f"ontology.{max_coord}_{max_coord}",
               relation="TENSIONS_WITH", strength=0.5, provenance="canonical")

    layer = GraphMutationLayer(G, store)
    yield layer
    store.close()
    os.unlink(path)


class TestAddConstruct:
    def test_success(self, env):
        result = handle_extend_schema(env, "add_construct",
                                      face="ontology", x=3, y=3,
                                      question="Test?", tags=["test"],
                                      description="Test construct")
        assert result["status"] == "created"

    def test_success_at_grid_boundary(self, env):
        """Grid positions go up to GRID_SIZE-1 (11 for 12x12)."""
        max_coord = GRID_SIZE - 1
        result = handle_extend_schema(env, "add_construct",
                                      face="ontology", x=max_coord, y=0,
                                      question="Edge?", tags=[],
                                      description="Boundary construct")
        assert result["status"] == "created"

    def test_collision(self, env):
        result = handle_extend_schema(env, "add_construct",
                                      face="ontology", x=0, y=0,
                                      question="Dup?", tags=[], description="Dup")
        assert result["status"] == "error"
        assert "already exists" in result["message"]

    def test_invalid_face(self, env):
        result = handle_extend_schema(env, "add_construct",
                                      face="nonexistent", x=0, y=0,
                                      question="Q?", tags=[], description="D")
        assert result["status"] == "error"

    def test_branch_alias_accepted(self, env):
        """The 'branch' parameter is accepted as alias for 'face'."""
        result = handle_extend_schema(env, "add_construct",
                                      branch="ontology", x=5, y=5,
                                      question="Alias?", tags=[],
                                      description="Branch alias")
        assert result["status"] == "created"


class TestAddRelation:
    def test_success(self, env):
        max_coord = GRID_SIZE - 1
        result = handle_extend_schema(env, "add_relation",
                                      source_id="ontology.0_0",
                                      target_id=f"ontology.{max_coord}_{max_coord}",
                                      relation_type="GENERATES", strength=0.5)
        assert result["status"] == "created"

    def test_contradiction(self, env):
        max_coord = GRID_SIZE - 1
        result = handle_extend_schema(env, "add_relation",
                                      source_id="ontology.0_0",
                                      target_id=f"ontology.{max_coord}_{max_coord}",
                                      relation_type="COMPATIBLE_WITH", strength=0.5)
        assert result["status"] == "contradiction"
        assert "options" in result

    def test_missing_params(self, env):
        result = handle_extend_schema(env, "add_relation")
        assert result["status"] == "error"


class TestUnknownOperation:
    def test_unknown_operation(self, env):
        result = handle_extend_schema(env, "delete_construct")
        assert result["status"] == "error"
        assert "Unknown operation" in result["message"]
