"""Stage 4 — Construct Resolver: determine active constructs per branch.

Authoritative source: Spec 06 §4.
Primary construct always active. Nearby within adaptive threshold also activate.
Threshold: 60% of mean nearest-neighbor distance within each branch.
"""

from __future__ import annotations

import numpy as np

from advanced_prompting_engine.graph.schema import ALL_BRANCHES, PipelineState


class ConstructResolver:
    """Stage 4: Resolve primary + nearby active constructs per branch."""

    def __init__(self, query_layer, embedding_cache):
        self._query = query_layer
        self._embedding = embedding_cache

    def execute(self, state: PipelineState):
        if state.manifold_position is None:
            raise RuntimeError("Stage 4 requires manifold_position from Stage 3")

        per_branch = state.manifold_position["per_branch"]
        active_constructs = {}

        for branch in ALL_BRANCHES:
            branch_data = per_branch.get(branch, {})
            primary_id = branch_data.get("primary")
            nearby = branch_data.get("nearby", [])

            # Always include the primary construct
            primary = self._query.get_construct_by_id(primary_id)
            if primary is None:
                active_constructs[branch] = []
                continue

            active = [primary]

            # Compute activation threshold: 60% of mean nearest-neighbor distance
            threshold = self._compute_activation_threshold(branch, nearby)

            for n in nearby:
                if n["distance"] < threshold:
                    active.append(n)

            active_constructs[branch] = active

        state.active_constructs = active_constructs

    def _compute_activation_threshold(self, branch: str, nearby: list[dict]) -> float:
        """Adaptive threshold: 60% of mean nearest-neighbor distance in this branch."""
        if len(nearby) < 2:
            return 0.0  # no neighbors to activate

        # Use the distances from the nearby list (already sorted)
        distances = [n["distance"] for n in nearby if n["distance"] > 0]
        if not distances:
            return 0.0

        mean_nn = float(np.mean(distances[:10]))  # use closest 10 as representative
        return mean_nn * 0.6
