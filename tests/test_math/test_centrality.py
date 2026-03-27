"""Tests for centrality measures."""

import networkx as nx
from advanced_prompting_engine.math.centrality import compute_centralities


def test_star_graph():
    G = nx.star_graph(4)
    G = nx.relabel_nodes(G, {i: f"n{i}" for i in range(5)})
    c = compute_centralities(G)
    # Center node (n0) should have highest betweenness
    assert c["n0"]["betweenness"] > c["n1"]["betweenness"]


def test_isolated_node():
    G = nx.Graph()
    G.add_node("alone")
    c = compute_centralities(G)
    assert c["alone"]["betweenness"] == 0.0
    # PageRank (or degree centrality fallback) assigns a value to all nodes
    assert "pagerank" in c["alone"]
