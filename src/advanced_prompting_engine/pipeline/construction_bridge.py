"""Stage 8 — Construction Bridge: assemble the full construction basis output.

Authoritative source: Spec 06 §8.
Combines all accumulated pipeline state into the final output dict.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import (
    ALL_BRANCHES,
    BRANCH_DEFINITIONS,
    GENERATES,
    PipelineState,
)


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
        G = self._query.graph

        # Spectrum opposites
        spectrum_opposites = []
        for branch, constructs in active.items():
            if not constructs:
                continue
            primary = constructs[0]
            opp = self._query.get_spectrum_opposite(
                branch, primary.get("x", 0), primary.get("y", 0)
            )
            if opp:
                spectrum_opposites.append({
                    "branch": branch,
                    "active": {
                        "position": [primary.get("x"), primary.get("y")],
                        "question": primary.get("question"),
                    },
                    "opposite": {
                        "position": [opp.get("x"), opp.get("y")],
                        "question": opp.get("question"),
                    },
                    "spectrum_question": opp.get("spectrum_question"),
                })

        # Structural profile
        edge_count = sum(
            1 for b, cs in active.items() for c in cs
            if c.get("classification") in ("corner", "midpoint", "edge")
        )
        center_count = sum(
            1 for b, cs in active.items() for c in cs
            if c.get("classification") == "center"
        )
        total = edge_count + center_count
        edge_ratio = edge_count / max(total, 1)
        mean_potency = (
            sum(c.get("potency", 0.6) for b, cs in active.items() for c in cs) / max(total, 1)
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
        for branch in ALL_BRANCHES:
            defn = BRANCH_DEFINITIONS[branch]
            constructs = active.get(branch, [])
            primary = constructs[0] if constructs else None
            spoke = spokes.get(branch, {})

            # Spectrum opposite for this branch
            opp_question = None
            spectrum_question = None
            if primary:
                opp = self._query.get_spectrum_opposite(
                    branch, primary.get("x", 0), primary.get("y", 0)
                )
                if opp:
                    opp_question = opp.get("question")
                    spectrum_question = opp.get("spectrum_question")

            # Tension note
            branch_tensions = [
                t for t in tensions.get("direct", [])
                if any(branch in b for b in t.get("between", []))
            ]
            tension_note = (
                f"{len(branch_tensions)} direct tension(s) involving this branch"
                if branch_tensions else None
            )

            # Generative note
            branch_gens = [
                g for g in generatives
                if any(branch in c for c in g.get("constructs", []))
            ]
            generative_note = (
                f"{len(branch_gens)} generative combination(s) involving this branch"
                if branch_gens else None
            )

            construction_questions[branch] = {
                "template": defn["construction_template"],
                "active_question": primary.get("question") if primary else None,
                "active_question_revisited": primary.get("question_revisited") if primary else None,
                "opposite_question": opp_question,
                "spectrum_question": spectrum_question,
                "classification": primary.get("classification") if primary else None,
                "potency": primary.get("potency") if primary else None,
                "spoke_profile": spoke.get("classification"),
                "spoke_strength": spoke.get("strength", 0.0),
                "tension_note": tension_note,
                "generative_note": generative_note,
            }

        state.construction_basis = {
            "coordinate": state.coordinate,
            "active_constructs": {
                b: [
                    {
                        "position": [c.get("x"), c.get("y")],
                        "classification": c.get("classification"),
                        "potency": c.get("potency"),
                        "question": c.get("question"),
                    }
                    for c in cs
                ]
                for b, cs in active.items()
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
            "spokes": {
                b: {
                    "strength": s.get("strength", 0.0),
                    "consistency": s.get("consistency", 0.0),
                    "polarity": s.get("polarity", 0.0),
                    "contribution": s.get("contribution", 0.0),
                    "classification": s.get("classification"),
                    "gems": s.get("gems", []),
                }
                for b, s in spokes.items()
            },
            "central_gem": central_gem,
            "construction_questions": construction_questions,
        }
