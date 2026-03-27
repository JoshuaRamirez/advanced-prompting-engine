"""Community detection — Louvain wrapper.

Authoritative source: Spec 05 §7.
"""

from __future__ import annotations

import networkx as nx


def detect_communities(subgraph: nx.Graph) -> list[set[str]]:
    """Run Louvain community detection on a subgraph.

    Returns list of sets, each a community of node IDs.
    """
    if len(subgraph.nodes()) < 2:
        return [set(subgraph.nodes())]
    try:
        return list(nx.community.louvain_communities(subgraph, seed=42))
    except Exception:
        return [set(subgraph.nodes())]
