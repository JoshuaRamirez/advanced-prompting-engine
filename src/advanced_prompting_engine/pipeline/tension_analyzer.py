"""Stage 5 — Tension Analyzer: compute positional tensions + spectrum oppositions.

Authoritative source: CONSTRUCT-v2.md (8-stage forward pass, Stage 5).

v2 uses positional correspondence for inter-face tension (coordinate distance
modulated by cube tier) instead of v1's declared-edge traversal.
Also computes intra-face spectrum tensions for edge-classified active constructs.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import NexusTier, PipelineState
from advanced_prompting_engine.math.tension import (
    compute_spectrum_tensions,
    compute_tensions,
)


class TensionAnalyzer:
    """Stage 5: Compute positional inter-face tensions and intra-face spectrum tensions."""

    def __init__(self, graph, query_layer):
        self._graph = graph
        self._query = query_layer

    def execute(self, state: PipelineState):
        if state.active_constructs is None:
            raise RuntimeError("Stage 5 requires active_constructs from Stage 4")

        # Build nexus_tiers lookup from the graph's nexus nodes
        nexus_tiers = self._build_nexus_tiers()

        # Inter-face positional tensions
        positional = compute_tensions(state.active_constructs, nexus_tiers)

        # Intra-face spectrum tensions
        spectrum = compute_spectrum_tensions(state.active_constructs, self._graph)

        state.tensions = {
            "total_magnitude": positional["total_magnitude"],
            "positional": positional["tensions"],
            "spectrum": spectrum,
        }

    def _build_nexus_tiers(self) -> dict[tuple[str, str], str]:
        """Extract cube tier for every nexus pair from the graph's nexus nodes.

        Returns string tier values (e.g. "paired", "adjacent", "opposite")
        matching the keys used by TIER_WEIGHTS in math/tension.py.
        """
        tiers: dict[tuple[str, str], str] = {}
        G = self._query.graph

        for node_id, data in G.nodes(data=True):
            if data.get("type") != "nexus":
                continue
            source_face = data.get("source_face")
            target_face = data.get("target_face")
            tier_value = data.get("cube_tier")
            if source_face and target_face and tier_value:
                # Store as string — TIER_WEIGHTS uses NexusTier.X.value strings as keys
                tier_str = _normalize_tier_string(tier_value)
                tiers[(source_face, target_face)] = tier_str

        return tiers


def _normalize_tier_string(tier_value: str) -> str:
    """Normalize a tier value to one of the canonical tier strings.

    Accepts either a raw string ("paired") or handles any case mismatch.
    Falls back to "adjacent" if unrecognized.
    """
    normalized = tier_value.lower().strip()
    valid = {t.value for t in NexusTier}
    return normalized if normalized in valid else NexusTier.ADJACENT.value
