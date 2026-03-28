"""Spectral embedding cache — lifecycle-managed.

Authoritative source: Spec 09.
Computed at startup, invalidated on graph mutation, recomputed lazily.
"""

from __future__ import annotations

import networkx as nx
import numpy as np

from advanced_prompting_engine.cache.hashing import compute_graph_hash
from advanced_prompting_engine.math.embedding import compute_spectral_embedding


class EmbeddingCache:
    """Lifecycle-managed cache for spectral node embeddings."""

    def __init__(self):
        self._embeddings: dict[str, np.ndarray] = {}
        self._graph_hash: str = ""

    def initialize(self, G: nx.Graph):
        self._embeddings = compute_spectral_embedding(G)
        self._graph_hash = compute_graph_hash(G)

    def validate(self, G: nx.Graph) -> bool:
        return compute_graph_hash(G) == self._graph_hash

    def invalidate(self):
        self._embeddings = {}
        self._graph_hash = ""

    def ensure_valid(self, G: nx.Graph):
        if not self._graph_hash or not self.validate(G):
            self.initialize(G)

    def get(self, node_id: str) -> np.ndarray:
        if node_id not in self._embeddings:
            raise KeyError(f"Embedding not found for {node_id!r}. Cache may need rebuild.")
        return self._embeddings[node_id]

    def all_embeddings(self) -> dict[str, np.ndarray]:
        return self._embeddings

    @property
    def is_initialized(self) -> bool:
        return bool(self._graph_hash)
