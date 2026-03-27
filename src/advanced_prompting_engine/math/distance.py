"""Graph distance metrics — weighted path and coordinate distance.

Authoritative source: Spec 05 §4.
"""

from __future__ import annotations

import networkx as nx

from advanced_prompting_engine.graph.schema import EDGE_WEIGHTS


def graph_distance(G: nx.Graph, source: str, target: str) -> float:
    """Compute weighted shortest path distance between two nodes."""

    def weight_fn(u, v, data):
        return EDGE_WEIGHTS.get(data.get("relation", ""), 1.0)

    try:
        return nx.shortest_path_length(G, source, target, weight=weight_fn)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return float("inf")


def coordinate_distance(coord_a: dict, coord_b: dict, G: nx.Graph) -> float:
    """Weighted sum of per-axis graph distances between two coordinates."""
    total = 0.0
    weight_sum = 0.0
    for branch in coord_a:
        if branch not in coord_b:
            continue
        a_id = f"{branch}.{coord_a[branch]['x']}_{coord_a[branch]['y']}"
        b_id = f"{branch}.{coord_b[branch]['x']}_{coord_b[branch]['y']}"
        w = (coord_a[branch]["weight"] + coord_b[branch]["weight"]) / 2
        d = graph_distance(G, a_id, b_id)
        if d < float("inf"):
            total += w * d
            weight_sum += w
    if weight_sum == 0:
        return float("inf")
    return total / weight_sum
