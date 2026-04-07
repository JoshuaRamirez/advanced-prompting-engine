"""Graph Mutation Layer — writes with contradiction detection.

Authoritative source: CONSTRUCT-v2.md, ADR-006.
Invalidates caches on any write.
"""

from __future__ import annotations

import networkx as nx

from advanced_prompting_engine.graph.grid import classify, potency
from advanced_prompting_engine.graph.schema import (
    CONTRADICTION_MAP,
    GRID_SIZE,
    SYMMETRIC_RELATIONS,
)
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
        tfidf_cache=None,
    ):
        self._g = G
        self._store = store
        self._caches = [c for c in [tfidf_cache] if c is not None]

    def _invalidate_caches(self):
        for cache in self._caches:
            cache.invalidate()

    # ------------------------------------------------------------------
    # Add construct
    # ------------------------------------------------------------------

    def add_construct(
        self,
        face: str,
        x: int,
        y: int,
        question: str,
        tags: list[str],
        description: str,
        provenance: str = "user",
    ) -> dict:
        """Add a user construct at a grid position."""
        max_coord = GRID_SIZE - 1

        if face not in self._g.nodes or self._g.nodes[face].get("type") != "face":
            raise ValueError(f"Face {face!r} does not exist")

        if not (0 <= x <= max_coord and 0 <= y <= max_coord):
            raise ValueError(f"Grid position ({x}, {y}) out of range (0-{max_coord})")

        node_id = f"{face}.{x}_{y}"
        if node_id in self._g.nodes:
            raise ValueError(f"Construct {node_id!r} already exists")

        cls = classify(x, y)
        pot = potency(x, y)

        node = {
            "id": node_id,
            "type": "construct",
            "tier": 2,
            "face": face,
            "x": x,
            "y": y,
            "classification": cls,
            "potency": pot,
            "question": question,
            "description": description,
            "tags": tags,
            "provenance": provenance,
            "mutable": True,
        }

        self._g.add_node(node_id, **node)
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
        if source_id not in self._g.nodes:
            raise ValueError(f"Source node {source_id!r} does not exist")
        if target_id not in self._g.nodes:
            raise ValueError(f"Target node {target_id!r} does not exist")

        contradiction = self.check_contradiction(source_id, target_id, relation_type)
        if contradiction is not None and override_reason is None:
            return contradiction

        contradicts_canonical = contradiction is not None

        self._g.add_edge(
            source_id, target_id,
            relation=relation_type,
            strength=strength,
            provenance="user",
            contradicts_canonical=contradicts_canonical,
        )

        if relation_type in SYMMETRIC_RELATIONS:
            self._g.add_edge(
                target_id, source_id,
                relation=relation_type,
                strength=strength,
                provenance="user",
                contradicts_canonical=contradicts_canonical,
            )

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
        max_coord = GRID_SIZE - 1
        op = proposed.get("operation")
        if op == "add_construct":
            node_id = f"{proposed['face']}.{proposed['x']}_{proposed['y']}"
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
