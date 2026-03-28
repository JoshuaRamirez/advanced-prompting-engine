"""Graph Mutation Layer — writes with contradiction detection.

Authoritative source: Spec 12.
Invalidates all 3 caches on any write.
"""

from __future__ import annotations

import networkx as nx

from advanced_prompting_engine.graph.grid import classify, potency
from advanced_prompting_engine.graph.schema import CONTRADICTION_MAP, SYMMETRIC_RELATIONS
from advanced_prompting_engine.graph.store import SqliteStore


class ContradictionWarning:
    """Returned when a proposed edge contradicts an existing edge."""

    def __init__(self, existing: dict, proposed: dict):
        self.existing = existing
        self.proposed = proposed
        self.options = ["cancel", "override", "add_resolution_path"]

    def to_dict(self) -> dict:
        return {
            "status": "contradiction",
            "existing": self.existing,
            "proposed": self.proposed,
            "options": self.options,
        }


class GraphMutationLayer:
    """Mutation operations with integrity enforcement."""

    def __init__(
        self,
        G: nx.DiGraph,
        store: SqliteStore,
        embedding_cache=None,
        tfidf_cache=None,
        centrality_cache=None,
    ):
        self._g = G
        self._store = store
        self._caches = [c for c in [embedding_cache, tfidf_cache, centrality_cache] if c is not None]

    def _invalidate_caches(self):
        for cache in self._caches:
            cache.invalidate()

    # ------------------------------------------------------------------
    # Add construct
    # ------------------------------------------------------------------

    def add_construct(
        self,
        branch: str,
        x: int,
        y: int,
        question: str,
        tags: list[str],
        description: str,
        provenance: str = "user",
    ) -> dict:
        """Add a user construct at a grid position."""
        # Validate branch
        if branch not in self._g.nodes or self._g.nodes[branch].get("type") != "branch":
            raise ValueError(f"Branch {branch!r} does not exist")

        # Validate grid position
        if not (0 <= x <= 9 and 0 <= y <= 9):
            raise ValueError(f"Grid position ({x}, {y}) out of range")

        # Check ID collision
        node_id = f"{branch}.{x}_{y}"
        if node_id in self._g.nodes:
            raise ValueError(f"Construct {node_id!r} already exists")

        cls = classify(x, y)
        pot = potency(x, y)

        node = {
            "id": node_id,
            "type": "construct",
            "tier": 2,
            "branch": branch,
            "x": x,
            "y": y,
            "classification": cls,
            "potency": pot,
            "question": question,
            "question_revisited": None,
            "description": description,
            "tags": tags,
            "spectrum_ids": [],
            "condensed_gems": [],
            "provenance": provenance,
            "mutable": True,
        }

        # Write to graph
        self._g.add_node(node_id, **node)

        # Write to SQLite
        self._store.insert_user_node(node)

        self._invalidate_caches()

        return {"status": "created", "id": node_id}

    # ------------------------------------------------------------------
    # Add relation
    # ------------------------------------------------------------------

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        strength: float = 0.5,
        override_reason: str | None = None,
    ) -> dict | ContradictionWarning:
        """Add a user relation between two constructs.

        Returns success dict or ContradictionWarning.
        """
        # Validate nodes exist
        if source_id not in self._g.nodes:
            raise ValueError(f"Source node {source_id!r} does not exist")
        if target_id not in self._g.nodes:
            raise ValueError(f"Target node {target_id!r} does not exist")

        # Contradiction check
        contradiction = self.check_contradiction(source_id, target_id, relation_type)
        if contradiction is not None and override_reason is None:
            return contradiction

        contradicts_canonical = contradiction is not None

        # Write to graph
        self._g.add_edge(
            source_id, target_id,
            relation=relation_type,
            strength=strength,
            provenance="user",
            contradicts_canonical=contradicts_canonical,
        )

        # Add reverse edge for symmetric relations
        if relation_type in SYMMETRIC_RELATIONS:
            self._g.add_edge(
                target_id, source_id,
                relation=relation_type,
                strength=strength,
                provenance="user",
                contradicts_canonical=contradicts_canonical,
            )

        # Write to SQLite
        self._store.insert_user_edge(
            source_id, target_id, relation_type,
            properties={"strength": strength},
            contradicts_canonical=contradicts_canonical,
        )

        self._invalidate_caches()

        return {"status": "created", "id": f"{source_id}->{target_id}:{relation_type}"}

    # ------------------------------------------------------------------
    # Contradiction detection
    # ------------------------------------------------------------------

    def check_contradiction(
        self, source_id: str, target_id: str, proposed_relation: str
    ) -> ContradictionWarning | None:
        """Check if proposed edge contradicts an existing edge."""
        contradicts = CONTRADICTION_MAP.get(proposed_relation, [])
        if not contradicts:
            return None

        for existing_relation in contradicts:
            # Check both directions
            for u, v in [(source_id, target_id), (target_id, source_id)]:
                if self._g.has_edge(u, v):
                    edge = self._g.edges[u, v]
                    if edge.get("relation") == existing_relation:
                        return ContradictionWarning(
                            existing={
                                "source": u,
                                "target": v,
                                "relation": existing_relation,
                                "strength": edge.get("strength"),
                                "provenance": edge.get("provenance"),
                            },
                            proposed={
                                "source": source_id,
                                "target": target_id,
                                "relation": proposed_relation,
                            },
                        )
        return None

    # ------------------------------------------------------------------
    # Validation (dry-run)
    # ------------------------------------------------------------------

    def validate_mutation(self, proposed: dict) -> dict:
        """Dry-run validation without writing."""
        op = proposed.get("operation")
        if op == "add_construct":
            node_id = f"{proposed['branch']}.{proposed['x']}_{proposed['y']}"
            if node_id in self._g.nodes:
                return {"valid": False, "reason": f"ID collision: {node_id}"}
            return {"valid": True}
        elif op == "add_relation":
            contra = self.check_contradiction(
                proposed["source_id"], proposed["target_id"], proposed["relation_type"]
            )
            if contra:
                return {"valid": False, "reason": "contradiction", "details": contra.to_dict()}
            return {"valid": True}
        return {"valid": False, "reason": f"Unknown operation: {op}"}
