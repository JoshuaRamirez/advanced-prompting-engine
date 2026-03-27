"""Tests for tension computation."""

import networkx as nx
from advanced_prompting_engine.math.tension import compute_tensions, compute_decay_factor


def test_no_tensions():
    G = nx.DiGraph()
    G.add_node("a.0_0", potency=1.0)
    active = {"a": [{"id": "a.0_0", "potency": 1.0, "classification": "corner", "branch": "a"}]}
    result = compute_tensions(active, G)
    assert result["total_magnitude"] == 0.0
    assert result["direct"] == []
    assert result["spectrum"] == []
    assert result["cascading"] == []


def test_direct_tension():
    G = nx.DiGraph()
    G.add_node("a.0_0", potency=1.0)
    G.add_node("b.9_9", potency=1.0)
    G.add_edge("a.0_0", "b.9_9", relation="TENSIONS_WITH", strength=0.5)
    active = {
        "a": [{"id": "a.0_0", "potency": 1.0, "classification": "corner", "branch": "a"}],
        "b": [{"id": "b.9_9", "potency": 1.0, "classification": "corner", "branch": "b"}],
    }
    result = compute_tensions(active, G)
    assert len(result["direct"]) == 1
    assert result["direct"][0]["magnitude"] == 0.5  # 0.5 * 1.0 * 1.0


def test_potency_weighting():
    G = nx.DiGraph()
    G.add_node("a.1_1", potency=0.6)
    G.add_node("b.2_2", potency=0.6)
    G.add_edge("a.1_1", "b.2_2", relation="TENSIONS_WITH", strength=1.0)
    active = {
        "a": [{"id": "a.1_1", "potency": 0.6, "classification": "center", "branch": "a"}],
        "b": [{"id": "b.2_2", "potency": 0.6, "classification": "center", "branch": "b"}],
    }
    result = compute_tensions(active, G)
    assert abs(result["direct"][0]["magnitude"] - 0.36) < 1e-6  # 1.0 * 0.6 * 0.6


def test_decay_factor_default():
    G = nx.DiGraph()
    assert compute_decay_factor(G) == 0.7
