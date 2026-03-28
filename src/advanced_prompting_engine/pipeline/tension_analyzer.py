"""Stage 5 — Tension Analyzer: compute potency-weighted tensions + spectrum oppositions.

Authoritative source: Spec 06 §5.
Retrieves spectrum_question from SPECTRUM_OPPOSITION edge properties.
Scans for RESOLVES edges for each tension pair.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import PipelineState
from advanced_prompting_engine.math.tension import compute_tensions


class TensionAnalyzer:
    """Stage 5: Compute direct, spectrum, and cascading tensions."""

    def __init__(self, graph):
        self._graph = graph

    def execute(self, state: PipelineState):
        if state.active_constructs is None:
            raise RuntimeError("Stage 5 requires active_constructs from Stage 4")
        state.tensions = compute_tensions(state.active_constructs, self._graph)
