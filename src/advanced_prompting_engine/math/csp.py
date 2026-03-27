"""Constraint satisfaction for coordinate resolution.

Authoritative source: Spec 05 §5.
"""

from __future__ import annotations

import networkx as nx

from advanced_prompting_engine.graph.grid import potency
from advanced_prompting_engine.graph.schema import COMPATIBLE_WITH, EXCLUDES, REQUIRES


def resolve_coordinate(partial_coord: dict, G: nx.Graph) -> dict:
    """Fill null axes via constraint satisfaction.

    Input: branch → Optional[{x, y, weight}] (some axes may be None).
    Output: branch → {x, y, weight} (all 10 axes filled).
    """
    specified = {b: v for b, v in partial_coord.items() if v is not None}
    specified_ids = [f"{b}.{v['x']}_{v['y']}" for b, v in specified.items()]
    unspecified = [b for b, v in partial_coord.items() if v is None]

    result = dict(specified)

    for branch in unspecified:
        candidates = []
        for x in range(10):
            for y in range(10):
                cid = f"{branch}.{x}_{y}"
                if cid not in G.nodes:
                    continue

                # Check EXCLUDES
                excluded = False
                for sid in specified_ids:
                    if G.has_edge(cid, sid) and G.edges[cid, sid].get("relation") == EXCLUDES:
                        excluded = True
                        break
                    if G.has_edge(sid, cid) and G.edges[sid, cid].get("relation") == EXCLUDES:
                        excluded = True
                        break
                if excluded:
                    continue

                # Score: COMPATIBLE_WITH count × 1.0 + REQUIRES count × 2.0 + potency × 0.5
                compat_count = 0
                requires_count = 0
                for sid in specified_ids:
                    if G.has_edge(cid, sid) and G.edges[cid, sid].get("relation") == COMPATIBLE_WITH:
                        compat_count += 1
                    if G.has_edge(sid, cid) and G.edges[sid, cid].get("relation") == COMPATIBLE_WITH:
                        compat_count += 1
                    if G.has_edge(sid, cid) and G.edges[sid, cid].get("relation") == REQUIRES:
                        requires_count += 1

                p = potency(x, y)
                score = compat_count * 1.0 + requires_count * 2.0 + p * 0.5
                candidates.append((x, y, score, p))

        if not candidates:
            # Fallback to center position
            candidates = [(5, 5, 0.0, potency(5, 5))]

        # Sort by score descending, tiebreak by potency descending
        candidates.sort(key=lambda c: (c[2], c[3]), reverse=True)
        best_x, best_y, best_score, _ = candidates[0]

        # Auto-fill weight: base 0.15, ceiling 0.4, scaled by pull ratio
        max_score = max(c[2] for c in candidates) if candidates else 1.0
        pull_ratio = best_score / max(max_score, 1e-10)
        weight = 0.15 + (0.4 - 0.15) * pull_ratio

        result[branch] = {"x": best_x, "y": best_y, "weight": weight}
        specified_ids.append(f"{branch}.{best_x}_{best_y}")

    return result
