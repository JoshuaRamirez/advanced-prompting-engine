# Spec 12 — Data Integrity

## Purpose

Defines the contradiction detection algorithm, override flow, resolution path creation, provenance scoping implementation, version migration procedure, and graph validation rules.

---

## Contradiction Detection

### When It Fires

Contradiction detection runs inside `GraphMutationLayer.add_relation()` — before any write occurs.

### Algorithm

```python
CONTRADICTION_MAP = {
    "COMPATIBLE_WITH": ["TENSIONS_WITH", "EXCLUDES"],
    "TENSIONS_WITH": ["COMPATIBLE_WITH"],
    "REQUIRES": ["EXCLUDES"],
    "EXCLUDES": ["COMPATIBLE_WITH", "REQUIRES"],
    "GENERATES": [],   # no contradictions — anything can be generative
    "RESOLVES": [],    # no contradictions — resolutions are additive
}

def check_contradiction(
    source_id: str, target_id: str, proposed_relation: str, G: nx.Graph
) -> dict | None:
    """Check if proposed edge contradicts an existing edge.

    Returns ContradictionWarning dict or None.
    """
    contradicts = CONTRADICTION_MAP.get(proposed_relation, [])
    if not contradicts:
        return None

    # Check both directions (symmetric relations)
    for existing_relation in contradicts:
        if G.has_edge(source_id, target_id):
            edge = G.edges[source_id, target_id]
            if edge.get("relation") == existing_relation:
                return {
                    "status": "contradiction",
                    "existing": {
                        "source": source_id,
                        "target": target_id,
                        "relation": existing_relation,
                        "strength": edge.get("strength"),
                        "provenance": edge.get("provenance"),
                    },
                    "proposed": {
                        "source": source_id,
                        "target": target_id,
                        "relation": proposed_relation,
                    },
                    "options": ["cancel", "override", "add_resolution_path"],
                }

        # Check reverse direction for symmetric relations
        if G.has_edge(target_id, source_id):
            edge = G.edges[target_id, source_id]
            if edge.get("relation") == existing_relation:
                return {
                    "status": "contradiction",
                    "existing": {
                        "source": target_id,
                        "target": source_id,
                        "relation": existing_relation,
                        "strength": edge.get("strength"),
                        "provenance": edge.get("provenance"),
                    },
                    "proposed": {
                        "source": source_id,
                        "target": target_id,
                        "relation": proposed_relation,
                    },
                    "options": ["cancel", "override", "add_resolution_path"],
                }

    return None
```

---

## Override Flow

When a user chooses "override":

```python
def override_contradiction(
    source_id: str, target_id: str, relation: str, strength: float,
    reason: str, G: nx.Graph, store: SqliteStore
):
    """Write the contradicting edge with a flag."""
    G.add_edge(source_id, target_id,
               relation=relation,
               strength=strength,
               provenance="user",
               contradicts_canonical=True,
               override_reason=reason)

    store.insert_user_edge(
        source_id, target_id, relation, strength,
        contradicts_canonical=True,
        override_reason=reason
    )
```

Overridden contradictions:
- Are written with `contradicts_canonical=True`
- Carry the user's reason
- Are visible in `validate_graph` output
- Both the canonical edge and the user edge coexist in the graph

---

## Resolution Path Flow

When a user chooses "add_resolution_path":

```python
def add_resolution_path(
    tension_source: str, tension_target: str,
    resolver_branch: str, resolver_x: int, resolver_y: int,
    resolver_question: str, resolver_tags: list[str],
    G: nx.Graph, mutation_layer: GraphMutationLayer
):
    """Create a new construct that RESOLVES the tension."""
    # 1. Create the resolver construct
    resolver_id = mutation_layer.add_construct(
        branch=resolver_branch,
        x=resolver_x,
        y=resolver_y,
        question=resolver_question,
        tags=resolver_tags,
        description=f"Resolves tension between {tension_source} and {tension_target}",
        provenance="user",
    )

    # 2. Add RESOLVES edges
    mutation_layer.add_relation(
        source_id=resolver_id,
        target_id=tension_source,
        relation_type="RESOLVES",
        strength=0.5,
    )
    mutation_layer.add_relation(
        source_id=resolver_id,
        target_id=tension_target,
        relation_type="RESOLVES",
        strength=0.5,
    )
```

The resolver construct:
- Is a user-created center-class construct (center positions are resolution nodes)
- Has two RESOLVES edges connecting it to the two tension endpoints
- Is discoverable by the pipeline's resolution path scan in Stage 5

---

## Provenance Scoping

### Implementation in Graph Query Layer

```python
class GraphQueryLayer:
    def list_constructs(self, branch: str, provenance: str = "merged",
                        classification: str = None) -> list:
        if provenance == "canonical":
            nodes = [n for n in self._g.nodes()
                     if self._g.nodes[n].get("branch") == branch
                     and self._g.nodes[n].get("provenance") == "canonical"
                     and self._g.nodes[n].get("type") == "construct"]
        elif provenance == "user":
            nodes = [n for n in self._g.nodes()
                     if self._g.nodes[n].get("branch") == branch
                     and self._g.nodes[n].get("provenance") == "user"
                     and self._g.nodes[n].get("type") == "construct"]
        else:  # merged
            nodes = [n for n in self._g.nodes()
                     if self._g.nodes[n].get("branch") == branch
                     and self._g.nodes[n].get("type") == "construct"]

        if classification:
            nodes = [n for n in nodes
                     if self._g.nodes[n].get("classification") == classification]

        return [self._g.nodes[n] for n in nodes]
```

All query methods follow this pattern. The pipeline defaults to `provenance="merged"`.

---

## Version Migration

### Detection

On startup, compare the stored version manifest with the engine's built-in version:

```python
def check_migration_needed(store: SqliteStore, expected_version: str) -> bool:
    current = store.get_current_version()
    return current != expected_version
```

### Migration Procedure

```python
def migrate(store: SqliteStore, G: nx.Graph, expected_version: str):
    """Migrate canonical data and check user edge integrity."""

    # 1. Identify user edges that reference canonical nodes
    user_edges = store.get_all_user_edges()

    # 2. Get expected canonical node IDs for the new version
    expected_ids = get_expected_canonical_ids(expected_version)

    # 3. Check each user edge
    orphaned = []
    for edge in user_edges:
        source_ok = edge.source_id in expected_ids or store.user_node_exists(edge.source_id)
        target_ok = edge.target_id in expected_ids or store.user_node_exists(edge.target_id)
        if not source_ok or not target_ok:
            orphaned.append({
                "edge_id": edge.id,
                "source_id": edge.source_id,
                "source_ok": source_ok,
                "target_id": edge.target_id,
                "target_ok": target_ok,
            })

    # 4. Replace canonical data
    store.drop_canonical_triggers()
    store.truncate_canonical_tables()
    store.insert_canonical_data(expected_version)
    store.create_canonical_triggers()
    store.insert_version_manifest(expected_version)

    # 5. Report orphaned edges (do NOT auto-delete)
    if orphaned:
        store.flag_orphaned_edges(orphaned)

    return orphaned
```

### Orphan Reporting

Orphaned edges are reported to the client on the first tool call after migration:

```json
{
  "migration_notice": {
    "from_version": "1.0",
    "to_version": "2.0",
    "orphaned_edges": [
      {
        "edge_id": 42,
        "source_id": "epistemology.3_0",
        "target_id": "custom_construct_1",
        "reason": "target_id not found in new canonical or user nodes"
      }
    ],
    "action_required": "Review orphaned edges via explore_space or extend_schema"
  }
}
```

---

## Graph Validation

A `validate_graph` operation (accessible via `explore_space`) checks graph integrity:

```python
def validate_graph(G: nx.Graph) -> dict:
    """Check graph integrity and return a report."""
    issues = []

    # 1. Orphaned constructs (no HAS_CONSTRUCT edge to a branch)
    for n, data in G.nodes(data=True):
        if data.get("type") == "construct":
            has_branch = any(
                G.edges[e].get("relation") == "HAS_CONSTRUCT"
                for e in G.in_edges(n)
            )
            if not has_branch:
                issues.append({"type": "orphaned_construct", "node": n})

    # 2. Contradictions (coexisting contradictory edges)
    for u, v, data in G.edges(data=True):
        rel = data.get("relation")
        if rel in CONTRADICTION_MAP:
            for contra_rel in CONTRADICTION_MAP[rel]:
                if G.has_edge(u, v) or G.has_edge(v, u):
                    other = G.edges.get((u, v), {}) or G.edges.get((v, u), {})
                    if other.get("relation") == contra_rel:
                        issues.append({
                            "type": "active_contradiction",
                            "edge_a": {"source": u, "target": v, "relation": rel},
                            "edge_b": {"source": u, "target": v, "relation": contra_rel},
                        })

    # 3. Spectrum integrity (both endpoints must be edge-classified)
    for u, v, data in G.edges(data=True):
        if data.get("relation") == "SPECTRUM_OPPOSITION":
            u_class = G.nodes[u].get("classification")
            v_class = G.nodes[v].get("classification")
            if u_class == "center" or v_class == "center":
                issues.append({
                    "type": "invalid_spectrum",
                    "edge": {"source": u, "target": v},
                    "reason": "Spectrum endpoint is center-classified",
                })

    # 4. Nexus integrity (source and target must be valid branches)
    for n, data in G.nodes(data=True):
        if data.get("type") == "nexus":
            sb = data.get("source_branch")
            tb = data.get("target_branch")
            if sb not in G.nodes or tb not in G.nodes:
                issues.append({"type": "invalid_nexus", "node": n})

    return {
        "valid": len(issues) == 0,
        "issue_count": len(issues),
        "issues": issues,
    }
```
