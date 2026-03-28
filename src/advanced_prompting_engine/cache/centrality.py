"""Centrality cache — lifecycle-managed.

Authoritative source: Spec 09.
Used by Coordinate Resolver (tiebreaker) and Generative Analyzer.
"""

from __future__ import annotations

import networkx as nx

from advanced_prompting_engine.cache.hashing import compute_graph_hash
from advanced_prompting_engine.math.centrality import compute_centralities


class CentralityCache:
    """Lifecycle-managed cache for betweenness centrality and PageRank."""

    def __init__(self):
        self._centralities: dict[str, dict[str, float]] = {}
        self._graph_hash: str = ""

    def initialize(self, G: nx.Graph):
        self._centralities = compute_centralities(G)
        self._graph_hash = compute_graph_hash(G)

    def validate(self, G: nx.Graph) -> bool:
        return compute_graph_hash(G) == self._graph_hash

    def invalidate(self):
        self._centralities = {}
        self._graph_hash = ""

    def ensure_valid(self, G: nx.Graph):
        if not self._graph_hash or not self.validate(G):
            self.initialize(G)

    def get(self, node_id: str) -> dict[str, float]:
        return self._centralities.get(node_id, {"betweenness": 0.0, "pagerank": 0.0})

    @property
    def is_initialized(self) -> bool:
        return bool(self._graph_hash)
