"""MCP Tool: create_prompt_basis — primary entry point.

Authoritative source: Spec 10.
Accepts natural language intent or pre-formed coordinate.
Supports compact (summary fields) and focused (guidance-centric) output modes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from advanced_prompting_engine.graph.schema import ALL_FACES

if TYPE_CHECKING:
    from advanced_prompting_engine.pipeline.runner import PipelineRunner


def handle_create_prompt_basis(
    pipeline: "PipelineRunner",
    intent: str | None = None,
    coordinate: dict | None = None,
    compact: bool = False,
    focused: bool = False,
) -> dict:
    """Execute the pipeline and return the construction basis."""
    if intent and coordinate:
        return {"status": "error", "message": "Provide intent OR coordinate, not both"}
    if not intent and not coordinate:
        return {"status": "error", "message": "Provide either intent or coordinate"}

    raw_input = coordinate if coordinate else intent
    try:
        result = pipeline.run(raw_input)
        if focused:
            result = _focused(result)
        elif compact:
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
            b: {
                "x": v["x"],
                "y": v["y"],
                "weight": v["weight"],
                "control_type": v.get("control_type"),
            }
            for b, v in basis.get("coordinate", {}).items()
        },
        "control_type_composition": basis.get("control_type_composition"),
        "structural_profile": basis.get("structural_profile"),
        "tensions_summary": {
            "total": basis.get("tensions", {}).get("total_magnitude", 0),
            "positional_count": len(basis.get("tensions", {}).get("positional", [])),
            "spectrum_count": len(basis.get("tensions", {}).get("spectrum", [])),
        },
        "harmonization": [
            {
                "pair": h["pair"],
                "resonance": h["resonance"],
                "directional_resonance": h.get("directional_resonance", 0.0),
                "grounding_face": h.get("grounding_face"),
                "grounded_face": h.get("grounded_face"),
            }
            for h in basis.get("harmonization_pairs", [])
        ],
        "spokes": {
            b: {"classification": s.get("classification"), "strength": s.get("strength", 0)}
            for b, s in basis.get("spokes", {}).items()
        },
        "central_gem": basis.get("central_gem"),
        "precedence_flags": basis.get("precedence_flags", []),
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


def _focused(basis: dict) -> dict:
    """Guidance-centric output: only what a prompt engineer needs (~500 bytes).

    Returns the guidance synthesis, top 5 faces with position data,
    gap statements, strongest resonance, and coherence score.
    """
    guidance = basis.get("guidance", {})
    coordinate = basis.get("coordinate", {})
    construction_questions = basis.get("construction_questions", {})

    # Top 5 faces by weight
    face_weights = [
        (face, coordinate.get(face, {}).get("weight", 0.0))
        for face in ALL_FACES
    ]
    face_weights.sort(key=lambda fw: fw[1], reverse=True)
    top_faces = []
    for face, weight in face_weights[:5]:
        cq = construction_questions.get(face, {})
        top_faces.append({
            "face": face,
            "weight": round(weight, 2),
            "position_summary": cq.get("position_summary"),
            "construction_question": cq.get("template"),
        })

    return {
        "guidance": guidance,
        "top_faces": top_faces,
        "gaps": guidance.get("neglected_dimensions", []),
        "strongest_resonance": guidance.get("strongest_resonance", {}),
        "coherence": basis.get("central_gem", {}),
    }
