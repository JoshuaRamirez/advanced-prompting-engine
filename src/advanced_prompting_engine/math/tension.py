"""Potency-weighted tension computation — direct, spectrum, and cascading.

Authoritative source: Spec 05 §6.
"""

from __future__ import annotations

from collections import deque

import networkx as nx
import numpy as np

from advanced_prompting_engine.graph.schema import REQUIRES, SPECTRUM_OPPOSITION, TENSIONS_WITH


def compute_decay_factor(G: nx.Graph) -> float:
    """Derive cascade decay from mean REQUIRES edge strength. Default 0.7."""
    strengths = [
        d.get("strength", 0.5)
        for _, _, d in G.edges(data=True)
        if d.get("relation") == REQUIRES
    ]
    if not strengths:
        return 0.7
    return float(np.mean(strengths))


def compute_tensions(active_constructs: dict, G: nx.Graph) -> dict:
    """Compute all tensions: direct, spectrum, and cascading.

    active_constructs: branch → list of dicts with at minimum {branch, x, y, potency, id}.
    Returns dict with total_magnitude, direct[], spectrum[], cascading[], resolution_paths[].
    """
    all_active = []
    for branch, constructs in active_constructs.items():
        for c in constructs:
            all_active.append(c)

    active_ids = {c["id"] for c in all_active}

    direct = []
    spectrum = []
    cascading = []
    resolution_paths = []

    # Direct tensions
    for i, a in enumerate(all_active):
        for b in all_active[i + 1 :]:
            a_id = a["id"]
            b_id = b["id"]
            for u, v in [(a_id, b_id), (b_id, a_id)]:
                if G.has_edge(u, v) and G.edges[u, v].get("relation") == TENSIONS_WITH:
                    strength = G.edges[u, v].get("strength", 0.5)
                    mag = strength * a["potency"] * b["potency"]
                    direct.append({
                        "between": [a_id, b_id],
                        "magnitude": mag,
                        "type": "declared",
                        "potency_product": a["potency"] * b["potency"],
                    })
                    # Check for resolution
                    _collect_resolutions(a_id, b_id, G, resolution_paths)
                    break  # only count once per pair

    # Spectrum oppositions (deduplicate — symmetric edges are stored both directions)
    seen_spectrum_pairs: set[frozenset] = set()
    for c in all_active:
        c_id = c["id"]
        if c.get("classification") in ("corner", "midpoint", "edge"):
            for _, neighbor, data in G.edges(c_id, data=True):
                if data.get("relation") == SPECTRUM_OPPOSITION:
                    pair = frozenset([c_id, neighbor])
                    if pair in seen_spectrum_pairs:
                        continue
                    seen_spectrum_pairs.add(pair)
                    opp_potency = G.nodes[neighbor].get("potency", 0.6)
                    mag = 0.6 * c["potency"] * opp_potency
                    spectrum.append({
                        "active": c_id,
                        "opposite": neighbor,
                        "magnitude": mag,
                        "type": "spectrum_geometric",
                        "spectrum_question": data.get("question"),
                    })

    # Cascading tensions
    decay = compute_decay_factor(G)
    for c in all_active:
        cascade_results = _propagate_tension(c["id"], active_ids, G, decay, max_hops=5)
        cascading.extend(cascade_results)

    total = (
        sum(t["magnitude"] for t in direct)
        + sum(t["magnitude"] for t in spectrum)
        + sum(t["magnitude"] for t in cascading)
    )

    return {
        "total_magnitude": total,
        "direct": direct,
        "spectrum": spectrum,
        "cascading": cascading,
        "resolution_paths": resolution_paths,
    }


def _propagate_tension(
    source_id: str, active_ids: set[str], G: nx.Graph, decay: float, max_hops: int
) -> list[dict]:
    """Follow REQUIRES chains from source, check for tensions at each hop."""
    results = []
    visited = {source_id}
    frontier = deque([(source_id, 0)])

    while frontier:
        current, hops = frontier.popleft()
        if hops >= max_hops:
            continue
        for _, neighbor, data in G.edges(current, data=True):
            if data.get("relation") != REQUIRES or neighbor in visited:
                continue
            visited.add(neighbor)
            # Check if this required node tensions with any active node
            for _, tension_target, td in G.edges(neighbor, data=True):
                if td.get("relation") == TENSIONS_WITH and tension_target in active_ids:
                    mag = td.get("strength", 0.5) * (decay ** (hops + 1))
                    if mag >= 0.05:  # negligible threshold
                        results.append({
                            "between": [source_id, tension_target],
                            "magnitude": mag,
                            "type": "inferred_cascade",
                            "chain": [source_id, current, neighbor, tension_target],
                        })
            frontier.append((neighbor, hops + 1))

    return results


def _collect_resolutions(a_id: str, b_id: str, G: nx.Graph, resolution_paths: list):
    """Check if any construct resolves the tension between a and b."""
    from advanced_prompting_engine.graph.schema import RESOLVES

    for node in G.nodes():
        resolves_a = G.has_edge(node, a_id) and G.edges[node, a_id].get("relation") == RESOLVES
        resolves_b = G.has_edge(node, b_id) and G.edges[node, b_id].get("relation") == RESOLVES
        if resolves_a and resolves_b:
            resolution_paths.append({
                "resolver": node,
                "tension_between": [a_id, b_id],
            })
