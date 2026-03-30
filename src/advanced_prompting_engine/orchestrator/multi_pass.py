"""Multi-pass orchestration — stress_test, triangulate, deepen.

Authoritative source: Spec 11.
These invoke the pipeline multiple times and compare results.
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from advanced_prompting_engine.graph.schema import ALL_BRANCHES
from advanced_prompting_engine.math.distance import coordinate_distance

if TYPE_CHECKING:
    from advanced_prompting_engine.pipeline.runner import PipelineRunner


# All 8 neighbor directions for stress_test
_DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1)]


def stress_test(coordinate: dict, pipeline: "PipelineRunner") -> dict:
    """Perturb each axis to neighboring positions. Compare against baseline.

    Returns baseline + breakpoints + improvements.
    ~80 perturbations × ~150ms each = ~12 seconds.
    """
    baseline = pipeline.run(coordinate)
    baseline_tension = baseline["tensions"]["total_magnitude"]
    baseline_coherence = baseline["central_gem"]["coherence"]

    perturbations = []
    for branch in coordinate:
        bx = coordinate[branch]["x"]
        by = coordinate[branch]["y"]
        for dx, dy in _DIRECTIONS:
            nx_, ny = bx + dx, by + dy
            if 0 <= nx_ <= 9 and 0 <= ny <= 9 and (nx_, ny) != (bx, by):
                modified = copy.deepcopy(coordinate)
                modified[branch] = {"x": nx_, "y": ny, "weight": coordinate[branch]["weight"]}
                perturbations.append({
                    "branch": branch,
                    "from": (bx, by),
                    "to": (nx_, ny),
                    "coordinate": modified,
                })

    results = []
    for p in perturbations:
        result = pipeline.run(p["coordinate"])
        tension_delta = result["tensions"]["total_magnitude"] - baseline_tension
        coherence_delta = result["central_gem"]["coherence"] - baseline_coherence
        results.append({
            "branch": p["branch"],
            "from": p["from"],
            "to": p["to"],
            "tension_delta": tension_delta,
            "coherence_delta": coherence_delta,
            "new_tension": result["tensions"]["total_magnitude"],
            "new_coherence": result["central_gem"]["coherence"],
        })

    breakpoints = [r for r in results if r["tension_delta"] > 0.1]
    improvements = [r for r in results if r["tension_delta"] < -0.1 or r["coherence_delta"] > 0.01]

    return {
        "baseline_tension": baseline_tension,
        "baseline_coherence": baseline_coherence,
        "perturbations_tested": len(results),
        "breakpoints": sorted(breakpoints, key=lambda r: r["tension_delta"], reverse=True),
        "improvements": sorted(improvements, key=lambda r: r["tension_delta"]),
        "all_results": results,
    }


def triangulate(
    coord_a: dict, coord_b: dict, pipeline: "PipelineRunner", G
) -> dict:
    """Run pipeline for two coordinates and compare results."""
    result_a = pipeline.run(coord_a)
    result_b = pipeline.run(coord_b)

    # Per-branch construct intersection
    intersection = {}
    for branch in ALL_BRANCHES:
        a_ids = {
            f"{c['position'][0]}_{c['position'][1]}"
            for c in result_a.get("active_constructs", {}).get(branch, [])
        }
        b_ids = {
            f"{c['position'][0]}_{c['position'][1]}"
            for c in result_b.get("active_constructs", {}).get(branch, [])
        }
        intersection[branch] = list(a_ids & b_ids)

    # Shared tensions
    a_tensions = {
        tuple(sorted(t["between"]))
        for t in result_a.get("tensions", {}).get("direct", [])
    }
    b_tensions = {
        tuple(sorted(t["between"]))
        for t in result_b.get("tensions", {}).get("direct", [])
    }
    shared_tensions = [list(t) for t in a_tensions & b_tensions]

    # Spoke comparison
    spoke_comparison = {}
    for branch in ALL_BRANCHES:
        sa = result_a.get("spokes", {}).get(branch, {})
        sb = result_b.get("spokes", {}).get(branch, {})
        spoke_comparison[branch] = {
            "a_classification": sa.get("classification", "unknown"),
            "b_classification": sb.get("classification", "unknown"),
            "strength_delta": sa.get("strength", 0) - sb.get("strength", 0),
            "consistency_delta": sa.get("consistency", 0) - sb.get("consistency", 0),
        }

    # Coordinate distance
    dist = coordinate_distance(coord_a, coord_b, G)

    return {
        "distance": dist,
        "intersection": intersection,
        "shared_tensions": shared_tensions,
        "spoke_comparison": spoke_comparison,
        "a_coherence": result_a.get("central_gem", {}).get("coherence", 0.0),
        "b_coherence": result_b.get("central_gem", {}).get("coherence", 0.0),
    }


def deepen(
    basis: dict, pipeline: "PipelineRunner", G, tfidf_cache, targets: list | None = None
) -> dict:
    """Recursive gem condensation — overlay, semantic similarity, no overwrite.

    Takes a completed construction basis, condenses top gems into center points
    of uninvolved branches, and runs the pipeline again.
    """
    if targets is None:
        targets = _auto_select_condensation_targets(basis, G, tfidf_cache)

    if not targets:
        return basis

    # Record condensation metadata (do NOT mutate the shared graph)
    condensation_metadata = []
    for target in targets:
        gem = target["gem"]
        condensation_metadata.append({
            "dest_id": f"{target['destination_branch']}.{target['dest_x']}_{target['dest_y']}",
            "source_nexus": gem["nexus"],
            "magnitude": gem["magnitude"],
            "source_planes": [gem["nexus"].split(".")[1], gem["nexus"].split(".")[2]],
            "generation": basis.get("depth", 0) + 1,
        })

    # Build coordinate targeting condensed positions
    new_coordinate = copy.deepcopy(basis["coordinate"])
    for target in targets:
        dest_branch = target["destination_branch"]
        new_coordinate[dest_branch] = {
            "x": target["dest_x"],
            "y": target["dest_y"],
            "weight": target["gem"]["magnitude"],
        }

    # Run pipeline with modified coordinate
    deeper_basis = pipeline.run(new_coordinate)
    deeper_basis["depth"] = basis.get("depth", 0) + 1
    deeper_basis["condensation_source"] = targets
    deeper_basis["condensation_metadata"] = condensation_metadata

    return deeper_basis


def _auto_select_condensation_targets(basis: dict, G, tfidf_cache) -> list:
    """Select top 3 gems and place them via semantic similarity."""
    gems = sorted(basis.get("gems", []), key=lambda g: g["magnitude"], reverse=True)
    targets = []
    used_branches = set()
    used_positions = set()

    for gem in gems[:3]:
        nexus_parts = gem["nexus"].split(".")
        if len(nexus_parts) < 3:
            continue
        source_branch = nexus_parts[1]
        target_branch = nexus_parts[2]

        for branch in ALL_BRANCHES:
            if branch in (source_branch, target_branch) or branch in used_branches:
                continue

            # Find the center point most semantically similar to nexus content
            nexus_id = gem["nexus"]
            nexus_content = G.nodes.get(nexus_id, {}).get("content", "") if nexus_id in G.nodes else ""

            best_pos = None
            best_sim = -1.0

            for node_id, data in G.nodes(data=True):
                if (data.get("branch") != branch
                        or data.get("classification") != "center"
                        or data.get("type") != "construct"):
                    continue
                pos_key = (data.get("x"), data.get("y"))
                if pos_key in used_positions:
                    continue
                sim = tfidf_cache.similarity(nexus_content, data.get("question", ""))
                if sim > best_sim:
                    best_sim = sim
                    best_pos = (data.get("x"), data.get("y"))

            if best_pos:
                targets.append({
                    "gem": gem,
                    "destination_branch": branch,
                    "dest_x": best_pos[0],
                    "dest_y": best_pos[1],
                    "semantic_similarity": best_sim,
                })
                used_branches.add(branch)
                used_positions.add(best_pos)
                break

    return targets
