"""Centrality measures — betweenness and PageRank.

Authoritative source: Spec 05 §8.
"""

from __future__ import annotations

import networkx as nx


def compute_centralities(G: nx.Graph) -> dict[str, dict[str, float]]:
    """Compute betweenness centrality and PageRank for all nodes.

    PageRank falls back to degree centrality if scipy is not available (ADR-005).
    """
    betweenness = nx.betweenness_centrality(G)

    try:
        pagerank = nx.pagerank(G, alpha=0.85, max_iter=100)
    except (ImportError, ModuleNotFoundError):
        # scipy not available — use degree centrality as fallback
        pagerank = nx.degree_centrality(G)

    return {
        node: {
            "betweenness": betweenness.get(node, 0.0),
            "pagerank": pagerank.get(node, 0.0),
        }
        for node in G.nodes()
    }
