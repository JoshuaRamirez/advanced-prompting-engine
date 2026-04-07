"""Grid mechanics — classification, potency, spectrum generation, and degree labeling.

Authoritative source: CONSTRUCT-v2.md §5 (Face Structure).
12x12 grid with dual midpoint model: positions 5 AND 6 on each edge are midpoints (8 total).
"""

from __future__ import annotations

import numpy as np

from advanced_prompting_engine.graph.schema import GRID_SIZE

_MAX_POS = GRID_SIZE - 1
_MID_POSITIONS = (GRID_SIZE // 2 - 1, GRID_SIZE // 2)  # (5, 6) for GRID_SIZE=12


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify(x: int, y: int) -> str:
    """Classify a grid position by its structural role.

    Per CONSTRUCT-v2.md §5.3:
      - Corner:   both coordinates in {0, _MAX_POS}
      - Midpoint: one coordinate in {0, _MAX_POS} AND the other in _MID_POSITIONS
      - Edge:     at least one coordinate in {0, _MAX_POS} (not corner or midpoint)
      - Center:   both coordinates in 1–(_MAX_POS-1)

    Returns one of: 'corner', 'midpoint', 'edge', 'center'.
    """
    is_corner = (x in (0, _MAX_POS)) and (y in (0, _MAX_POS))
    is_x_midpoint = (x in _MID_POSITIONS) and (y in (0, _MAX_POS))
    is_y_midpoint = (x in (0, _MAX_POS)) and (y in _MID_POSITIONS)
    is_edge = (x in (0, _MAX_POS)) or (y in (0, _MAX_POS))

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
    """Derive potency from grid position.

    Per CONSTRUCT-v2.md §5.4, four-level hierarchy:
    corner (1.0) > midpoint (0.9) > edge (0.8) > center (0.6).
    """
    return POTENCY[classify(x, y)]


def potency_matrix() -> np.ndarray:
    """Return a 12x12 numpy array of precomputed potency values.

    Element [x, y] contains the potency for grid position (x, y).
    Useful for vectorized operations across the full face.
    """
    matrix = np.empty((GRID_SIZE, GRID_SIZE), dtype=np.float64)
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            matrix[x, y] = potency(x, y)
    return matrix


# ---------------------------------------------------------------------------
# Spectrum generation
# ---------------------------------------------------------------------------

def generate_spectrums(face: str) -> list[tuple[str, str, str]]:
    """Generate all valid edge-to-edge reflection pairs for a face.

    Per CONSTRUCT-v2.md §5.3, reflections use (_MAX_POS-x, _MAX_POS-y) on the grid.
    Both endpoints must be edge-classified (corner, midpoint, or edge).

    Returns list of (spectrum_id, point_a_id, point_b_id).
    Produces exactly 22 unique spectrums per face.
    """
    spectrums: list[tuple[str, str, str]] = []
    seen: set[tuple[tuple[int, int], tuple[int, int]]] = set()

    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            if classify(x, y) in ("corner", "midpoint", "edge"):
                ox, oy = _MAX_POS - x, _MAX_POS - y
                if classify(ox, oy) in ("corner", "midpoint", "edge"):
                    pair = tuple(sorted([(x, y), (ox, oy)]))
                    if pair not in seen:
                        seen.add(pair)
                        a_id = f"{face}.{x}_{y}"
                        b_id = f"{face}.{ox}_{oy}"
                        sid = f"{face}.spectrum_{len(spectrums)}"
                        spectrums.append((sid, a_id, b_id))

    return spectrums


# ---------------------------------------------------------------------------
# Degree labeling
# ---------------------------------------------------------------------------

def degree_label(position: int, axis_low: str, axis_high: str) -> str:
    """Return the qualitative degree label for a position (0–_MAX_POS) on an axis.

    Per CONSTRUCT-v2.md §5.2, positions map to qualitative ranges:
      0:          fully {axis_low}
      1-2:        strongly {axis_low}
      3-4:        moderately {axis_low}
      5 (lo-mid): balanced, inclining toward {axis_low}
      6 (hi-mid): balanced, inclining toward {axis_high}
      7-8:        moderately {axis_high}
      9-10:       strongly {axis_high}
      11:         fully {axis_high}
    """
    mid_lo, mid_hi = _MID_POSITIONS
    if position == 0:
        return f"fully {axis_low}"
    if position <= 2:
        return f"strongly {axis_low}"
    if position <= mid_lo - 1:
        return f"moderately {axis_low}"
    if position == mid_lo:
        return f"balanced between {axis_low} and {axis_high}, inclining toward {axis_low}"
    if position == mid_hi:
        return f"balanced between {axis_low} and {axis_high}, inclining toward {axis_high}"
    if position <= _MAX_POS - 3:
        return f"moderately {axis_high}"
    if position <= _MAX_POS - 1:
        return f"strongly {axis_high}"
    # position == _MAX_POS
    return f"fully {axis_high}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def is_edge_point(x: int, y: int) -> bool:
    """True if position is on the grid perimeter (any edge classification).

    Per CONSTRUCT-v2.md §5.3, edge points have at least one coordinate
    equal to 0 or _MAX_POS.
    """
    return classify(x, y) in ("corner", "midpoint", "edge")
