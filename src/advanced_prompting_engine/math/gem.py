"""Gem magnitude computation — potency-weighted activation with cube tier modulation.

Authoritative source: CONSTRUCT-v2.md §9.3.

v2 replaces v1's cross-face edge traversal with positional activation scoring.
Gems are the condensed state of nexus interactions. Their magnitude reflects
how strongly both faces are activated, modulated by the cube tier:
- Paired gems carry complementary resonance
- Adjacent gems carry proximal interaction
- Opposite gems carry maximal contrast
"""

from __future__ import annotations

import numpy as np

from advanced_prompting_engine.graph.schema import GRID_SIZE, NexusTier
from advanced_prompting_engine.math.tension import positional_distance


# Paired gems get a resonance bonus — they're designed to harmonize.
TIER_GEM_MODIFIERS: dict[str, float] = {
    NexusTier.PAIRED.value: 1.3,
    NexusTier.ADJACENT.value: 1.0,
    NexusTier.OPPOSITE.value: 0.8,
}


def compute_gem(
    source_face: str,
    target_face: str,
    active_constructs: dict[str, list[dict]],
    cube_tier: str,
) -> dict:
    """Compute gem for one directional nexus.

    Uses potency-weighted activation ratios with harmonic mean,
    modulated by cube tier. No graph traversal required.
    """
    source_constructs = active_constructs.get(source_face, [])
    target_constructs = active_constructs.get(target_face, [])

    source_energy = sum(c.get("effective_potency", c["potency"]) for c in source_constructs)
    target_energy = sum(c.get("effective_potency", c["potency"]) for c in target_constructs)

    # Maximum possible energy: all 144 positions activated at their potency.
    # Use a reasonable estimate: 44 edge points at ~0.8 avg + 100 center at 0.6
    max_energy = 44 * 0.85 + 100 * 0.6  # ~97.4

    source_ratio = source_energy / max(max_energy, 1e-10)
    target_ratio = target_energy / max(max_energy, 1e-10)

    # Harmonic mean ensures both faces must contribute
    if source_ratio + target_ratio < 1e-10:
        magnitude = 0.0
    else:
        magnitude = 2 * source_ratio * target_ratio / (source_ratio + target_ratio)

    # Positional correspondence factor: same-position activations → near 1.0,
    # opposite-position activations → near 0.0
    correspondence = _positional_correspondence(source_constructs, target_constructs)
    magnitude *= correspondence

    # Cube tier modulation
    tier_mod = TIER_GEM_MODIFIERS.get(cube_tier, 1.0)
    magnitude *= tier_mod

    # Determine harmony type from positional correspondence
    harmony_type = _classify_gem_type(source_constructs, target_constructs, cube_tier)

    return {
        "nexus": f"nexus.{source_face}.{target_face}",
        "magnitude": magnitude,
        "type": harmony_type,
        "source_energy": source_ratio,
        "target_energy": target_ratio,
        "cube_tier": cube_tier,
    }


def _positional_correspondence(
    source_constructs: list[dict],
    target_constructs: list[dict],
) -> float:
    """Average positional proximity between activated constructs on two faces.

    Same-position activations yield correspondence near 1.0.
    Opposite-position activations yield correspondence near 0.0.
    This makes gems sensitive to WHERE activations fall, not just energy.
    """
    if not source_constructs or not target_constructs:
        return 0.0

    total = 0.0
    count = 0
    for sc in source_constructs:
        for tc in target_constructs:
            dist = positional_distance(sc["x"], sc["y"], tc["x"], tc["y"])
            total += (1.0 - dist)
            count += 1

    return total / max(count, 1)


def _classify_gem_type(
    source_constructs: list[dict],
    target_constructs: list[dict],
    cube_tier: str,
) -> str:
    """Classify gem as harmonious or conflicting based on positional correspondence.

    If activations are at similar positions on both faces → harmonious.
    If activations are at distant/opposite positions → conflicting.
    Paired faces bias toward harmony.
    """
    if not source_constructs or not target_constructs:
        return "inactive"

    # Compute mean position for each face's activations
    sx = np.mean([c["x"] for c in source_constructs])
    sy = np.mean([c["y"] for c in source_constructs])
    tx = np.mean([c["x"] for c in target_constructs])
    ty = np.mean([c["y"] for c in target_constructs])

    max_dist = np.sqrt(2) * (GRID_SIZE - 1)
    dist = np.sqrt((sx - tx) ** 2 + (sy - ty) ** 2) / max_dist

    # Paired faces have a lower threshold for harmony
    threshold = 0.4 if cube_tier == NexusTier.PAIRED.value else 0.5

    return "harmonious" if dist < threshold else "conflicting"
