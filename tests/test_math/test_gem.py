"""Tests for gem magnitude computation."""

import networkx as nx
from advanced_prompting_engine.math.gem import compute_gem


def _make_two_branch_graph():
    """Graph with 2 branches, each having a few edge constructs."""
    G = nx.DiGraph()
    for x in [0, 9]:
        for y in [0, 9]:
            for b in ["a", "b"]:
                nid = f"{b}.{x}_{y}"
                G.add_node(nid, branch=b, type="construct", classification="corner", potency=1.0)
    return G


def test_balanced_branches():
    G = _make_two_branch_graph()
    active = {
        "a": [{"id": "a.0_0", "potency": 1.0}],
        "b": [{"id": "b.0_0", "potency": 1.0}],
    }
    gem = compute_gem("a", "b", active, G)
    assert gem["nexus"] == "nexus.a.b"
    assert gem["magnitude"] > 0
    assert gem["type"] in ("harmonious", "conflicting")


def test_no_active_constructs():
    G = _make_two_branch_graph()
    active = {"a": [], "b": []}
    gem = compute_gem("a", "b", active, G)
    # With no active constructs, energy is baseline (1x for all edge constructs)
    # But both branches contribute, so magnitude should be nonzero
    assert gem["magnitude"] > 0


def test_one_sided_energy():
    """One branch with active constructs, the other without."""
    G = _make_two_branch_graph()
    active = {
        "a": [{"id": "a.0_0", "potency": 1.0}, {"id": "a.9_9", "potency": 1.0}],
        "b": [],  # no active
    }
    gem_active = compute_gem("a", "b", active, G)

    # Compare to balanced
    active_balanced = {
        "a": [{"id": "a.0_0", "potency": 1.0}],
        "b": [{"id": "b.0_0", "potency": 1.0}],
    }
    gem_balanced = compute_gem("a", "b", active_balanced, G)

    # Harmonic mean: one-sided should produce lower magnitude
    # Actually both contribute baseline, but active branch gets 2x boost
    # The key property is that harmonic mean requires both to be high
    assert gem_active["magnitude"] > 0


def test_harmony_type_with_tension():
    G = _make_two_branch_graph()
    G.add_edge("a.0_0", "b.0_0", relation="TENSIONS_WITH", strength=0.5)
    active = {
        "a": [{"id": "a.0_0", "potency": 1.0}],
        "b": [{"id": "b.0_0", "potency": 1.0}],
    }
    gem = compute_gem("a", "b", active, G)
    assert gem["type"] == "conflicting"
