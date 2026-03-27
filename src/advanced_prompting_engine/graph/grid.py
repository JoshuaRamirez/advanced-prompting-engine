"""Grid mechanics — classification, potency, and spectrum generation.

Authoritative source: Spec 02 (grid-mechanics.md).
Dual midpoint model: positions 4 AND 5 on each edge are midpoints (8 total).
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify(x: int, y: int) -> str:
    """Classify a grid position by its structural role.

    Returns one of: 'corner', 'midpoint', 'edge', 'center'.
    """
    is_corner = (x in (0, 9)) and (y in (0, 9))
    is_x_midpoint = (x in (4, 5)) and (y in (0, 9))
    is_y_midpoint = (x in (0, 9)) and (y in (4, 5))
    is_edge = (x in (0, 9)) or (y in (0, 9))

    if is_corner:
        return "corner"
    if is_x_midpoint or is_y_midpoint:
        return "midpoint"
    if is_edge:
        return "edge"
    return "center"


# ---------------------------------------------------------------------------
# Potency
# ---------------------------------------------------------------------------

POTENCY: dict[str, float] = {
    "corner": 1.0,
    "midpoint": 0.9,
    "edge": 0.8,
    "center": 0.6,
}


def potency(x: int, y: int) -> float:
    """Derive potency from grid position."""
    return POTENCY[classify(x, y)]


# ---------------------------------------------------------------------------
# Spectrum generation
# ---------------------------------------------------------------------------

def generate_spectrums(branch: str) -> list[tuple[str, str, str]]:
    """Generate all valid edge-to-edge reflection pairs for a branch.

    Returns list of (spectrum_id, point_a_id, point_b_id).
    Each pair has both endpoints edge-classified (corner, midpoint, or edge).
    Produces exactly 18 unique spectrums per branch.
    """
    spectrums: list[tuple[str, str, str]] = []
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()

    for x in range(10):
        for y in range(10):
            if classify(x, y) in ("corner", "midpoint", "edge"):
                ox, oy = 9 - x, 9 - y
                if classify(ox, oy) in ("corner", "midpoint", "edge"):
                    pair = tuple(sorted([(x, y), (ox, oy)]))
                    if pair not in seen:
                        seen.add(pair)
                        a_id = f"{branch}.{x}_{y}"
                        b_id = f"{branch}.{ox}_{oy}"
                        sid = f"{branch}.spectrum_{len(spectrums)}"
                        spectrums.append((sid, a_id, b_id))

    return spectrums


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_edge_point(x: int, y: int) -> bool:
    """True if position is on the grid perimeter (any edge classification)."""
    return classify(x, y) in ("corner", "midpoint", "edge")
