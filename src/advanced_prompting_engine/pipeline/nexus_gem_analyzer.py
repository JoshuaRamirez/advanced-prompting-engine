"""Stage 6 — Nexus/Gem Analyzer: compute gems for active face pairs.

Authoritative source: CONSTRUCT-v2.md (8-stage forward pass, Stage 6).

66 unique nexus pairs (12 faces, choose 2), producing 132 directional gems.
Each gem is modulated by the cube tier of the nexus (paired/adjacent/opposite).
Also computes harmonization scores for the 6 complementary cube pairs.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import NexusTier, PipelineState
from advanced_prompting_engine.math.gem import compute_gem
from advanced_prompting_engine.math.harmonization import compute_harmonization


class NexusGemAnalyzer:
    """Stage 6: Compute gem for each directional pair of active faces + harmonization."""

    def __init__(self, graph, query_layer):
        self._graph = graph
        self._query = query_layer

    def execute(self, state: PipelineState):
        if state.active_constructs is None:
            raise RuntimeError("Stage 6 requires active_constructs from Stage 4")

        # Build cube tier lookup (string values matching TIER_GEM_MODIFIERS keys)
        tier_lookup = self._build_tier_lookup()

        active_faces = [
            f for f, constructs in state.active_constructs.items()
            if constructs
        ]

        gems = []
        nexus_details = []

        for source in active_faces:
            for target in active_faces:
                if source == target:
                    continue

                # Look up cube tier for this directional pair (string value)
                cube_tier = tier_lookup.get(
                    (source, target),
                    tier_lookup.get((target, source), NexusTier.ADJACENT.value),
                )

                gem = compute_gem(
                    source, target, state.active_constructs, cube_tier,
                )
                gems.append(gem)
                nexus_details.append({
                    "nexus": gem["nexus"],
                    "source_face": source,
                    "target_face": target,
                    "magnitude": gem["magnitude"],
                    "type": gem["type"],
                    "cube_tier": gem["cube_tier"],
                })

        state.gems = gems
        state.nexus_details = nexus_details

        # Harmonization for complementary cube pairs
        state.harmonization_pairs = compute_harmonization(state.active_constructs)

    def _build_tier_lookup(self) -> dict[tuple[str, str], str]:
        """Extract cube tier for every nexus pair from the graph's nexus nodes.

        Returns string tier values (e.g. "paired", "adjacent", "opposite")
        matching the keys used by TIER_GEM_MODIFIERS in math/gem.py.
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
