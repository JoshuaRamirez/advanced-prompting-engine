"""Stage 8 — Construction Bridge: assemble the full construction basis output.

Authoritative source: CONSTRUCT-v2.md (8-stage forward pass, Stage 8).
Combines all accumulated pipeline state into the final output dict.
Includes harmonization pairs for the 6 complementary cube pairs.
Generates a guidance synthesis section from assembled data.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.grid import degree_label
from advanced_prompting_engine.graph.schema import (
    ALL_FACES,
    CUBE_PAIRS,
    FACE_DEFINITIONS,
    FACE_PHASES,
    GENERATES,
    GRID_SIZE,
    PipelineState,
)

# §6 meaning hierarchy: classification → meaning mechanism
_MEANING_MECHANISMS: dict[str, str] = {
    "corner": "integration",
    "midpoint": "axial_balance",
    "edge": "demarcation",
    "center": "composition",
}

# Cube pair shared concern descriptions (CONSTRUCT-v2.md §4.3)
CUBE_PAIR_CONCERNS: dict[tuple[str, str], str] = {
    ("ontology", "praxeology"): "Being \u2194 Doing",
    ("epistemology", "methodology"): "Knowing \u2194 Proceeding",
    ("axiology", "ethics"): "Valuing \u2194 Judging",
    ("teleology", "heuristics"): "Purpose \u2194 Strategy",
    ("phenomenology", "aesthetics"): "Experiencing \u2194 Recognizing form",
    ("semiotics", "hermeneutics"): "Encoding \u2194 Decoding",
}


def _generate_guidance(
    coordinate: dict,
    spokes: dict,
    harmonization_pairs: list,
    construction_questions: dict,
) -> dict:
    """Synthesize actionable guidance from assembled pipeline data.

    Identifies dominant dimensions, neglected dimensions, strongest
    harmonization pair, and produces a natural-language summary.
    """
    # Sort faces by weight descending
    face_weights = []
    for face in ALL_FACES:
        weight = coordinate.get(face, {}).get("weight", 0.0)
        face_weights.append((face, weight))
    face_weights.sort(key=lambda fw: fw[1], reverse=True)

    # Dominant: weight > 0.5 or top 3, whichever yields more
    top_3 = face_weights[:3]
    above_threshold = [(f, w) for f, w in face_weights if w > 0.5]
    dominant = above_threshold if len(above_threshold) > len(top_3) else top_3

    # Neglected: bottom 2 with weight < 0.2
    neglected = [(f, w) for f, w in face_weights if w < 0.2]
    neglected = neglected[-2:] if len(neglected) > 2 else neglected

    # Build dominant dimension entries
    dominant_dimensions = []
    for face, weight in dominant:
        cq = construction_questions.get(face, {})
        dominant_dimensions.append({
            "face": face,
            "weight": round(weight, 2),
            "question": cq.get("template", FACE_DEFINITIONS[face]["construction_template"]),
            "position": cq.get("position_summary"),
        })

    # Build neglected dimension entries with gap statements
    neglected_dimensions = []
    for face, weight in neglected:
        core_q = FACE_DEFINITIONS[face]["core_question"]
        # Lower-case the first character for embedding in the gap sentence,
        # and strip trailing punctuation so it reads naturally as a clause
        core_q_lower = core_q[0].lower() + core_q[1:] if core_q else core_q
        core_q_lower = core_q_lower.rstrip("?. ")
        neglected_dimensions.append({
            "face": face,
            "weight": round(weight, 2),
            "gap": f"Your intent does not address {core_q_lower}.",
        })

    # Find strongest harmonization pair
    strongest_resonance = {}
    if harmonization_pairs:
        best = max(harmonization_pairs, key=lambda h: h.get("resonance", 0.0))
        pair_tuple = tuple(best.get("pair", []))
        concern = CUBE_PAIR_CONCERNS.get(pair_tuple, "")
        if not concern:
            # Try reversed order
            concern = CUBE_PAIR_CONCERNS.get(tuple(reversed(pair_tuple)), "")
        strongest_resonance = {
            "pair": list(best.get("pair", [])),
            "concern": concern,
            "resonance": round(best.get("resonance", 0.0), 2),
        }

    # Build summary sentence
    dominant_names = [d["face"] for d in dominant_dimensions]
    neglected_names = [n["face"] for n in neglected_dimensions]
    summary_parts = [
        f"This intent is primarily grounded in {', '.join(dominant_names)}."
    ]
    if neglected_names:
        summary_parts.append(
            f" It does not address {' or '.join(neglected_names)}"
            " \u2014 consider whether these omissions are intentional."
        )

    return {
        "dominant_dimensions": dominant_dimensions,
        "neglected_dimensions": neglected_dimensions,
        "strongest_resonance": strongest_resonance,
        "summary": "".join(summary_parts),
    }


class ConstructionBridge:
    """Stage 8: Assemble the final construction basis from all pipeline state."""

    def __init__(self, query_layer):
        self._query = query_layer

    def execute(self, state: PipelineState):
        active = state.active_constructs or {}
        tensions = state.tensions or {}
        spokes = state.spokes or {}
        central_gem = state.central_gem or {}
        gems = state.gems or []
        harmonization_pairs = state.harmonization_pairs or []
        G = self._query.graph

        # Spectrum opposites
        spectrum_opposites = []
        for face, constructs in active.items():
            if not constructs:
                continue
            primary = constructs[0]
            opp = self._query.get_spectrum_opposite(
                face, primary.get("x", 0), primary.get("y", 0)
            )
            if opp:
                spectrum_opposites.append({
                    "face": face,
                    "active": {
                        "position": [primary.get("x"), primary.get("y")],
                        "question": primary.get("question"),
                    },
                    "opposite": {
                        "position": [opp.get("x"), opp.get("y")],
                        "question": opp.get("question"),
                    },
                })

        # Structural profile
        edge_count = sum(
            1 for f, cs in active.items() for c in cs
            if c.get("classification") in ("corner", "midpoint", "edge")
        )
        center_count = sum(
            1 for f, cs in active.items() for c in cs
            if c.get("classification") == "center"
        )
        total = edge_count + center_count
        edge_ratio = edge_count / max(total, 1)
        mean_potency = (
            sum(c.get("potency", 0.6) for f, cs in active.items() for c in cs)
            / max(total, 1)
        )

        # Generative combinations
        generatives = []
        all_active_ids = [c["id"] for cs in active.values() for c in cs]
        for i, a_id in enumerate(all_active_ids):
            for b_id in all_active_ids[i + 1:]:
                for u, v in [(a_id, b_id), (b_id, a_id)]:
                    if G.has_edge(u, v) and G.edges[u, v].get("relation") == GENERATES:
                        generatives.append({
                            "constructs": [a_id, b_id],
                            "source": "declared",
                            "quality": G.edges[u, v].get("quality", ""),
                        })
                        break

        # Construction questions
        construction_questions = {}
        for face in ALL_FACES:
            defn = FACE_DEFINITIONS[face]
            constructs = active.get(face, [])
            primary = constructs[0] if constructs else None
            spoke = spokes.get(face, {})

            # Spectrum opposite for this face
            opp_question = None
            if primary:
                opp = self._query.get_spectrum_opposite(
                    face, primary.get("x", 0), primary.get("y", 0)
                )
                if opp:
                    opp_question = opp.get("question")

            # Tension note
            positional_tensions = tensions.get("positional", [])
            face_tensions = [
                t for t in positional_tensions
                if face in t.get("faces", [])
            ]
            tension_note = (
                f"{len(face_tensions)} positional tension(s) involving this face"
                if face_tensions else None
            )

            # Generative note
            face_gens = [
                g for g in generatives
                if any(c.split(".")[0] == face for c in g.get("constructs", []))
            ]
            generative_note = (
                f"{len(face_gens)} generative combination(s) involving this face"
                if face_gens else None
            )

            # Sub-dimensional interpretation (mechanically derived via degree_label)
            x_label = None
            y_label = None
            position_summary = None
            if primary:
                px = primary.get("x", 0)
                py = primary.get("y", 0)
                x_label = degree_label(px, defn["x_axis_low"], defn["x_axis_high"])
                y_label = degree_label(py, defn["y_axis_low"], defn["y_axis_high"])
                position_summary = f"{x_label} + {y_label}"

            # §6 meaning hierarchy: classification determines meaning mechanism
            classification = primary.get("classification") if primary else None
            meaning_mechanism = _MEANING_MECHANISMS.get(classification) if classification else None

            construction_questions[face] = {
                "template": defn["construction_template"],
                "active_question": primary.get("question") if primary else None,
                "opposite_question": opp_question,
                "phase": FACE_PHASES.get(face, "unknown"),
                "classification": classification,
                "potency": primary.get("potency") if primary else None,
                "x": primary.get("x") if primary else None,
                "y": primary.get("y") if primary else None,
                "x_axis": defn["x_axis_name"],
                "x_interpretation": x_label,
                "y_axis": defn["y_axis_name"],
                "y_interpretation": y_label,
                "position_summary": position_summary,
                "meaning_mechanism": meaning_mechanism,
                "spoke_profile": spoke.get("classification"),
                "spoke_strength": spoke.get("strength", 0.0),
                "tension_note": tension_note,
                "generative_note": generative_note,
            }

        state.construction_basis = {
            "coordinate": state.coordinate,
            "active_constructs": {
                f: [
                    {
                        "position": [c.get("x"), c.get("y")],
                        "classification": c.get("classification"),
                        "potency": c.get("potency"),
                        "question": c.get("question"),
                    }
                    for c in cs
                ]
                for f, cs in active.items()
            },
            "spectrum_opposites": spectrum_opposites,
            "structural_profile": {
                "edge_count": edge_count,
                "center_count": center_count,
                "edge_ratio": edge_ratio,
                "mean_potency": mean_potency,
            },
            "tensions": tensions,
            "generative_combinations": generatives,
            "gems": gems,
            "harmonization_pairs": harmonization_pairs,
            "spokes": {
                f: {
                    "strength": s.get("strength", 0.0),
                    "consistency": s.get("consistency", 0.0),
                    "polarity": s.get("polarity", 0.0),
                    "contribution": s.get("contribution", 0.0),
                    "classification": s.get("classification"),
                    "gems": s.get("gems", []),
                }
                for f, s in spokes.items()
            },
            "central_gem": central_gem,
            "construction_questions": construction_questions,
        }

        # Synthesis: generate actionable guidance from assembled data
        guidance = _generate_guidance(
            coordinate=state.coordinate,
            spokes=spokes,
            harmonization_pairs=harmonization_pairs,
            construction_questions=construction_questions,
        )
        state.construction_basis["guidance"] = guidance
