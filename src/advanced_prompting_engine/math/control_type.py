"""Control-type composition — structural vs bias share per prompt.

Authoritative source: Section 4 of
`docs/cc_genui_20260420_200730_face_importance_ranking.html`.

Each of the 12 faces is classified as:

  - **structural**: inhabitation produces testable, compositional output
    commitments (schemas, formats, procedures, entities).
  - **bias**: inhabitation produces distributional shifts in style/stance
    (moral framing, value framing, interpretive framing, aesthetic form).
  - **mixed**: can inhabit either mode depending on phrasing
    (epistemology, phenomenology, teleology).

For any measured prompt, computing weight-sums by control type exposes
whether the prompt leans on structural control (recommended for
engineering/extraction/schema tasks) or probabilistic bias (recommended
for creative/policy/persona tasks). This is the output-side dual of the
task-priority framework in the prompt-refiner skill.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import FACE_CONTROL_TYPE


def compute_control_type_composition(coordinate: dict) -> dict:
    """Aggregate activation weight by control type.

    Args:
        coordinate: mapping of face -> {weight: ...}.

    Returns:
        Dict with:
          - structural_weight, bias_weight, mixed_weight — raw sums
          - total_weight — sum of all 12 face weights
          - structural_share, bias_share, mixed_share — ratios in [0, 1]
            (zero-total → all zero shares)
          - dominant_control_type — "structural" | "bias" | "mixed" | "none"
    """
    if not coordinate:
        return {
            "structural_weight": 0.0,
            "bias_weight": 0.0,
            "mixed_weight": 0.0,
            "total_weight": 0.0,
            "structural_share": 0.0,
            "bias_share": 0.0,
            "mixed_share": 0.0,
            "dominant_control_type": "none",
        }

    by_type: dict[str, float] = {"structural": 0.0, "bias": 0.0, "mixed": 0.0}
    for face, data in coordinate.items():
        ctype = FACE_CONTROL_TYPE.get(face)
        if ctype is None:
            continue
        weight = float(data.get("weight", 0.0))
        by_type[ctype] += weight

    total = sum(by_type.values())

    if total <= 0.0:
        shares = {k: 0.0 for k in by_type}
        dominant = "none"
    else:
        shares = {k: v / total for k, v in by_type.items()}
        dominant = max(shares, key=shares.get)

    return {
        "structural_weight": round(by_type["structural"], 4),
        "bias_weight": round(by_type["bias"], 4),
        "mixed_weight": round(by_type["mixed"], 4),
        "total_weight": round(total, 4),
        "structural_share": round(shares["structural"], 4),
        "bias_share": round(shares["bias"], 4),
        "mixed_share": round(shares["mixed"], 4),
        "dominant_control_type": dominant,
    }


def annotate_coordinate(coordinate: dict) -> dict:
    """Return a copy of coordinate with per-face control_type added.

    Does not mutate the input.
    """
    annotated: dict = {}
    for face, data in coordinate.items():
        entry = dict(data)
        ctype = FACE_CONTROL_TYPE.get(face)
        if ctype is not None:
            entry["control_type"] = ctype
        annotated[face] = entry
    return annotated
