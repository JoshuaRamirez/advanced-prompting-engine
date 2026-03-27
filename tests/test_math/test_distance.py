"""Tests for graph distance metrics."""

import networkx as nx
from advanced_prompting_engine.math.distance import graph_distance, coordinate_distance


def _make_simple_graph():
    G = nx.DiGraph()
    G.add_edge("a", "b", relation="COMPATIBLE_WITH", weight=0.2)
    G.add_edge("b", "c", relation="TENSIONS_WITH", weight=0.8)
    return G


def test_same_node():
    G = _make_simple_graph()
    assert graph_distance(G, "a", "a") == 0.0


def test_no_path():
    G = nx.DiGraph()
    G.add_node("a")
    G.add_node("b")
    assert graph_distance(G, "a", "b") == float("inf")


def test_weighted_path():
    G = _make_simple_graph()
    d = graph_distance(G, "a", "b")
    assert d == 0.2  # COMPATIBLE_WITH weight


def test_missing_node():
    G = _make_simple_graph()
    assert graph_distance(G, "a", "zzz") == float("inf")


def test_coordinate_distance_basic():
    G = nx.DiGraph()
    G.add_node("branch.0_0")
    G.add_node("branch.1_1")
    G.add_edge("branch.0_0", "branch.1_1", relation="COMPATIBLE_WITH")
    coord_a = {"branch": {"x": 0, "y": 0, "weight": 1.0}}
    coord_b = {"branch": {"x": 1, "y": 1, "weight": 1.0}}
    d = coordinate_distance(coord_a, coord_b, G)
    assert d < float("inf")
