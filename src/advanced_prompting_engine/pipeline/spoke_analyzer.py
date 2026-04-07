"""Stage 7 — Spoke Analyzer: per-face behavioral signatures + central gem.

Authoritative source: CONSTRUCT-v2.md (8-stage forward pass, Stage 7).
12 spokes, 11 gems each. Inactive faces get empty spokes.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import ALL_FACES, PipelineState
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
        for face in ALL_FACES:
            # Gather gems where this face is the source
            face_gems = [
                g for g in gems
                if g["nexus"].startswith(f"nexus.{face}.")
            ]
            spoke = compute_spoke_shape(face_gems)
            spokes[face] = spoke

        # Compute contributions across all spokes
        compute_contributions(spokes)

        # Classify each spoke
        for face in ALL_FACES:
            spokes[face]["classification"] = classify_spoke(spokes[face])

        # Central gem coherence
        central_gem = compute_central_gem(spokes)

        state.spokes = spokes
        state.central_gem = central_gem
