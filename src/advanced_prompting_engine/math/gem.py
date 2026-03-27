"""Gem magnitude computation — harmonic mean of edge energy ratios.

Authoritative source: Spec 05 §10, Spec 07.
Active edge constructs get 2x potency boost. Harmonic mean ensures both
branches must contribute for high magnitude.
"""

from __future__ import annotations

import networkx as nx

from advanced_prompting_engine.graph.schema import COMPATIBLE_WITH, TENSIONS_WITH


def compute_gem(
    source_branch: str,
    target_branch: str,
    active_constructs: dict,
    G: nx.Graph,
) -> dict:
    """Compute gem for one directional nexus.

    Returns dict with nexus, magnitude, type, source_energy, target_energy.
    """
    source_edge = _get_edge_constructs(G, source_branch)
    target_edge = _get_edge_constructs(G, target_branch)

    source_active_ids = {
        c["id"] for c in active_constructs.get(source_branch, [])
    }
    target_active_ids = {
        c["id"] for c in active_constructs.get(target_branch, [])
    }

    # Sum potencies: active edge constructs get 2x, inactive get 1x
    source_energy = sum(
        c["potency"] * (2.0 if c["id"] in source_active_ids else 1.0)
        for c in source_edge
    )
    target_energy = sum(
        c["potency"] * (2.0 if c["id"] in target_active_ids else 1.0)
        for c in target_edge
    )

    # Normalize by maximum possible (all at 2x)
    max_source = sum(c["potency"] * 2.0 for c in source_edge) if source_edge else 1.0
    max_target = sum(c["potency"] * 2.0 for c in target_edge) if target_edge else 1.0

    source_ratio = source_energy / max(max_source, 1e-10)
    target_ratio = target_energy / max(max_target, 1e-10)

    # Harmonic mean
    if source_ratio + target_ratio == 0:
        magnitude = 0.0
    else:
        magnitude = 2 * source_ratio * target_ratio / (source_ratio + target_ratio)

    # Determine harmony vs conflict
    tension_count = 0
    compat_count = 0
    for sc in active_constructs.get(source_branch, []):
        for tc in active_constructs.get(target_branch, []):
            s_id, t_id = sc["id"], tc["id"]
            for u, v in [(s_id, t_id), (t_id, s_id)]:
                if G.has_edge(u, v):
                    rel = G.edges[u, v].get("relation")
                    if rel == TENSIONS_WITH:
                        tension_count += 1
                    elif rel == COMPATIBLE_WITH:
                        compat_count += 1

    harmony_type = "harmonious" if compat_count >= tension_count else "conflicting"

    return {
        "nexus": f"nexus.{source_branch}.{target_branch}",
        "magnitude": magnitude,
        "type": harmony_type,
        "source_energy": source_ratio,
        "target_energy": target_ratio,
    }


def _get_edge_constructs(G: nx.Graph, branch: str) -> list[dict]:
    """Get all edge-classified constructs for a branch from the graph."""
    results = []
    for node, data in G.nodes(data=True):
        if (
            data.get("branch") == branch
            and data.get("type") == "construct"
            and data.get("classification") in ("corner", "midpoint", "edge")
        ):
            results.append({"id": node, "potency": data.get("potency", 0.8), **data})
    return results
