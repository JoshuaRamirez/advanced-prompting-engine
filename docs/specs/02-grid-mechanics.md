# Spec 02 — Grid Mechanics

## Purpose

Defines the algorithms that derive classification, potency, spectrum membership, and sub-dimensional meaning from a grid position (x, y). These are deterministic functions — given a position, all structural properties are computable.

---

## Classification Function

```python
def classify(x: int, y: int) -> str:
    """Determine structural classification from grid position."""
    is_corner = (x in (0, 9)) and (y in (0, 9))
    is_x_midpoint = (x == 4 or x == 5) and (y in (0, 9))  # see note
    is_y_midpoint = (x in (0, 9)) and (y == 4 or y == 5)   # see note
    is_edge = (x in (0, 9)) or (y in (0, 9))

    if is_corner:
        return "corner"
    if is_x_midpoint or is_y_midpoint:
        return "midpoint"
    if is_edge:
        return "edge"
    return "center"
```

**Note on midpoints:** The Construct specifies midpoints at (4,0), (9,4), (4,9), (0,4). In a 0-indexed 10-point grid, position 4 is the 5th point — the nearest to center on the edge. This is used consistently.

### Classification Map (10x10)

```
C = corner, M = midpoint, E = edge, · = center

  0 1 2 3 4 5 6 7 8 9
0 C E E E M E E E E C
1 E · · · · · · · · E
2 E · · · · · · · · E
3 E · · · · · · · · E
4 M · · · · · · · · M
5 E · · · · · · · · E
6 E · · · · · · · · E
7 E · · · · · · · · E
8 E · · · · · · · · E
9 C E E E M E E E E C
```

### Counts

| Classification | Count | Positions |
|---|---|---|
| Corner | 4 | (0,0), (9,0), (0,9), (9,9) |
| Midpoint | 4 | (4,0), (9,4), (4,9), (0,4) |
| Edge (remaining) | 28 | All other perimeter positions |
| Center | 64 | All interior positions (x ∈ 1..8, y ∈ 1..8) |
| **Total** | **100** | |

### The Counting Pattern

The perimeter is traversed as: 10 (top) + 9 (right, excluding shared corner) + 9 (bottom, excluding shared corner) + 9 (left, excluding shared corner) = 37 traversal steps covering 36 unique points.

The 36 edge points encapsulate the 64 center points.

---

## Potency Function

```python
POTENCY = {
    "corner": 1.0,
    "midpoint": 0.95,
    "edge": 0.85,
    "center": 0.5,
}

def potency(x: int, y: int) -> float:
    """Derive potency from grid position."""
    return POTENCY[classify(x, y)]
```

### Potency Semantics

| Classification | Potency | Meaning |
|---|---|---|
| Corner | 1.0 | Combined extreme of both sub-dimensions. Maximum organizational force. |
| Midpoint | 0.95 | Axial balance point at one edge extreme. Maximum centering force. |
| Edge | 0.85 | Intermediate position along one extreme. High directional force. |
| Center | 0.5 | Balanced interior position. Resolution and synthesis. |

Potency is used as a multiplier in tension computation, gem magnitude computation, and spoke aggregation. Higher potency amplifies; lower potency dampens.

---

## Spectrum Generation

Each branch has 20 spectrums generated from geometric opposition of edge points.

### Algorithm

```python
def generate_spectrums(branch: str) -> list[tuple[str, str, str]]:
    """Generate 20 spectrum pairs for a branch.

    Returns list of (spectrum_id, point_a_id, point_b_id).
    """
    spectrums = []

    # Group 1: top-left to bottom-right diagonal pairings (10 spectrums)
    # Pairs: (0,0)↔(9,9), (0,1)↔(9,8), (0,2)↔(9,7), ..., (0,9)↔(9,0)
    for i in range(10):
        a = f"{branch}.0_{i}"
        b = f"{branch}.9_{9 - i}"
        spectrums.append((f"{branch}.spectrum_{len(spectrums)}", a, b))

    # Group 2: top to bottom cross-pairings (10 spectrums)
    # Pairs: (1,0)↔(8,9), (2,0)↔(7,9), ..., (8,0)↔(1,9)
    for i in range(1, 9):
        a = f"{branch}.{i}_0"
        b = f"{branch}.{9 - i}_9"
        spectrums.append((f"{branch}.spectrum_{len(spectrums)}", a, b))

    # Note: Group 2 produces 8 spectrums (i=1..8), not 10.
    # Total: 10 + 8 = 18 spectrums from these two groups.

    # Group 3: left to right horizontal pairings (2 additional spectrums)
    # The remaining edge pairs not covered by diagonal pairings:
    # (0,4)↔(9,4) — left midpoint to right midpoint (horizontal axis)
    # (0,5)↔(9,5) — secondary horizontal pair
    # Note: these may already be covered in Group 1.
    # Exact count depends on pairing strategy.

    return spectrums
```

**Pairing Strategy (Corrected):**

The 20 spectrums per plane are defined by pairing opposite edge points. On a 10x10 grid, "opposite" means the point reflected through the grid center (4.5, 4.5):

```python
def opposite(x: int, y: int) -> tuple[int, int]:
    """Compute the opposite edge point via center reflection."""
    return (9 - x, 9 - y)
```

Each edge point pairs with exactly one opposite. Since the pairing is symmetric (A↔B = B↔A), and there are 36 edge points, there are 36/2 = 18 unique pairs. However, some edge points' opposites are center points (not edge points), which are excluded from spectrum pairing.

**Actual spectrum count per branch:**

Only pairs where BOTH endpoints are edge-classified count as spectrums. The exact count depends on which reflections land on edge vs center positions:

- All 4 corners pair with opposite corners: 2 unique pairs (since (0,0)↔(9,9) and (9,0)↔(0,9))
- Midpoints pair with opposite midpoints: 2 unique pairs ((4,0)↔(5,9) — but (5,9) is center-classified)

This requires computing: for each edge point, is its reflection also an edge point?

```python
def generate_spectrums_precise(branch: str) -> list:
    spectrums = []
    seen = set()
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
                        spectrums.append((f"{branch}.spectrum_{len(spectrums)}", a_id, b_id))
    return spectrums
```

**Pre-computed result:** With the classification map above, the precise count of edge↔edge reflection pairs is **18** per branch, producing **180** total spectrums across 10 branches.

(The original estimate of 20/200 was approximate. The precise algorithm yields 18/180. The Construct's structural claim of "20 spectrums" per plane refers to the broader concept including the 4 edge-as-spectrum structures. For implementation, use the precise algorithm above and accept the count it produces.)

---

## Sub-Dimension Mapping

Each grid position (x, y) has meaning relative to its branch's two sub-dimensions.

### Normalized Position

```python
def sub_dimensional_position(x: int, y: int, branch: str) -> dict:
    """Map grid position to sub-dimensional meaning."""
    return {
        "x_normalized": x / 9.0,  # 0.0 = x_axis_low, 1.0 = x_axis_high
        "y_normalized": y / 9.0,  # 0.0 = y_axis_low, 1.0 = y_axis_high
        "x_label": interpolate_label(x, branch, "x"),
        "y_label": interpolate_label(y, branch, "y"),
    }
```

For Epistemology at position (3, 0):
- x_normalized = 3/9 ≈ 0.33 → leans Empirical (x_low) but not fully
- y_normalized = 0/9 = 0.0 → fully Certain (y_low)
- Meaning: "Mostly empirical, fully certain" — an epistemological stance of observational confidence

### Corner Meanings (per branch)

Each corner is the combined extreme of both sub-dimensions. These are defined in CONSTRUCT-INTEGRATION.md and are deterministic from the branch's sub-dimension labels:

```python
def corner_meaning(branch: str, x: int, y: int) -> str:
    """Generate corner meaning from sub-dimension extremes."""
    branch_def = BRANCH_DEFINITIONS[branch]
    x_label = branch_def["x_axis_low"] if x == 0 else branch_def["x_axis_high"]
    y_label = branch_def["y_axis_low"] if y == 0 else branch_def["y_axis_high"]
    return f"{x_label} + {y_label}"
```

---

## Edge Encapsulation

The 36 edge points form a closed perimeter around the 64 center points. This is a structural invariant:

- No center point can have a sub-dimensional value more extreme than the edge points
- Center points are bounded by the edge points on both sub-dimensions
- The edge defines the envelope; the center resolves within it

In implementation terms: center points' (x, y) values are always in the range [1, 8] on both axes. Edge points have at least one coordinate at 0 or 9.

```python
def is_encapsulated_by(center_x, center_y, edge_points):
    """Verify that a center point is within the edge boundary."""
    assert 1 <= center_x <= 8 and 1 <= center_y <= 8
    return True  # Always true by construction for interior points
```

---

## Corner Bounding

The 4 corners organize the 32 non-corner edge points. Each edge of the grid is bounded by two corners:

| Edge | Start corner | End corner | Non-corner points |
|---|---|---|---|
| Top (y=0) | (0,0) | (9,0) | (1,0) through (8,0) = 8 points |
| Right (x=9) | (9,0) | (9,9) | (9,1) through (9,8) = 8 points |
| Bottom (y=9) | (0,9) | (9,9) | (1,9) through (8,9) = 8 points |
| Left (x=0) | (0,0) | (0,9) | (0,1) through (0,8) = 8 points |

Total non-corner edge points: 32 (8 per side × 4 sides). With 4 corners: 36 total edge points.

The corners are the **organizational bounds** — each non-corner edge point sits on a gradient between two corners, representing an intermediate position between the corners' combined extremes.
