"""Tests for SQLite persistence layer (v2: faces, 12x12 grid)."""

import json
import os
import sqlite3
import tempfile

import pytest

from advanced_prompting_engine.graph.canonical import build_canonical_graph, CANONICAL_VERSION
from advanced_prompting_engine.graph.store import SqliteStore


@pytest.fixture
def tmp_db():
    """Temporary database file cleaned up after test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def initialized_store(tmp_db):
    """Store with canonical data loaded."""
    store = SqliteStore(db_path=tmp_db)
    nodes, edges = build_canonical_graph()
    store.initialize_canonical(nodes, edges, CANONICAL_VERSION)
    return store


class TestInitialization:
    def test_creates_tables(self, tmp_db):
        store = SqliteStore(db_path=tmp_db)
        store.create_tables()
        # Verify tables exist
        rows = store.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {r["name"] for r in rows}
        assert "canonical_nodes" in names
        assert "canonical_edges" in names
        assert "user_nodes" in names
        assert "user_edges" in names
        assert "version_manifest" in names
        store.close()

    def test_canonical_node_count(self, initialized_store):
        assert initialized_store.canonical_node_count() == 1873

    def test_canonical_edge_count(self, initialized_store):
        assert initialized_store.canonical_edge_count() == 2279

    def test_version_manifest(self, initialized_store):
        assert initialized_store.get_current_version() == CANONICAL_VERSION

    def test_needs_initialization_empty(self, tmp_db):
        store = SqliteStore(db_path=tmp_db)
        store.create_tables()
        assert store.needs_initialization() is True
        store.close()

    def test_needs_initialization_after_init(self, initialized_store):
        assert initialized_store.needs_initialization() is False

    def test_type_constraint_uses_face(self, tmp_db):
        """The canonical_nodes type CHECK constraint accepts 'face' (not 'branch')."""
        store = SqliteStore(db_path=tmp_db)
        store.create_tables()
        # 'face' should succeed
        store.conn.execute(
            "INSERT INTO canonical_nodes (id, type, tier, properties) VALUES (?, ?, ?, ?)",
            ("test_face", "face", 1, "{}"),
        )
        store.conn.commit()
        # 'branch' should fail
        with pytest.raises(sqlite3.IntegrityError):
            store.conn.execute(
                "INSERT INTO canonical_nodes (id, type, tier, properties) VALUES (?, ?, ?, ?)",
                ("test_branch", "branch", 1, "{}"),
            )
        store.close()


class TestWriteProtection:
    def test_cannot_update_canonical_node(self, initialized_store):
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            initialized_store.conn.execute(
                "UPDATE canonical_nodes SET type='xxx' WHERE id='ontology'"
            )

    def test_cannot_delete_canonical_node(self, initialized_store):
        with pytest.raises(sqlite3.IntegrityError, match="cannot be deleted"):
            initialized_store.conn.execute(
                "DELETE FROM canonical_nodes WHERE id='ontology'"
            )

    def test_cannot_update_canonical_edge(self, initialized_store):
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            initialized_store.conn.execute(
                "UPDATE canonical_edges SET relation='xxx' WHERE id=1"
            )

    def test_cannot_delete_canonical_edge(self, initialized_store):
        with pytest.raises(sqlite3.IntegrityError, match="cannot be deleted"):
            initialized_store.conn.execute(
                "DELETE FROM canonical_edges WHERE id=1"
            )


class TestRoundTrip:
    def test_load_canonical_nodes(self, initialized_store):
        nodes = initialized_store.load_canonical_nodes()
        assert len(nodes) == 1873

    def test_load_canonical_edges(self, initialized_store):
        edges = initialized_store.load_canonical_edges()
        assert len(edges) == 2279

    def test_user_nodes_empty_initially(self, initialized_store):
        assert len(initialized_store.load_user_nodes()) == 0

    def test_user_edges_empty_initially(self, initialized_store):
        assert len(initialized_store.load_user_edges()) == 0


class TestUserData:
    def test_insert_user_node(self, initialized_store):
        node = {"id": "test.custom_1", "type": "construct", "tier": 2, "face": "ontology"}
        initialized_store.insert_user_node(node)
        loaded = initialized_store.load_user_nodes()
        assert len(loaded) == 1
        assert loaded[0]["id"] == "test.custom_1"

    def test_insert_user_edge(self, initialized_store):
        initialized_store.insert_user_edge(
            "ontology.0_0", "epistemology.0_0", "COMPATIBLE_WITH",
            properties={"strength": 0.7}
        )
        loaded = initialized_store.load_user_edges()
        assert len(loaded) == 1
        assert loaded[0]["relation"] == "COMPATIBLE_WITH"

    def test_delete_user_edge(self, initialized_store):
        initialized_store.insert_user_edge(
            "ontology.0_0", "epistemology.0_0", "COMPATIBLE_WITH"
        )
        initialized_store.delete_user_edge("ontology.0_0", "epistemology.0_0", "COMPATIBLE_WITH")
        assert len(initialized_store.load_user_edges()) == 0
