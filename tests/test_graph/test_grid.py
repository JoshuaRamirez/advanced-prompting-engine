"""Tests for grid classification, potency, spectrum generation, and degree labeling (v2: 12x12)."""

import numpy as np

from advanced_prompting_engine.graph.grid import (
    classify,
    degree_label,
    generate_spectrums,
    is_edge_point,
    potency,
    potency_matrix,
)


def test_classification_counts():
    """Verify 4 corners, 8 midpoints, 32 edge, 100 center = 144 total."""
    counts = {"corner": 0, "midpoint": 0, "edge": 0, "center": 0}
    for x in range(12):
        for y in range(12):
            counts[classify(x, y)] += 1

    assert counts["corner"] == 4
    assert counts["midpoint"] == 8
    assert counts["edge"] == 32
    assert counts["center"] == 100
    assert sum(counts.values()) == 144


def test_corner_positions():
    assert classify(0, 0) == "corner"
    assert classify(11, 0) == "corner"
    assert classify(0, 11) == "corner"
    assert classify(11, 11) == "corner"


def test_midpoint_positions_dual_model():
    """8 midpoints: positions 5 and 6 on each edge."""
    # Top edge
    assert classify(5, 0) == "midpoint"
    assert classify(6, 0) == "midpoint"
    # Right edge
    assert classify(11, 5) == "midpoint"
    assert classify(11, 6) == "midpoint"
    # Bottom edge
    assert classify(5, 11) == "midpoint"
    assert classify(6, 11) == "midpoint"
    # Left edge
    assert classify(0, 5) == "midpoint"
    assert classify(0, 6) == "midpoint"


def test_edge_positions():
    """Non-corner, non-midpoint perimeter positions are 'edge'."""
    assert classify(1, 0) == "edge"
    assert classify(11, 1) == "edge"
    assert classify(10, 11) == "edge"
    assert classify(0, 10) == "edge"


def test_center_positions():
    assert classify(1, 1) == "center"
    assert classify(5, 5) == "center"
    assert classify(6, 6) == "center"
    assert classify(10, 10) == "center"


def test_potency_values():
    assert potency(0, 0) == 1.0    # corner
    assert potency(5, 0) == 0.9    # midpoint
    assert potency(1, 0) == 0.8    # edge
    assert potency(5, 5) == 0.6    # center


def test_potency_matrix_shape_and_values():
    """potency_matrix returns a 12x12 numpy array matching scalar potency()."""
    mat = potency_matrix()
    assert isinstance(mat, np.ndarray)
    assert mat.shape == (12, 12)
    for x in range(12):
        for y in range(12):
            assert mat[x, y] == potency(x, y), f"Mismatch at ({x}, {y})"


def test_spectrum_count_per_face():
    """Each face should produce exactly 22 spectrums."""
    spectrums = generate_spectrums("epistemology")
    assert len(spectrums) == 22


def test_spectrum_endpoints_are_edge_classified():
    """Both endpoints of every spectrum must be edge-classified."""
    spectrums = generate_spectrums("ontology")
    for _sid, a_id, b_id in spectrums:
        ax, ay = map(int, a_id.split(".")[1].split("_"))
        bx, by = map(int, b_id.split(".")[1].split("_"))
        assert is_edge_point(ax, ay), f"{a_id} is not edge-classified"
        assert is_edge_point(bx, by), f"{b_id} is not edge-classified"


def test_spectrum_endpoints_are_reflections():
    """Each pair should be center-reflections: (x,y) <-> (11-x, 11-y)."""
    spectrums = generate_spectrums("methodology")
    for _sid, a_id, b_id in spectrums:
        ax, ay = map(int, a_id.split(".")[1].split("_"))
        bx, by = map(int, b_id.split(".")[1].split("_"))
        assert (ax + bx == 11) and (ay + by == 11), f"{a_id} <-> {b_id} not reflections"


def test_spectrum_no_duplicates():
    spectrums = generate_spectrums("heuristics")
    pairs = set()
    for _sid, a_id, b_id in spectrums:
        pair = tuple(sorted([a_id, b_id]))
        assert pair not in pairs, f"Duplicate spectrum: {pair}"
        pairs.add(pair)


def test_is_edge_point():
    assert is_edge_point(0, 0) is True    # corner
    assert is_edge_point(5, 0) is True    # midpoint
    assert is_edge_point(3, 0) is True    # edge
    assert is_edge_point(5, 5) is False   # center


def test_total_edge_points():
    """44 edge points per plane (corners + midpoints + remaining edge)."""
    count = sum(1 for x in range(12) for y in range(12) if is_edge_point(x, y))
    assert count == 44


def test_degree_label_extremes():
    """Position 0 is fully low, position 11 is fully high."""
    assert degree_label(0, "Empirical", "Rational") == "fully Empirical"
    assert degree_label(11, "Empirical", "Rational") == "fully Rational"


def test_degree_label_ranges():
    """Each degree range maps to the correct qualitative label."""
    low, high = "Static", "Dynamic"
    assert "strongly Static" in degree_label(1, low, high)
    assert "strongly Static" in degree_label(2, low, high)
    assert "moderately Static" in degree_label(3, low, high)
    assert "moderately Static" in degree_label(4, low, high)
    assert "balanced between" in degree_label(5, low, high)
    assert "balanced between" in degree_label(6, low, high)
    assert "moderately Dynamic" in degree_label(7, low, high)
    assert "moderately Dynamic" in degree_label(8, low, high)
    assert "strongly Dynamic" in degree_label(9, low, high)
    assert "strongly Dynamic" in degree_label(10, low, high)
