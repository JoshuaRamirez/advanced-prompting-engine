"""Foundation-precedence flags — detect incoherent philosophical stances.

Authoritative source: Section 5, Principle 3 of
`docs/cc_genui_20260420_200730_face_importance_ranking.html`.

A philosophical stance is incoherent when an evaluative face (ethics,
axiology, teleology) is strongly activated while its foundational faces
(ontology, epistemology) are near the floor. This module surfaces those
incoherent stances as explicit flags for the skill layer to consume.

Two check kinds are computed:

  1. foundation_missing — an evaluative face is dominant but neither
     ontology nor epistemology carries enough activation to ground it.
  2. triad_cascade — within the evaluative triad (teleology grounds
     ethics grounds axiology), a downstream member dominates while an
     upstream member is at floor.

Thresholds intentionally mirror the prompt-refiner skill's Low/High
calibration (0.2 / 0.55) for cross-layer consistency.
"""

from __future__ import annotations


FOUNDATION_FACES: frozenset[str] = frozenset({"ontology", "epistemology"})
EVALUATIVE_FACES: frozenset[str] = frozenset({"axiology", "ethics", "teleology"})

# Internal grounding order of the evaluative triad: teleology grounds
# ethics grounds axiology (classical philosophical lineage —
# purpose precedes duty precedes worth).
EVALUATIVE_TRIAD_ORDER: list[str] = ["teleology", "ethics", "axiology"]

LOW_THRESHOLD: float = 0.2
HIGH_THRESHOLD: float = 0.55


def compute_precedence_flags(coordinate: dict) -> list[dict]:
    """Flag incoherent-stance patterns.

    Args:
        coordinate: mapping of face name → dict containing "weight" in [0,1].

    Returns:
        List of flag dicts, each with a "type" discriminator and a
        natural-language "message" suitable for direct presentation.
        An empty list means no precedence concerns were detected.
    """
    if not coordinate:
        return []

    weights: dict[str, float] = {
        face: float(data.get("weight", 0.0)) for face, data in coordinate.items()
    }

    flags: list[dict] = []

    onto_w = weights.get("ontology", 0.0)
    epis_w = weights.get("epistemology", 0.0)

    # Check 1: foundation_missing
    for eval_face in sorted(EVALUATIVE_FACES):
        ev_w = weights.get(eval_face, 0.0)
        if ev_w >= HIGH_THRESHOLD and onto_w < LOW_THRESHOLD and epis_w < LOW_THRESHOLD:
            flags.append({
                "type": "foundation_missing",
                "face": eval_face,
                "activation": round(ev_w, 3),
                "foundations": {
                    "ontology": round(onto_w, 3),
                    "epistemology": round(epis_w, 3),
                },
                "message": (
                    f"{eval_face} dominates ({ev_w:.2f}) while both foundation "
                    f"faces are near the floor (ontology {onto_w:.2f}, "
                    f"epistemology {epis_w:.2f}). Evaluative stance without "
                    f"foundational commitments reads as incoherent."
                ),
            })

    # Check 2: triad_cascade — downstream face dominates while upstream is at floor
    # Grounding order: teleology -> ethics -> axiology
    tel_w = weights.get("teleology", 0.0)
    eth_w = weights.get("ethics", 0.0)
    axi_w = weights.get("axiology", 0.0)

    if axi_w >= HIGH_THRESHOLD and tel_w < LOW_THRESHOLD:
        flags.append({
            "type": "triad_cascade",
            "dominant": "axiology",
            "missing_upstream": "teleology",
            "activations": {
                "teleology": round(tel_w, 3),
                "ethics": round(eth_w, 3),
                "axiology": round(axi_w, 3),
            },
            "message": (
                f"axiology dominates ({axi_w:.2f}) while teleology is near "
                f"floor ({tel_w:.2f}). Worth-framing without purpose-grounding "
                f"is classically ungrounded (teleology → ethics → axiology)."
            ),
        })
    if eth_w >= HIGH_THRESHOLD and tel_w < LOW_THRESHOLD:
        flags.append({
            "type": "triad_cascade",
            "dominant": "ethics",
            "missing_upstream": "teleology",
            "activations": {
                "teleology": round(tel_w, 3),
                "ethics": round(eth_w, 3),
                "axiology": round(axi_w, 3),
            },
            "message": (
                f"ethics dominates ({eth_w:.2f}) while teleology is near "
                f"floor ({tel_w:.2f}). Duty-framing without purpose-grounding "
                f"is classically ungrounded (teleology → ethics → axiology)."
            ),
        })
    if axi_w >= HIGH_THRESHOLD and eth_w < LOW_THRESHOLD and tel_w >= LOW_THRESHOLD:
        flags.append({
            "type": "triad_cascade",
            "dominant": "axiology",
            "missing_upstream": "ethics",
            "activations": {
                "teleology": round(tel_w, 3),
                "ethics": round(eth_w, 3),
                "axiology": round(axi_w, 3),
            },
            "message": (
                f"axiology dominates ({axi_w:.2f}) while ethics is near "
                f"floor ({eth_w:.2f}). Worth without duty skips a step of "
                f"the classical triad (teleology → ethics → axiology)."
            ),
        })

    return flags
