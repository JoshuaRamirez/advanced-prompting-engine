"""Stage 6 — Nexus/Gem Analyzer: compute gems for active branch pairs.

Authoritative source: Spec 06 §6, Spec 07.
Does NOT consume Stage 5 tensions — harmony determined independently.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import PipelineState
from advanced_prompting_engine.math.gem import compute_gem


class NexusGemAnalyzer:
    """Stage 6: Compute gem for each pair of active branches."""

    def __init__(self, graph):
        self._graph = graph

    def execute(self, state: PipelineState):
        if state.active_constructs is None:
            raise RuntimeError("Stage 6 requires active_constructs from Stage 4")

        active_branches = [
            b for b, constructs in state.active_constructs.items()
            if constructs
        ]

        gems = []
        nexus_details = []

        for source in active_branches:
            for target in active_branches:
                if source == target:
                    continue
                gem = compute_gem(source, target, state.active_constructs, self._graph)
                gems.append(gem)
                nexus_details.append({
                    "nexus": gem["nexus"],
                    "source_branch": source,
                    "target_branch": target,
                    "magnitude": gem["magnitude"],
                    "type": gem["type"],
                })

        state.gems = gems
        state.nexus_details = nexus_details
