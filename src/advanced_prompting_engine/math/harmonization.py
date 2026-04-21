"""Harmonization scoring — paired face resonance.

Authoritative source: CONSTRUCT-v2.md §12.

Paired faces (inside/outside of the same cube face) are structurally tuned
to receive each other's activations. Harmonization measures how well the
activations on two paired faces correspond positionally.

Polarity convention provides commensurability (same position = same archetype).
Cube pairing provides directionality (specific faces listen to each other).
This module computes the resonance between paired faces.
"""

from __future__ import annotations

import numpy as np

from advanced_prompting_engine.graph.schema import (
    CUBE_PAIRS,
    CUBE_PAIR_DIRECTIONS,
    GRID_SIZE,
)


def compute_harmonization(
    active_constructs: dict[str, list[dict]],
) -> list[dict]:
    """Compute harmonization scores for all 6 complementary pairs.

    For each pair, measures positional correspondence: how closely the
    activation patterns on both faces align in the shared coordinate system.

    Returns list of 6 dicts, one per cube pair.
    """
    results = []

    for face_a, face_b in CUBE_PAIRS:
        constructs_a = active_constructs.get(face_a, [])
        constructs_b = active_constructs.get(face_b, [])

        # Determine grounding direction for this pair (ADR-014).
        # CUBE_PAIR_DIRECTIONS key is the grounding face regardless of
        # the tuple order in CUBE_PAIRS.
        if face_a in CUBE_PAIR_DIRECTIONS and CUBE_PAIR_DIRECTIONS[face_a] == face_b:
            grounding_face, grounded_face = face_a, face_b
            constructs_ground = constructs_a
            constructs_grounded = constructs_b
        elif face_b in CUBE_PAIR_DIRECTIONS and CUBE_PAIR_DIRECTIONS[face_b] == face_a:
            grounding_face, grounded_face = face_b, face_a
            constructs_ground = constructs_b
            constructs_grounded = constructs_a
        else:
            # No directional mapping — fall back to symmetric only.
            grounding_face = None
            grounded_face = None
            constructs_ground = []
            constructs_grounded = []

        if not constructs_a or not constructs_b:
            results.append({
                "pair": [face_a, face_b],
                "resonance": 0.0,
                "directional_resonance": 0.0,
                "grounding_face": grounding_face,
                "grounded_face": grounded_face,
                "alignment": 0.0,
                "coverage_a": 0.0,
                "coverage_b": 0.0,
            })
            continue

        alignment = _positional_alignment(constructs_a, constructs_b)
        coverage_a = _activation_coverage(constructs_a)
        coverage_b = _activation_coverage(constructs_b)

        # Symmetric resonance: both faces must be activated AND aligned.
        # Retained for backward compat and as the "both together" metric.
        resonance = alignment * np.sqrt(coverage_a * coverage_b)

        # Directional resonance (ADR-014): measures whether the grounded
        # face's activations correspond to the grounding face's positions,
        # weighted by the grounding face's own coverage. High when the
        # grounded stance is genuinely grounded; zero when grounded is
        # activated without its grounding foundation. Unlike symmetric,
        # this does NOT require the grounded face to be densely activated —
        # it credits the pattern "grounding present, grounded inherited or
        # implicit" that symmetric under-reports (field-observation case:
        # inherited-plan execution prompts).
        if grounding_face is not None and constructs_ground and constructs_grounded:
            coverage_ground = _activation_coverage(constructs_ground)
            alignment_g_to_g = _directional_alignment(
                constructs_grounded, constructs_ground,
            )
            directional_resonance = float(alignment_g_to_g * coverage_ground)
        else:
            directional_resonance = 0.0

        results.append({
            "pair": [face_a, face_b],
            "resonance": float(resonance),
            "directional_resonance": directional_resonance,
            "grounding_face": grounding_face,
            "grounded_face": grounded_face,
            "alignment": float(alignment),
            "coverage_a": float(coverage_a),
            "coverage_b": float(coverage_b),
        })

    return results


def _positional_alignment(
    constructs_a: list[dict],
    constructs_b: list[dict],
) -> float:
    """Measure how closely two activation patterns align positionally.

    Computes alignment bidirectionally (A→B and B→A) and returns the
    average, ensuring symmetric results regardless of which face has
    more activations.

    Returns 1.0 for perfect alignment, approaches 0.0 for maximally
    distant activations.
    """
    align_ab = _directional_alignment(constructs_a, constructs_b)
    align_ba = _directional_alignment(constructs_b, constructs_a)
    return (align_ab + align_ba) / 2.0


def _directional_alignment(
    from_constructs: list[dict],
    to_constructs: list[dict],
) -> float:
    """One-directional alignment: for each point in from_constructs, find
    the nearest point in to_constructs and average the proximity."""
    if not from_constructs or not to_constructs:
        return 0.0

    max_dist = np.sqrt(2) * (GRID_SIZE - 1)

    total_proximity = 0.0
    for ca in from_constructs:
        min_dist = max_dist
        for cb in to_constructs:
            d = np.sqrt((ca["x"] - cb["x"]) ** 2 + (ca["y"] - cb["y"]) ** 2)
            min_dist = min(min_dist, d)
        total_proximity += 1.0 - (min_dist / max_dist)

    return total_proximity / len(from_constructs)


def _activation_coverage(constructs: list[dict]) -> float:
    """Measure how much of the face's potency is activated.

    Returns ratio of activated potency to approximate max potency.
    """
    activated_potency = sum(c["potency"] for c in constructs)
    max_potency = 44 * 0.85 + 100 * 0.6  # approximate max for 12x12 grid
    return min(activated_potency / max(max_potency, 1e-10), 1.0)
