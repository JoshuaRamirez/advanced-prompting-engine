"""Stage 2 — Coordinate Resolver: fill null axes via CSP.

Authoritative source: Spec 06 §2.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import PipelineState
from advanced_prompting_engine.math.csp import resolve_coordinate


class CoordinateResolver:
    """Stage 2: Fill null axes in partial coordinate via constraint satisfaction."""

    def __init__(self, graph):
        self._graph = graph

    def execute(self, state: PipelineState):
        if state.partial_coordinate is None:
            raise RuntimeError("Stage 2 requires partial_coordinate from Stage 1")
        state.coordinate = resolve_coordinate(state.partial_coordinate, self._graph)
