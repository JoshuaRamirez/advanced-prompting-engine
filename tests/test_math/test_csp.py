"""Tests for constraint satisfaction coordinate resolver."""

import networkx as nx
from advanced_prompting_engine.math.csp import resolve_coordinate
from advanced_prompting_engine.graph.schema import ALL_BRANCHES


def _make_minimal_graph():
    """Graph with 100 constructs for one branch."""
    G = nx.DiGraph()
    for x in range(10):
        for y in range(10):
            G.add_node(f"ontology.{x}_{y}", branch="ontology", type="construct",
                       classification="center", potency=0.6)
    return G


def test_fully_specified_passthrough():
    G = _make_minimal_graph()
    coord = {b: {"x": 5, "y": 5, "weight": 0.5} for b in ALL_BRANCHES}
    result = resolve_coordinate(coord, G)
    for b in ALL_BRANCHES:
        assert result[b]["x"] == 5
        assert result[b]["y"] == 5


def test_all_empty_fallback():
    G = _make_minimal_graph()
    coord = {b: None for b in ALL_BRANCHES}
    result = resolve_coordinate(coord, G)
    # All unspecified branches should get a position
    for b in ALL_BRANCHES:
        assert result[b] is not None
        assert 0 <= result[b]["x"] <= 9
        assert 0 <= result[b]["y"] <= 9
        assert 0.15 <= result[b]["weight"] <= 0.4


def test_single_branch_specified():
    G = _make_minimal_graph()
    coord = {b: None for b in ALL_BRANCHES}
    coord["ontology"] = {"x": 0, "y": 0, "weight": 1.0}
    result = resolve_coordinate(coord, G)
    assert result["ontology"]["x"] == 0
    assert result["ontology"]["y"] == 0
