"""MCP Tool: interpret_basis — convenience interpreter for construction basis output.

Takes the JSON output from create_prompt_basis and returns the guidance
section formatted as readable text. The guidance is already present in the
basis; this tool makes it accessible without parsing the full output.
"""

from __future__ import annotations

import json


def handle_interpret_basis(basis_json: str) -> dict:
    """Parse a construction basis JSON string and return formatted guidance.

    Accepts the full JSON output from create_prompt_basis (including the
    wrapper with status/construction_basis keys) or just the inner basis dict.
    """
    try:
        data = json.loads(basis_json)
    except (json.JSONDecodeError, TypeError):
        return {"status": "error", "message": "Invalid JSON"}

    # Unwrap if wrapped in the standard response envelope
    if "construction_basis" in data:
        data = data["construction_basis"]

    guidance = data.get("guidance")
    if not guidance:
        return {
            "status": "error",
            "message": "No guidance section found. Run create_prompt_basis first.",
        }

    lines = []
    lines.append(f"## Summary\n{guidance['summary']}\n")

    lines.append("## Dominant Dimensions")
    for d in guidance.get("dominant_dimensions", []):
        lines.append(f"- **{d['face'].title()}** (weight {d['weight']:.2f}): {d['question']}")
        if d.get("position"):
            lines.append(f"  Position: {d['position']}")

    lines.append("\n## Gaps")
    neglected = guidance.get("neglected_dimensions", [])
    if neglected:
        for g in neglected:
            lines.append(f"- **{g['face'].title()}** (weight {g['weight']:.2f}): {g['gap']}")
    else:
        lines.append("- No significant gaps detected.")

    res = guidance.get("strongest_resonance", {})
    if res and res.get("pair"):
        lines.append("\n## Strongest Resonance")
        lines.append(
            f"{res['pair'][0].title()} \u2194 {res['pair'][1].title()}"
            f" ({res['concern']}): {res['resonance']:.2f}"
        )

    return {"status": "success", "interpretation": "\n".join(lines)}
