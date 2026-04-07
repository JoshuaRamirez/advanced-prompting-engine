"""Centrality cache — DEPRECATED in v2.

v2 potency is position-derived on a regular grid (CONSTRUCT-v2.md §5.4).
Centrality computed graph-theoretic importance from topology;
the regular v2 grid makes this unnecessary — corners are most potent,
center points are most compositional, by definition.

This module is retained as a stub for backwards compatibility.
"""

from __future__ import annotations


class CentralityCache:
    """Stub — v2 does not use graph centrality."""

    def __init__(self):
        self._initialized = False

    def initialize(self, G):
        self._initialized = True

    def validate(self, G) -> bool:
        return self._initialized

    def invalidate(self):
        self._initialized = False

    def ensure_valid(self, G):
        if not self._initialized:
            self.initialize(G)

    def get(self, node_id: str) -> dict[str, float]:
        return {"betweenness": 0.0, "pagerank": 0.0}

    @property
    def is_initialized(self) -> bool:
        return self._initialized
