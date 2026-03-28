"""Tests for Graph Mutation Layer — contradiction detection."""

import os
import tempfile

import networkx as nx
import pytest

from advanced_prompting_engine.graph.mutation import ContradictionWarning, GraphMutationLayer
from advanced_prompting_engine.graph.store import SqliteStore


@pytest.fixture
def mutation_env():
    """Graph + store for mutation testing."""
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
    yield layer, G, store, path
    store.close()
    os.unlink(path)


class TestContradictionDetection:
    def test_compatible_contradicts_tensions(self, mutation_env):
        layer, G, _, _ = mutation_env
        result = layer.check_contradiction("ontology.0_0", "ontology.9_9", "COMPATIBLE_WITH")
        assert isinstance(result, ContradictionWarning)
        assert result.existing["relation"] == "TENSIONS_WITH"

    def test_no_contradiction_for_generates(self, mutation_env):
        layer, G, _, _ = mutation_env
        result = layer.check_contradiction("ontology.0_0", "ontology.9_9", "GENERATES")
        assert result is None

    def test_no_contradiction_for_resolves(self, mutation_env):
        layer, G, _, _ = mutation_env
        result = layer.check_contradiction("ontology.0_0", "ontology.9_9", "RESOLVES")
        assert result is None


class TestAddRelation:
    def test_returns_contradiction_without_override(self, mutation_env):
        layer, _, _, _ = mutation_env
        result = layer.add_relation("ontology.0_0", "ontology.9_9", "COMPATIBLE_WITH")
        assert isinstance(result, ContradictionWarning)

    def test_override_writes_with_flag(self, mutation_env):
        layer, G, _, _ = mutation_env
        result = layer.add_relation(
            "ontology.0_0", "ontology.9_9", "COMPATIBLE_WITH",
            override_reason="Testing override"
        )
        assert result["status"] == "created"
        # Edge should exist with contradicts_canonical flag
        assert G.has_edge("ontology.0_0", "ontology.9_9")

    def test_add_generates_no_contradiction(self, mutation_env):
        layer, G, _, _ = mutation_env
        result = layer.add_relation("ontology.0_0", "ontology.9_9", "GENERATES")
        assert result["status"] == "created"


class TestAddConstruct:
    def test_add_user_construct(self, mutation_env):
        layer, G, _, _ = mutation_env
        result = layer.add_construct(
            branch="ontology", x=3, y=3,
            question="Test question?",
            tags=["test"],
            description="Test construct",
        )
        assert result["status"] == "created"
        assert "ontology.3_3" in G.nodes

    def test_collision_raises(self, mutation_env):
        layer, _, _, _ = mutation_env
        with pytest.raises(ValueError, match="already exists"):
            layer.add_construct(
                branch="ontology", x=0, y=0,
                question="Duplicate", tags=[], description="Dup",
            )

    def test_invalid_branch_raises(self, mutation_env):
        layer, _, _, _ = mutation_env
        with pytest.raises(ValueError, match="does not exist"):
            layer.add_construct(
                branch="nonexistent", x=0, y=0,
                question="Q", tags=[], description="D",
            )
