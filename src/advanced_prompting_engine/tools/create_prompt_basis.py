"""MCP Tool: create_prompt_basis — primary entry point.

Authoritative source: Spec 10.
Accepts natural language intent or pre-formed coordinate.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from advanced_prompting_engine.pipeline.runner import PipelineRunner


def handle_create_prompt_basis(
    pipeline: "PipelineRunner",
    intent: str | None = None,
    coordinate: dict | None = None,
    compact: bool = False,
) -> dict:
    """Execute the pipeline and return the construction basis."""
    if intent and coordinate:
        return {"status": "error", "message": "Provide intent OR coordinate, not both"}
    if not intent and not coordinate:
        return {"status": "error", "message": "Provide either intent or coordinate"}

    raw_input = coordinate if coordinate else intent
    try:
        result = pipeline.run(raw_input)
        if compact:
            result = _compact(result)
        return {"status": "success", "construction_basis": result}
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"Pipeline error: {e}"}


def _compact(basis: dict) -> dict:
    """Filter construction basis to essential fields only (~2KB vs ~52KB)."""
    return {
        "coordinate": {
            b: {"x": v["x"], "y": v["y"], "weight": v["weight"]}
            for b, v in basis.get("coordinate", {}).items()
        },
        "structural_profile": basis.get("structural_profile"),
        "tensions_summary": {
            "total": basis.get("tensions", {}).get("total_magnitude", 0),
            "direct_count": len(basis.get("tensions", {}).get("direct", [])),
            "spectrum_count": len(basis.get("tensions", {}).get("spectrum", [])),
        },
        "spokes": {
            b: {"classification": s.get("classification"), "strength": s.get("strength", 0)}
            for b, s in basis.get("spokes", {}).items()
        },
        "central_gem": basis.get("central_gem"),
        "construction_questions": {
            b: {
                "template": cq.get("template"),
                "position_summary": cq.get("position_summary"),
                "classification": cq.get("classification"),
                "potency": cq.get("potency"),
                "spoke_profile": cq.get("spoke_profile"),
            }
            for b, cq in basis.get("construction_questions", {}).items()
        },
    }
