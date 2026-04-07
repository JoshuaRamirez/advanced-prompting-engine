"""MCP Tool: extend_schema — authoring with contradiction detection.

Authoritative source: CONSTRUCT-v2.md, ADR-006.
2 operations: add_construct, add_relation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_prompting_engine.graph.mutation import ContradictionWarning

if TYPE_CHECKING:
    from advanced_prompting_engine.graph.mutation import GraphMutationLayer


def handle_extend_schema(
    mutation_layer: "GraphMutationLayer",
    operation: str,
    **kwargs,
) -> dict:
    """Route to add_construct or add_relation."""
    if operation == "add_construct":
        return _add_construct(mutation_layer, **kwargs)
    elif operation == "add_relation":
        return _add_relation(mutation_layer, **kwargs)
    else:
        return {"status": "error", "message": f"Unknown operation: {operation}"}


def _add_construct(mutation_layer, face=None,
                   branch=None,  # Deprecated: use 'face' instead (v1 backward compat)
                   x=None, y=None,
                   question=None, tags=None, description=None, **kwargs):
    f = face or branch  # accept either name
    if not all([f, question]) or x is None or y is None:
        return {"status": "error", "message": "face, x, y, and question are required"}
    try:
        result = mutation_layer.add_construct(
            face=f,
            x=int(x),
            y=int(y),
            question=question,
            tags=tags or [],
            description=description or "",
        )
        return result
    except ValueError as e:
        return {"status": "error", "message": str(e)}


def _add_relation(mutation_layer, source_id=None, target_id=None,
                  relation_type=None, strength=0.5, override_reason=None, **kwargs):
    if not all([source_id, target_id, relation_type]):
        return {"status": "error", "message": "source_id, target_id, and relation_type are required"}
    try:
        result = mutation_layer.add_relation(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            strength=float(strength),
            override_reason=override_reason,
        )
        if isinstance(result, ContradictionWarning):
            return result.to_dict()
        return result
    except ValueError as e:
        return {"status": "error", "message": str(e)}
