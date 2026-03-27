"""Tests for grid classification, potency, and spectrum generation."""

from advanced_prompting_engine.graph.grid import classify, potency, generate_spectrums, is_edge_point


def test_classification_counts():
    """Verify 4 corners, 8 midpoints, 24 edge, 64 center = 100 total."""
    counts = {"corner": 0, "midpoint": 0, "edge": 0, "center": 0}
    for x in range(10):
        for y in range(10):
            counts[classify(x, y)] += 1

    assert counts["corner"] == 4
    assert counts["midpoint"] == 8
    assert counts["edge"] == 24
    assert counts["center"] == 64
    assert sum(counts.values()) == 100


def test_corner_positions():
    assert classify(0, 0) == "corner"
    assert classify(9, 0) == "corner"
    assert classify(0, 9) == "corner"
    assert classify(9, 9) == "corner"


def test_midpoint_positions_dual_model():
    """8 midpoints: positions 4 and 5 on each edge."""
    # Top edge
    assert classify(4, 0) == "midpoint"
    assert classify(5, 0) == "midpoint"
    # Right edge
    assert classify(9, 4) == "midpoint"
    assert classify(9, 5) == "midpoint"
    # Bottom edge
    assert classify(4, 9) == "midpoint"
    assert classify(5, 9) == "midpoint"
    # Left edge
    assert classify(0, 4) == "midpoint"
    assert classify(0, 5) == "midpoint"


def test_edge_positions():
    """Non-corner, non-midpoint perimeter positions are 'edge'."""
    assert classify(1, 0) == "edge"
    assert classify(9, 1) == "edge"
    assert classify(8, 9) == "edge"
    assert classify(0, 8) == "edge"


def test_center_positions():
    assert classify(1, 1) == "center"
    assert classify(5, 5) == "center"
    assert classify(4, 4) == "center"
    assert classify(8, 8) == "center"


def test_potency_values():
    assert potency(0, 0) == 1.0  # corner
    assert potency(4, 0) == 0.9  # midpoint
    assert potency(1, 0) == 0.8  # edge
    assert potency(5, 5) == 0.6  # center


def test_spectrum_count_per_branch():
    """Each branch should produce exactly 18 spectrums."""
    spectrums = generate_spectrums("epistemology")
    assert len(spectrums) == 18


def test_spectrum_endpoints_are_edge_classified():
    """Both endpoints of every spectrum must be edge-classified."""
    spectrums = generate_spectrums("ontology")
    for _sid, a_id, b_id in spectrums:
        # Parse coordinates from IDs like "ontology.3_0"
        ax, ay = map(int, a_id.split(".")[1].split("_"))
        bx, by = map(int, b_id.split(".")[1].split("_"))
        assert is_edge_point(ax, ay), f"{a_id} is not edge-classified"
        assert is_edge_point(bx, by), f"{b_id} is not edge-classified"


def test_spectrum_endpoints_are_reflections():
    """Each pair should be center-reflections: (x,y) ↔ (9-x, 9-y)."""
    spectrums = generate_spectrums("methodology")
    for _sid, a_id, b_id in spectrums:
        ax, ay = map(int, a_id.split(".")[1].split("_"))
        bx, by = map(int, b_id.split(".")[1].split("_"))
        assert (ax + bx == 9) and (ay + by == 9), f"{a_id} ↔ {b_id} not reflections"


def test_spectrum_no_duplicates():
    spectrums = generate_spectrums("heuristics")
    pairs = set()
    for _sid, a_id, b_id in spectrums:
        pair = tuple(sorted([a_id, b_id]))
        assert pair not in pairs, f"Duplicate spectrum: {pair}"
        pairs.add(pair)


def test_is_edge_point():
    assert is_edge_point(0, 0) is True  # corner
    assert is_edge_point(4, 0) is True  # midpoint
    assert is_edge_point(3, 0) is True  # edge
    assert is_edge_point(5, 5) is False  # center


def test_total_edge_points():
    """36 edge points per plane (corners + midpoints + remaining edge)."""
    count = sum(1 for x in range(10) for y in range(10) if is_edge_point(x, y))
    assert count == 36
