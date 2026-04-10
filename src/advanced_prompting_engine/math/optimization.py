"""Pareto front computation.

Authoritative source: Spec 05 §13.

NOTE: pareto_front is not called by any current pipeline stage. Retained as a
utility for future multi-pass orchestrator enhancements.
"""

from __future__ import annotations


def pareto_front(results: list[dict]) -> list[dict]:
    """Find Pareto-optimal results (minimize tension, maximize generative).

    Each result must have 'tension' and 'generative' keys.
    Returns non-dominated results.
    """
    if not results:
        return []

    front = []
    for r in results:
        dominated = False
        for other in results:
            if other is r:
                continue
            if (
                other["tension"] <= r["tension"]
                and other["generative"] >= r["generative"]
                and (other["tension"] < r["tension"] or other["generative"] > r["generative"])
            ):
                dominated = True
                break
        if not dominated:
            front.append(r)
    return front
