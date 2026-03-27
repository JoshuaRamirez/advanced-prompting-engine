"""Tests for spectral embedding."""

import networkx as nx
import numpy as np
from advanced_prompting_engine.math.embedding import compute_spectral_embedding


def test_small_graph():
    G = nx.path_graph(5)
    G = nx.relabel_nodes(G, {i: f"n{i}" for i in range(5)})
    emb = compute_spectral_embedding(G, k=3)
    assert len(emb) == 5
    assert emb["n0"].shape == (3,)


def test_single_node():
    G = nx.Graph()
    G.add_node("a")
    emb = compute_spectral_embedding(G)
    assert len(emb) == 1
    assert emb["a"].shape == (0,)


def test_disconnected_components():
    G = nx.Graph()
    G.add_edge("a", "b")
    G.add_edge("c", "d")
    emb = compute_spectral_embedding(G, k=2)
    assert len(emb) == 4
    # Disconnected nodes should be distant in embedding space
    dist_within = np.linalg.norm(emb["a"] - emb["b"])
    dist_across = np.linalg.norm(emb["a"] - emb["c"])
    assert dist_across > dist_within


def test_dimensionality_capped():
    G = nx.complete_graph(4)
    G = nx.relabel_nodes(G, {i: f"n{i}" for i in range(4)})
    emb = compute_spectral_embedding(G, k=50)
    # k capped to n-1=3
    assert emb["n0"].shape == (3,)
