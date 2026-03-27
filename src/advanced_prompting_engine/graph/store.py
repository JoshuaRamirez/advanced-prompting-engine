"""SQLite persistence layer — canonical/user separation with write protection.

Authoritative source: Spec 04 (sqlite-schema.md), Spec 12 (data-integrity.md).
Triggers are created AFTER initial canonical data insertion.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any


DEFAULT_DB_DIR = os.path.expanduser("~/.advanced-prompting-engine")
DEFAULT_DB_NAME = "graph.db"


class SqliteStore:
    """SQLite persistence for the canonical + user graph data."""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            os.makedirs(DEFAULT_DB_DIR, exist_ok=True)
            db_path = os.path.join(DEFAULT_DB_DIR, DEFAULT_DB_NAME)
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @property
    def conn(self) -> sqlite3.Connection:
        return self.connect()

    # ------------------------------------------------------------------
    # Table creation
    # ------------------------------------------------------------------

    def create_tables(self):
        c = self.conn
        c.executescript("""
            CREATE TABLE IF NOT EXISTS canonical_nodes (
                id          TEXT PRIMARY KEY,
                type        TEXT NOT NULL CHECK(type IN ('branch', 'construct', 'nexus', 'central_gem')),
                tier        INTEGER,
                properties  TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS canonical_edges (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id   TEXT NOT NULL,
                target_id   TEXT NOT NULL,
                relation    TEXT NOT NULL,
                properties  TEXT NOT NULL DEFAULT '{}',
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(source_id, target_id, relation)
            );

            CREATE TABLE IF NOT EXISTS user_nodes (
                id          TEXT PRIMARY KEY,
                type        TEXT NOT NULL CHECK(type IN ('construct')),
                tier        INTEGER NOT NULL DEFAULT 2,
                properties  TEXT NOT NULL,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS user_edges (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id             TEXT NOT NULL,
                target_id             TEXT NOT NULL,
                relation              TEXT NOT NULL CHECK(relation IN (
                    'COMPATIBLE_WITH', 'TENSIONS_WITH', 'REQUIRES',
                    'EXCLUDES', 'GENERATES', 'RESOLVES'
                )),
                properties            TEXT NOT NULL DEFAULT '{}',
                contradicts_canonical INTEGER NOT NULL DEFAULT 0,
                created_at            TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at            TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(source_id, target_id, relation)
            );

            CREATE TABLE IF NOT EXISTS version_manifest (
                version     TEXT PRIMARY KEY,
                node_count  INTEGER NOT NULL,
                edge_count  INTEGER NOT NULL,
                checksum    TEXT NOT NULL,
                applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)

    def create_indexes(self):
        c = self.conn
        c.executescript("""
            CREATE INDEX IF NOT EXISTS idx_canonical_nodes_type ON canonical_nodes(type);
            CREATE INDEX IF NOT EXISTS idx_canonical_edges_source ON canonical_edges(source_id);
            CREATE INDEX IF NOT EXISTS idx_canonical_edges_target ON canonical_edges(target_id);
            CREATE INDEX IF NOT EXISTS idx_canonical_edges_relation ON canonical_edges(relation);

            CREATE INDEX IF NOT EXISTS idx_user_nodes_type ON user_nodes(type);
            CREATE INDEX IF NOT EXISTS idx_user_edges_source ON user_edges(source_id);
            CREATE INDEX IF NOT EXISTS idx_user_edges_target ON user_edges(target_id);
            CREATE INDEX IF NOT EXISTS idx_user_edges_relation ON user_edges(relation);
        """)

    # ------------------------------------------------------------------
    # Write-protection triggers
    # ------------------------------------------------------------------

    def create_write_protection_triggers(self):
        """Create triggers that prevent modification of canonical data.

        MUST be called AFTER all canonical data is inserted.
        """
        c = self.conn
        c.executescript("""
            CREATE TRIGGER IF NOT EXISTS protect_canonical_nodes_update
            BEFORE UPDATE ON canonical_nodes
            BEGIN
                SELECT RAISE(ABORT, 'Canonical nodes are immutable');
            END;

            CREATE TRIGGER IF NOT EXISTS protect_canonical_nodes_delete
            BEFORE DELETE ON canonical_nodes
            BEGIN
                SELECT RAISE(ABORT, 'Canonical nodes cannot be deleted');
            END;

            CREATE TRIGGER IF NOT EXISTS protect_canonical_edges_update
            BEFORE UPDATE ON canonical_edges
            BEGIN
                SELECT RAISE(ABORT, 'Canonical edges are immutable');
            END;

            CREATE TRIGGER IF NOT EXISTS protect_canonical_edges_delete
            BEFORE DELETE ON canonical_edges
            BEGIN
                SELECT RAISE(ABORT, 'Canonical edges cannot be deleted');
            END;
        """)

    def drop_write_protection_triggers(self):
        """Drop canonical protection triggers (used during migration)."""
        c = self.conn
        c.executescript("""
            DROP TRIGGER IF EXISTS protect_canonical_nodes_update;
            DROP TRIGGER IF EXISTS protect_canonical_nodes_delete;
            DROP TRIGGER IF EXISTS protect_canonical_edges_update;
            DROP TRIGGER IF EXISTS protect_canonical_edges_delete;
        """)

    # ------------------------------------------------------------------
    # Canonical data insertion (bulk)
    # ------------------------------------------------------------------

    def insert_canonical_nodes(self, nodes: list[dict]):
        """Bulk insert canonical nodes. Call before creating triggers."""
        c = self.conn
        c.executemany(
            "INSERT INTO canonical_nodes (id, type, tier, properties) VALUES (?, ?, ?, ?)",
            [
                (n["id"], n["type"], n.get("tier"), json.dumps(n))
                for n in nodes
            ],
        )

    def insert_canonical_edges(self, edges: list[dict]):
        """Bulk insert canonical edges. Call before creating triggers."""
        c = self.conn
        c.executemany(
            "INSERT INTO canonical_edges (source_id, target_id, relation, properties) VALUES (?, ?, ?, ?)",
            [
                (e["source_id"], e["target_id"], e["relation"], json.dumps(e))
                for e in edges
            ],
        )

    def initialize_canonical(self, nodes: list[dict], edges: list[dict], version: str):
        """Full initialization: tables → data → version → indexes → triggers.

        Steps 2-4 in a single transaction. Step 5 (triggers) after commit.
        """
        self.create_tables()

        # Transaction: insert all canonical data + version manifest
        c = self.conn
        c.execute("BEGIN")
        try:
            self.insert_canonical_nodes(nodes)
            self.insert_canonical_edges(edges)
            checksum = self.compute_checksum(nodes, edges)
            c.execute(
                "INSERT INTO version_manifest (version, node_count, edge_count, checksum) VALUES (?, ?, ?, ?)",
                (version, len(nodes), len(edges), checksum),
            )
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK")
            raise

        # After commit: indexes + triggers
        self.create_indexes()
        self.create_write_protection_triggers()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_canonical_nodes(self) -> list[dict]:
        rows = self.conn.execute("SELECT properties FROM canonical_nodes").fetchall()
        return [json.loads(row["properties"]) for row in rows]

    def load_canonical_edges(self) -> list[dict]:
        rows = self.conn.execute("SELECT properties FROM canonical_edges").fetchall()
        return [json.loads(row["properties"]) for row in rows]

    def load_user_nodes(self) -> list[dict]:
        rows = self.conn.execute("SELECT properties FROM user_nodes").fetchall()
        return [json.loads(row["properties"]) for row in rows]

    def load_user_edges(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT source_id, target_id, relation, properties, contradicts_canonical FROM user_edges"
        ).fetchall()
        results = []
        for row in rows:
            props = json.loads(row["properties"])
            props["source_id"] = row["source_id"]
            props["target_id"] = row["target_id"]
            props["relation"] = row["relation"]
            props["contradicts_canonical"] = bool(row["contradicts_canonical"])
            props["provenance"] = "user"
            results.append(props)
        return results

    # ------------------------------------------------------------------
    # User data writes
    # ------------------------------------------------------------------

    def insert_user_node(self, node: dict):
        self.conn.execute(
            "INSERT INTO user_nodes (id, type, tier, properties) VALUES (?, ?, ?, ?)",
            (node["id"], node.get("type", "construct"), node.get("tier", 2), json.dumps(node)),
        )
        self.conn.commit()

    def insert_user_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str,
        properties: dict | None = None,
        contradicts_canonical: bool = False,
    ):
        props = properties or {}
        self.conn.execute(
            """INSERT INTO user_edges
               (source_id, target_id, relation, properties, contradicts_canonical)
               VALUES (?, ?, ?, ?, ?)""",
            (source_id, target_id, relation, json.dumps(props), int(contradicts_canonical)),
        )
        self.conn.commit()

    def update_user_node(self, node_id: str, properties: dict):
        self.conn.execute(
            "UPDATE user_nodes SET properties=?, updated_at=datetime('now') WHERE id=?",
            (json.dumps(properties), node_id),
        )
        self.conn.commit()

    def delete_user_edge(self, source_id: str, target_id: str, relation: str):
        self.conn.execute(
            "DELETE FROM user_edges WHERE source_id=? AND target_id=? AND relation=?",
            (source_id, target_id, relation),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Version management
    # ------------------------------------------------------------------

    def get_current_version(self) -> str | None:
        row = self.conn.execute(
            "SELECT version FROM version_manifest ORDER BY applied_at DESC LIMIT 1"
        ).fetchone()
        return row["version"] if row else None

    def needs_initialization(self) -> bool:
        """True if the database has no canonical data."""
        try:
            row = self.conn.execute("SELECT COUNT(*) as cnt FROM canonical_nodes").fetchone()
            return row["cnt"] == 0
        except sqlite3.OperationalError:
            return True

    def check_migration_needed(self, expected_version: str) -> bool:
        current = self.get_current_version()
        return current != expected_version

    def find_orphaned_user_edges(self) -> list[dict]:
        """Find user edges whose source or target no longer exists."""
        orphaned = []
        rows = self.conn.execute(
            "SELECT id, source_id, target_id, relation FROM user_edges"
        ).fetchall()

        for row in rows:
            source_ok = self._node_exists(row["source_id"])
            target_ok = self._node_exists(row["target_id"])
            if not source_ok or not target_ok:
                orphaned.append({
                    "edge_id": row["id"],
                    "source_id": row["source_id"],
                    "source_ok": source_ok,
                    "target_id": row["target_id"],
                    "target_ok": target_ok,
                    "relation": row["relation"],
                })
        return orphaned

    def migrate(self, nodes: list[dict], edges: list[dict], new_version: str) -> list[dict]:
        """Replace canonical data and check for orphaned user edges.

        Returns list of orphaned edges (do NOT auto-delete).
        """
        # Find orphans before replacing canonical data
        orphaned = self.find_orphaned_user_edges()

        # Replace canonical data in a transaction
        self.drop_write_protection_triggers()
        c = self.conn
        c.execute("BEGIN")
        try:
            c.execute("DELETE FROM canonical_edges")
            c.execute("DELETE FROM canonical_nodes")
            self.insert_canonical_nodes(nodes)
            self.insert_canonical_edges(edges)
            checksum = self.compute_checksum(nodes, edges)
            c.execute(
                "INSERT INTO version_manifest (version, node_count, edge_count, checksum) VALUES (?, ?, ?, ?)",
                (new_version, len(nodes), len(edges), checksum),
            )
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK")
            raise

        self.create_write_protection_triggers()

        # Re-check orphans after migration
        orphaned = self.find_orphaned_user_edges()
        return orphaned

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _node_exists(self, node_id: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM canonical_nodes WHERE id=? UNION SELECT 1 FROM user_nodes WHERE id=?",
            (node_id, node_id),
        ).fetchone()
        return row is not None

    @staticmethod
    def compute_checksum(nodes: list[dict], edges: list[dict]) -> str:
        node_ids = sorted(n["id"] for n in nodes)
        edge_tuples = sorted(
            (e["source_id"], e["target_id"], e["relation"]) for e in edges
        )
        combined = f"{len(nodes)}:{len(edges)}:{node_ids}:{edge_tuples}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def canonical_node_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM canonical_nodes").fetchone()
        return row["cnt"]

    def canonical_edge_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM canonical_edges").fetchone()
        return row["cnt"]
