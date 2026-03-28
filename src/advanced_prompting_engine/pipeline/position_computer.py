"""Stage 3 — Position Computer: project coordinate into embedding space.

Authoritative source: Spec 06 §3.
Computes weighted centroid and per-branch neighborhoods.
"""

from __future__ import annotations

import numpy as np

from advanced_prompting_engine.graph.schema import ALL_BRANCHES, PipelineState


class PositionComputer:
    """Stage 3: Compute manifold position from coordinate in embedding space."""

    def __init__(self, embedding_cache, query_layer):
        self._embedding = embedding_cache
        self._query = query_layer

    def execute(self, state: PipelineState):
        if state.coordinate is None:
            raise RuntimeError("Stage 3 requires coordinate from Stage 2")

        coord = state.coordinate
        weighted_embeddings = []
        weights = []

        for branch in ALL_BRANCHES:
            entry = coord[branch]
            construct_id = f"{branch}.{entry['x']}_{entry['y']}"
            try:
                emb = self._embedding.get(construct_id)
            except KeyError:
                continue
            w = entry["weight"]
            weighted_embeddings.append(w * emb)
            weights.append(w)

        # Centroid
        weight_sum = sum(weights)
        if weight_sum > 0 and weighted_embeddings:
            centroid = np.sum(weighted_embeddings, axis=0) / weight_sum
        else:
            centroid = np.zeros(0)

        # Per-branch neighborhoods
        per_branch = {}
        for branch in ALL_BRANCHES:
            entry = coord[branch]
            primary_id = f"{branch}.{entry['x']}_{entry['y']}"
            try:
                primary_emb = self._embedding.get(primary_id)
            except KeyError:
                per_branch[branch] = {"primary": primary_id, "nearby": []}
                continue

            # Find nearby constructs in this branch
            nearby = []
            constructs = self._query.list_constructs(branch)
            for c in constructs:
                cid = c["id"]
                if cid == primary_id:
                    continue
                try:
                    c_emb = self._embedding.get(cid)
                except KeyError:
                    continue
                dist = float(np.linalg.norm(primary_emb - c_emb))
                if dist > 0:
                    nearby.append({"id": cid, "distance": dist, **c})

            nearby.sort(key=lambda n: n["distance"])
            per_branch[branch] = {"primary": primary_id, "nearby": nearby}

        state.manifold_position = {
            "centroid": centroid,
            "per_branch": per_branch,
        }
