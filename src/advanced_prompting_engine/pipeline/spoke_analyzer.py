"""Stage 7 — Spoke Analyzer: per-branch behavioral signatures + central gem.

Authoritative source: Spec 06 §7, Spec 08.
All 10 spokes always present. Inactive branches get empty spokes.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import ALL_BRANCHES, PipelineState
from advanced_prompting_engine.math.spoke import (
    classify_spoke,
    compute_central_gem,
    compute_contributions,
    compute_spoke_shape,
)


class SpokeAnalyzer:
    """Stage 7: Aggregate gems into spoke profiles and central gem coherence."""

    def execute(self, state: PipelineState):
        gems = state.gems or []

        spokes = {}
        for branch in ALL_BRANCHES:
            # Gather gems where this branch is the source
            branch_gems = [
                g for g in gems
                if g["nexus"].startswith(f"nexus.{branch}.")
            ]
            spoke = compute_spoke_shape(branch_gems)
            spokes[branch] = spoke

        # Compute contributions across all spokes
        compute_contributions(spokes)

        # Classify each spoke
        for branch in ALL_BRANCHES:
            spokes[branch]["classification"] = classify_spoke(spokes[branch])

        # Central gem coherence
        central_gem = compute_central_gem(spokes)

        state.spokes = spokes
        state.central_gem = central_gem
