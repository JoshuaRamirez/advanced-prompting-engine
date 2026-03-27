"""Tests for community detection."""

import networkx as nx
from advanced_prompting_engine.math.community import detect_communities


def test_single_node():
    G = nx.Graph()
    G.add_node("a")
    communities = detect_communities(G)
    assert len(communities) == 1
    assert "a" in communities[0]


def test_disconnected():
    G = nx.Graph()
    G.add_edge("a", "b")
    G.add_edge("c", "d")
    communities = detect_communities(G)
    assert len(communities) >= 2


def test_complete_graph():
    G = nx.complete_graph(5)
    G = nx.relabel_nodes(G, {i: f"n{i}" for i in range(5)})
    communities = detect_communities(G)
    # Complete graph likely one community
    total_nodes = sum(len(c) for c in communities)
    assert total_nodes == 5
