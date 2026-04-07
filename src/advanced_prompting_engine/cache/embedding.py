"""Spectral embedding cache — DEPRECATED in v2.

v2 positions are grid coordinates, not graph embeddings.
Every point already HAS a position — its (x, y) on the 12x12 grid.
Spectral embedding computed continuous positions from graph topology;
the regular v2 grid makes this unnecessary.

This module is retained as a stub for backwards compatibility.
The compute function is not called by any v2 pipeline stage.
"""

from __future__ import annotations


class EmbeddingCache:
    """Stub — v2 does not use spectral embedding."""

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

    @property
    def is_initialized(self) -> bool:
        return self._initialized
