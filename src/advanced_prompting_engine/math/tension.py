"""Positional tension computation — coordinate distance + cube stratification.

Authoritative source: CONSTRUCT-v2.md §9, §12, §14.

v2 replaces v1's declared-edge traversal with positional correspondence:
- Same position across faces = low tension (shared archetype)
- Opposite position across faces = high tension (opposed archetype)
- Cube stratification modulates: paired nexi dampen, opposite nexi amplify
"""

from __future__ import annotations

import numpy as np

from advanced_prompting_engine.graph.schema import GRID_SIZE, NexusTier

# Cube tier weights: how much the nexus tier modulates raw positional tension.
# Paired faces are designed to harmonize (dampen tension).
# Opposite faces are maximally distant (amplify tension).
TIER_WEIGHTS: dict[str, float] = {
    NexusTier.PAIRED.value: 0.4,
    NexusTier.ADJACENT.value: 1.0,
    NexusTier.OPPOSITE.value: 1.5,
}


def positional_distance(x1: int, y1: int, x2: int, y2: int) -> float:
    """Normalized Euclidean distance between two grid positions.

    Returns 0.0 for identical positions, 1.0 for maximally distant (corners).
    """
    max_dist = np.sqrt(2) * (GRID_SIZE - 1)
    raw = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    return float(raw / max_dist)


def positional_tension(
    x1: int, y1: int, potency1: float,
    x2: int, y2: int, potency2: float,
    cube_tier: str,
) -> float:
    """Compute tension between two points on different faces.

    Tension = positional_distance * potency_product * tier_weight.
    """
    dist = positional_distance(x1, y1, x2, y2)
    tier_weight = TIER_WEIGHTS.get(cube_tier, 1.0)
    return dist * potency1 * potency2 * tier_weight


def compute_tensions(
    active_constructs: dict[str, list[dict]],
    nexus_tiers: dict[tuple[str, str], str],
) -> dict:
    """Compute all inter-face tensions from activated positions.

    active_constructs: face → list of dicts with {face, x, y, potency, id}.
    nexus_tiers: (face_a, face_b) → tier string.

    Returns dict with total_magnitude, tensions[].
    """
    faces = list(active_constructs.keys())
    tensions = []

    for i, face_a in enumerate(faces):
        for face_b in faces[i + 1:]:
            tier_key = (face_a, face_b)
            tier = nexus_tiers.get(tier_key, nexus_tiers.get((face_b, face_a), NexusTier.ADJACENT.value))

            for ca in active_constructs[face_a]:
                for cb in active_constructs[face_b]:
                    t = positional_tension(
                        ca["x"], ca["y"], ca.get("effective_potency", ca["potency"]),
                        cb["x"], cb["y"], cb.get("effective_potency", cb["potency"]),
                        tier,
                    )
                    if t >= 0.01:
                        tensions.append({
                            "between": [ca["id"], cb["id"]],
                            "faces": [face_a, face_b],
                            "magnitude": t,
                            "cube_tier": tier,
                            "positional_distance": positional_distance(
                                ca["x"], ca["y"], cb["x"], cb["y"]
                            ),
                        })

    total = sum(t["magnitude"] for t in tensions)

    return {
        "total_magnitude": total,
        "tensions": tensions,
    }


def compute_spectrum_tensions(
    active_constructs: dict[str, list[dict]],
    G,
) -> list[dict]:
    """Compute intra-face spectrum tensions for edge-classified active constructs.

    An active edge point tensions with its geometric opposite on the same face.
    """
    from advanced_prompting_engine.graph.schema import SPECTRUM_OPPOSITION

    spectrum_tensions = []
    seen: set[frozenset] = set()

    for face, constructs in active_constructs.items():
        for c in constructs:
            if c.get("classification") not in ("corner", "midpoint", "edge"):
                continue
            c_id = c["id"]
            for _, neighbor, data in G.edges(c_id, data=True):
                if data.get("relation") != SPECTRUM_OPPOSITION:
                    continue
                pair = frozenset([c_id, neighbor])
                if pair in seen:
                    continue
                seen.add(pair)
                opp_potency = G.nodes[neighbor].get("potency", 0.6)
                mag = 0.6 * c["potency"] * opp_potency
                spectrum_tensions.append({
                    "active": c_id,
                    "opposite": neighbor,
                    "magnitude": mag,
                    "type": "spectrum_geometric",
                })

    return spectrum_tensions
