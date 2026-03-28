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
) -> dict:
    """Execute the pipeline and return the construction basis."""
    if intent and coordinate:
        return {"status": "error", "message": "Provide intent OR coordinate, not both"}
    if not intent and not coordinate:
        return {"status": "error", "message": "Provide either intent or coordinate"}

    raw_input = coordinate if coordinate else intent
    try:
        result = pipeline.run(raw_input)
        return {"status": "success", "construction_basis": result}
    except ValueError as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": f"Pipeline error: {e}"}
