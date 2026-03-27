# Spec 04 — SQLite Schema

## Purpose

Defines the SQLite table structures, write-protection triggers, indexes, and load/save procedures for persisting the graph across sessions.

---

## Database File

Location: `~/.advanced-prompting-engine/graph.db`

Created automatically on first startup if it does not exist. Canonical data is inserted during first initialization.

---

## Tables

### canonical_nodes

Stores all canonical (shipped) nodes: branches, constructs, nexi, central gem.

```sql
CREATE TABLE canonical_nodes (
    id          TEXT PRIMARY KEY,
    type        TEXT NOT NULL CHECK(type IN ('branch', 'construct', 'nexus', 'central_gem')),
    tier        INTEGER,
    properties  TEXT NOT NULL,  -- JSON blob of all node properties
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

The `properties` column stores a JSON object containing all type-specific properties defined in Spec 01 (e.g., `branch`, `x`, `y`, `classification`, `potency`, `question`, `tags`, etc.).

### canonical_edges

Stores all canonical edges: HAS_CONSTRUCT, PRECEDES, SPECTRUM_OPPOSITION, NEXUS_SOURCE, NEXUS_TARGET, CENTRAL_GEM_LINK.

```sql
CREATE TABLE canonical_edges (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id   TEXT NOT NULL REFERENCES canonical_nodes(id),
    target_id   TEXT NOT NULL REFERENCES canonical_nodes(id),
    relation    TEXT NOT NULL,
    properties  TEXT NOT NULL DEFAULT '{}',  -- JSON blob (strength, spectrum_id, etc.)
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(source_id, target_id, relation)
);
```

### user_nodes

Stores user-created nodes (additional constructs).

```sql
CREATE TABLE user_nodes (
    id          TEXT PRIMARY KEY,
    type        TEXT NOT NULL CHECK(type IN ('construct')),
    tier        INTEGER NOT NULL DEFAULT 2,
    properties  TEXT NOT NULL,  -- JSON blob
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

User nodes are always constructs (type = 'construct', tier = 2). Users cannot create branches, nexi, or central gem nodes.

### user_edges

Stores user-created edges between any combination of canonical and user nodes.

```sql
CREATE TABLE user_edges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id       TEXT NOT NULL,
    target_id       TEXT NOT NULL,
    relation        TEXT NOT NULL CHECK(relation IN (
        'COMPATIBLE_WITH', 'TENSIONS_WITH', 'REQUIRES',
        'EXCLUDES', 'GENERATES', 'RESOLVES'
    )),
    properties      TEXT NOT NULL DEFAULT '{}',  -- JSON blob (strength, quality, etc.)
    contradicts_canonical  INTEGER NOT NULL DEFAULT 0,  -- 1 if user overrode a contradiction
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(source_id, target_id, relation)
);
```

Source and target can reference either canonical_nodes or user_nodes. Foreign key enforcement is handled at application level since cross-table FKs are complex in SQLite.

### version_manifest

Tracks canonical graph versions for migration detection.

```sql
CREATE TABLE version_manifest (
    version     TEXT PRIMARY KEY,
    node_count  INTEGER NOT NULL,
    edge_count  INTEGER NOT NULL,
    checksum    TEXT NOT NULL,  -- SHA256 of sorted canonical node IDs + edge tuples
    applied_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## Write-Protection Triggers

Canonical tables are immutable after initial population.

```sql
-- Prevent updates to canonical nodes
CREATE TRIGGER protect_canonical_nodes_update
BEFORE UPDATE ON canonical_nodes
BEGIN
    SELECT RAISE(ABORT, 'Canonical nodes are immutable');
END;

-- Prevent deletes from canonical nodes
CREATE TRIGGER protect_canonical_nodes_delete
BEFORE DELETE ON canonical_nodes
BEGIN
    SELECT RAISE(ABORT, 'Canonical nodes cannot be deleted');
END;

-- Prevent updates to canonical edges
CREATE TRIGGER protect_canonical_edges_update
BEFORE UPDATE ON canonical_edges
BEGIN
    SELECT RAISE(ABORT, 'Canonical edges are immutable');
END;

-- Prevent deletes from canonical edges
CREATE TRIGGER protect_canonical_edges_delete
BEFORE DELETE ON canonical_edges
BEGIN
    SELECT RAISE(ABORT, 'Canonical edges cannot be deleted');
END;
```

**Note:** These triggers are created AFTER initial canonical data insertion. The initialization procedure inserts all canonical data, then creates the triggers.

---

## Indexes

```sql
-- Fast lookup by branch for constructs
CREATE INDEX idx_canonical_nodes_type ON canonical_nodes(type);
CREATE INDEX idx_canonical_edges_source ON canonical_edges(source_id);
CREATE INDEX idx_canonical_edges_target ON canonical_edges(target_id);
CREATE INDEX idx_canonical_edges_relation ON canonical_edges(relation);

CREATE INDEX idx_user_nodes_type ON user_nodes(type);
CREATE INDEX idx_user_edges_source ON user_edges(source_id);
CREATE INDEX idx_user_edges_target ON user_edges(target_id);
CREATE INDEX idx_user_edges_relation ON user_edges(relation);
```

---

## Initialization Procedure

On first startup (database file does not exist or version_manifest is empty):

```
1. Create all tables
2. Insert all canonical nodes:
   a. 10 branch nodes
   b. 1000 construct nodes (100 per branch)
   c. 90 nexus nodes
   d. 1 central gem node
3. Insert all canonical edges:
   a. 1000 HAS_CONSTRUCT edges
   b. 9 PRECEDES edges
   c. 200 SPECTRUM_OPPOSITION edges (from grid mechanics algorithm)
   d. 90 NEXUS_SOURCE edges
   e. 90 NEXUS_TARGET edges
   f. 90 CENTRAL_GEM_LINK edges
4. Insert version manifest entry
5. Create write-protection triggers
```

Steps 2-4 are wrapped in a single transaction. Step 5 occurs after commit, making canonical data immutable from that point.

---

## Graph Load Procedure

On every startup:

```
1. Open database file
2. Verify version_manifest exists and matches expected version
3. Load all canonical_nodes → NetworkX graph nodes
4. Load all canonical_edges → NetworkX graph edges
5. Load all user_nodes → NetworkX graph nodes (with provenance='user')
6. Load all user_edges → NetworkX graph edges (with provenance='user')
7. Return populated NetworkX graph
```

Node properties are deserialized from JSON. All properties stored in the JSON blob become node attributes in NetworkX.

---

## Graph Save Procedure

After user mutations (via Graph Mutation Layer):

```
1. For each new user node: INSERT INTO user_nodes
2. For each new user edge: INSERT INTO user_edges
3. For updated user nodes: UPDATE user_nodes SET properties=?, updated_at=?
4. For deleted user edges: DELETE FROM user_edges WHERE id=?
```

Canonical tables are never written to after initialization (triggers enforce this).

---

## Version Migration Procedure

On startup, if version_manifest version does not match the engine's built-in version:

```
1. Compare current canonical IDs with expected canonical IDs
2. For each user_edge:
   a. Verify source_id exists in canonical_nodes OR user_nodes
   b. Verify target_id exists in canonical_nodes OR user_nodes
   c. If either is missing: flag as orphaned
3. Report orphaned edges to the client on first tool call
4. Do NOT auto-delete orphaned edges — user decides
5. Insert new version_manifest entry
6. Replace canonical data (drop triggers, truncate canonical tables, re-insert, re-create triggers)
```

Step 6 is wrapped in a transaction. User tables are never touched during migration.

---

## Provenance Queries

The Graph Query Layer translates provenance filters into SQL:

```sql
-- provenance='canonical'
SELECT * FROM canonical_nodes WHERE ...

-- provenance='user'
SELECT * FROM user_nodes WHERE ...

-- provenance='merged' (default)
SELECT * FROM canonical_nodes WHERE ...
UNION ALL
SELECT * FROM user_nodes WHERE ...
```

Same pattern for edges. The merged view is the default for all pipeline operations.
