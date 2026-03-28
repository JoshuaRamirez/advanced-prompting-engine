"""MCP Tool: explore_space — expert access to the graph.

Authoritative source: Spec 10.
8 operations routing to GraphQueryLayer or MultiPassOrchestrator.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_prompting_engine.orchestrator import multi_pass

if TYPE_CHECKING:
    from advanced_prompting_engine.graph.query import GraphQueryLayer
    from advanced_prompting_engine.pipeline.runner import PipelineRunner


def handle_explore_space(
    query_layer: "GraphQueryLayer",
    pipeline: "PipelineRunner",
    operation: str,
    **kwargs,
) -> dict:
    """Route to the appropriate operation."""
    handlers = {
        "list_branches": _list_branches,
        "list_constructs": _list_constructs,
        "get_construct": _get_construct,
        "get_neighborhood": _get_neighborhood,
        "find_path": _find_path,
        "get_spoke": _get_spoke,
        "stress_test": _stress_test,
        "triangulate": _triangulate,
    }

    handler = handlers.get(operation)
    if handler is None:
        return {"status": "error", "message": f"Unknown operation: {operation}"}

    try:
        return handler(query_layer, pipeline, **kwargs)
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _list_branches(query_layer, pipeline, **kwargs):
    branches = query_layer.list_branches()
    return {"status": "success", "branches": branches}


def _list_constructs(query_layer, pipeline, branch=None, classification=None,
                     provenance="merged", **kwargs):
    if not branch:
        return {"status": "error", "message": "branch is required"}
    constructs = query_layer.list_constructs(branch, provenance=provenance,
                                              classification=classification)
    return {"status": "success", "count": len(constructs), "constructs": constructs}


def _get_construct(query_layer, pipeline, branch=None, x=None, y=None, **kwargs):
    if not branch or x is None or y is None:
        return {"status": "error", "message": "branch, x, and y are required"}
    c = query_layer.get_construct(branch, int(x), int(y))
    if c is None:
        return {"status": "error", "message": f"Construct not found: {branch}.{x}_{y}"}
    return {"status": "success", "construct": c}


def _get_neighborhood(query_layer, pipeline, branch=None, x=None, y=None, **kwargs):
    if not branch or x is None or y is None:
        return {"status": "error", "message": "branch, x, and y are required"}
    construct_id = f"{branch}.{x}_{y}"
    edges = query_layer.get_edges(construct_id)
    opp = query_layer.get_spectrum_opposite(branch, int(x), int(y))
    return {
        "status": "success",
        "construct_id": construct_id,
        "edges": edges,
        "spectrum_opposite": opp,
    }


def _find_path(query_layer, pipeline, branch=None, x=None, y=None,
               target_branch=None, target_x=None, target_y=None, **kwargs):
    if not all([branch, target_branch]) or any(v is None for v in [x, y, target_x, target_y]):
        return {"status": "error", "message": "source and target branch/x/y required"}
    source = f"{branch}.{x}_{y}"
    target = f"{target_branch}.{target_x}_{target_y}"
    path = query_layer.find_path(source, target)
    return {"status": "success", "path": path}


def _get_spoke(query_layer, pipeline, branch=None, **kwargs):
    if not branch:
        return {"status": "error", "message": "branch is required"}
    spoke = query_layer.get_spoke(branch)
    return {"status": "success", "spoke": spoke}


def _stress_test(query_layer, pipeline, coordinate=None, **kwargs):
    if not coordinate:
        return {"status": "error", "message": "coordinate is required for stress_test"}
    result = multi_pass.stress_test(coordinate, pipeline)
    return {"status": "success", **result}


def _triangulate(query_layer, pipeline, coordinate_a=None, coordinate_b=None, **kwargs):
    if not coordinate_a or not coordinate_b:
        return {"status": "error", "message": "coordinate_a and coordinate_b required"}
    G = query_layer.graph
    result = multi_pass.triangulate(coordinate_a, coordinate_b, pipeline, G)
    return {"status": "success", **result}
