"""Canonical graph data — generates all 1101 nodes and 1459 edges.

Authoritative source: Spec 03 (canonical-content.md), Spec 03a (source-questions.md).
Contains the 100 base questions, 19 spectrum questions, 45 nexus definitions,
and all generation functions.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.grid import classify, potency, generate_spectrums
from advanced_prompting_engine.graph.schema import (
    ALL_BRANCHES,
    BRANCH_DEFINITIONS,
    CENTRAL_GEM_LINK,
    DOMAIN_REPLACEMENTS,
    HAS_CONSTRUCT,
    NEXUS_SOURCE,
    NEXUS_TARGET,
    PRECEDES,
    SPECTRUM_OPPOSITION,
)

# Current canonical version
CANONICAL_VERSION = "0.1.0"

# ---------------------------------------------------------------------------
# Stop words for tag derivation (Spec 03)
# ---------------------------------------------------------------------------

STOP_WORDS = frozenset({
    "what", "is", "the", "of", "a", "an", "at", "in", "from", "how", "does",
    "do", "that", "this", "which", "for", "to", "and", "or", "by", "with",
    "its", "are", "be", "into", "as", "when", "where", "can", "has", "have",
    "through", "between", "within", "upon", "along", "across",
})


# ---------------------------------------------------------------------------
# Minimal stemmer (no nltk dependency — ADR-005)
# ---------------------------------------------------------------------------

_SUFFIXES = [
    "ational", "tional", "ation", "ness", "ment", "able", "ible", "ful",
    "ous", "ive", "ing", "ion", "ity", "ism", "ist", "ent", "ant",
    "ence", "ance", "ly", "al", "ed", "er", "es",
]


def _stem(word: str) -> str:
    """Minimal suffix-stripping stemmer. Consistency > accuracy."""
    if len(word) <= 4:
        return word
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def derive_tags(question: str, branch: str, classification: str) -> list[str]:
    """Extract tags from a parameterized question (Spec 03 tag derivation rule)."""
    words = question.lower().replace("?", "").replace(",", "").replace("'", "").split()
    filtered = [w for w in words if w not in STOP_WORDS and len(w) > 1]
    stemmed = list(dict.fromkeys(_stem(w) for w in filtered))  # deduplicate, preserve order
    stemmed.append(branch)
    stemmed.append(classification)
    return stemmed


# ---------------------------------------------------------------------------
# 100 base questions — indexed by (x, y)
# Edge questions from Spec 03a Q1-Q36, center from Q56-Q99 + authored y=6-8
# All use {domain} placeholder for branch parameterization
# ---------------------------------------------------------------------------

BASE_QUESTIONS: dict[tuple[int, int], str] = {
    # Corners (4)
    (0, 0): "What originating possibility initiates the total epistemic field of {domain}?",
    (9, 0): "What force-defined boundary sets the limitation of harmonic potential across the horizontal axis of {domain}?",
    (0, 9): "What end-state possibility reflects the accumulation of spectral influence along the vertical edge of {domain}?",
    (9, 9): "What convergence of opposed energetic directions yields a coherent inflection in {domain}?",
    # Midpoints — primary 4
    (4, 0): "What axial tension originates from the horizontal dimension's central polarity in {domain}?",
    (9, 4): "What transformation does vertical edge influence undergo at the locus of maximal lateral divergence in {domain}?",
    (4, 9): "What reflected projection completes the harmonic sequence begun from the top center of {domain}?",
    (0, 4): "What counterbalancing projection is enacted through edge-derived force reflection in {domain}?",
    # Midpoints — dual 4 (authored for dual midpoint model)
    (5, 0): "What secondary axial resonance extends from the horizontal center of {domain}?",
    (9, 5): "What post-central lateral transition emerges beyond the vertical midpoint of {domain}?",
    (5, 9): "What mirrored axial completion resolves the bottom center of {domain}?",
    (0, 5): "What ascending medial force bridges the vertical center of {domain}?",
    # Top edge y=0 (7)
    (1, 0): "What emergent polarity forms between anchoring origin and expanding vector in {domain}?",
    (2, 0): "What preliminary expression of spectrum is encoded before the midpoint of {domain} is reached?",
    (3, 0): "What early-stage energetic differentiator signals the initial divergence of {domain}?",
    (6, 0): "What hyperstructural inversion begins to unfold from lateral energy in {domain}?",
    (7, 0): "What high-fidelity spectral signature delineates specific knowing from generalized form in {domain}?",
    (8, 0): "What final pre-corner alignment locks the edge's intent in {domain}?",
    # Right edge x=9 (7)
    (9, 1): "What lateral discharge begins to transfer energetic potency downward in {domain}?",
    (9, 2): "What boundary-modulated field accumulates adjacent to edge-centric energy in {domain}?",
    (9, 3): "What preparation is made for harmonization across horizontal and vertical interplay in {domain}?",
    (9, 6): "What emergent tension creates a mirrored reflection of the upper quadrant in {domain}?",
    (9, 7): "What force-integration model completes the downward projection in {domain}?",
    (9, 8): "What point of containment regulates the end flow of vertical energy in {domain}?",
    # Bottom edge y=9 (7)
    (8, 9): "What spectral conclusion begins the return journey of horizontal contraction in {domain}?",
    (7, 9): "What saturation defines the late-stage energy horizon of {domain}?",
    (6, 9): "What reversal of directional knowledge becomes manifest in {domain}?",
    (3, 9): "What leftward movement of energy distills upper tensions in {domain}?",
    (2, 9): "What potential resolves against its horizontal inverse in {domain}?",
    (1, 9): "What fading polarity finalizes its contribution to {domain}?",
    # Left edge x=0 (7)
    (0, 8): "What structural echo of vertical centrality influences the boundary of {domain}?",
    (0, 7): "What harmonization across lower-edge spectrums arises in this ascending node of {domain}?",
    (0, 6): "What signature potential rotates into active formation within {domain}?",
    (0, 3): "What transitional field mimics inversion before the medial point of {domain}?",
    (0, 2): "What initiating edge thrust configures the spectral flow path of {domain}?",
    (0, 1): "What near-originating field contains an echo of the first point's truth in {domain}?",
    # --- Center points (64) ---
    # Core center (4)
    (4, 4): "What universal convergence of possibility initiates nexus formation in {domain}?",
    (4, 5): "What active boundary supports the center's epistemic field of {domain}?",
    (5, 4): "What mirror of core potential modulates counter-flow in {domain}?",
    (5, 5): "What harmonization at the true grid center governs all structural interactions in {domain}?",
    # Row y=1
    (1, 1): "What embryonic possibility awakens from boundary proximity in {domain}?",
    (2, 1): "What directional gradient modulates substructural motion in {domain}?",
    (3, 1): "What spectral tremor prefigures axial alignment in {domain}?",
    (4, 1): "What harmonic overture begins energetic modulation of {domain}?",
    (5, 1): "What flow redirection captures post-centrality effects in {domain}?",
    (6, 1): "What resonance buffer bounds central field harmonics in {domain}?",
    (7, 1): "What external harmonics leak inward at this position in {domain}?",
    (8, 1): "What semi-boundary potential blurs the center-edge distinction in {domain}?",
    # Row y=2
    (1, 2): "What vertical spectral transition begins force layering in {domain}?",
    (2, 2): "What dual harmonics rise into structured balance within {domain}?",
    (3, 2): "What sweep of cognition modulates upward force in {domain}?",
    (4, 2): "What tuning operation bridges the northern internal zone of {domain}?",
    (5, 2): "What return harmonic reshapes phase delay in {domain}?",
    (6, 2): "What edge proximity biases the flow of {domain}?",
    (7, 2): "What asymmetrical resonance is visible at this locus of {domain}?",
    (8, 2): "What thinning of possibility occurs at this boundary-adjacent point of {domain}?",
    # Row y=3
    (1, 3): "What layering of force expands downward in {domain}?",
    (2, 3): "What midpoint translation occurs at this progressive entry of {domain}?",
    (3, 3): "What convergence wave begins to overlap within {domain}?",
    (4, 3): "What pressure gradient builds before the core of {domain}?",
    (5, 3): "What inverse reflection shapes internal motion of {domain}?",
    (6, 3): "What spectral compression sounds at this stepping-out point of {domain}?",
    (7, 3): "What filtering behavior modulates vector intensity in {domain}?",
    (8, 3): "What preparation for transition is made at this position in {domain}?",
    # Row y=4
    (1, 4): "What return-to-core path signals harmonic approach in {domain}?",
    (2, 4): "What stabilizing formation sits beneath the secondary vertical of {domain}?",
    (3, 4): "What triadic edge balance frames ascending potential in {domain}?",
    (6, 4): "What feedback occurs at the grid dilation boundary of {domain}?",
    (7, 4): "What pressure absorption harmonizes forces at this position of {domain}?",
    (8, 4): "What is filtered from {domain} at this rightward central resolution point?",
    # Row y=5
    (1, 5): "What vertical inversion harmonizes within the southern trajectory of {domain}?",
    (2, 5): "What mirrored convergence operates in phase-locked relationship within {domain}?",
    (3, 5): "What descending gradient re-enters the axis of {domain}?",
    (6, 5): "What winding dispersion approaches the external edge of {domain}?",
    (7, 5): "What final arc of central-to-boundary shift characterizes {domain} here?",
    (8, 5): "What concluding harmonic slips from internal projection in {domain}?",
    # Row y=6 [PROVISIONAL]
    (1, 6): "What deepening structural descent carries {domain} below its median?",
    (2, 6): "What secondary harmonic layer stabilizes {domain} at this depth?",
    (3, 6): "What rotational echo of the upper field persists at this position of {domain}?",
    (4, 6): "What post-core release disperses concentrated energy in {domain}?",
    (5, 6): "What mirror of the upper-center symmetry reflects at this position of {domain}?",
    (6, 6): "What diagonal resonance crosses through this interior node of {domain}?",
    (7, 6): "What dampened edge influence reaches this interior point of {domain}?",
    (8, 6): "What boundary-proximate thinning recurs at this lower position of {domain}?",
    # Row y=7 [PROVISIONAL]
    (1, 7): "What lower-field harmonic rises from the depths of {domain}?",
    (2, 7): "What resolution pattern begins to crystallize at this position of {domain}?",
    (3, 7): "What late-stage convergence draws inward from the field of {domain}?",
    (4, 7): "What pre-terminal synthesis collects the energies of {domain}?",
    (5, 7): "What counterpart to the upper core operates at this depth of {domain}?",
    (6, 7): "What dispersive tendency is counteracted by structural constraint in {domain}?",
    (7, 7): "What near-boundary resonance echoes the opposite corner's influence in {domain}?",
    (8, 7): "What penultimate resolution forms before the terminal edge of {domain}?",
    # Row y=8 [PROVISIONAL]
    (1, 8): "What final interior force prepares {domain} for its southern boundary?",
    (2, 8): "What residual harmonic persists at this depth within {domain}?",
    (3, 8): "What last trace of central convergence is detectable at this position of {domain}?",
    (4, 8): "What pre-edge compression focuses the remaining energy of {domain}?",
    (5, 8): "What mirrored pre-edge state reflects the upper boundary approach of {domain}?",
    (6, 8): "What terminal interior oscillation characterizes this position of {domain}?",
    (7, 8): "What boundary anticipation shapes the final interior expression of {domain}?",
    (8, 8): "What near-corner resonance prefigures the terminal convergence of {domain}?",
}

# Revisited questions (Q87 for (4,4), Q100 for (9,9))
REVISITED_QUESTIONS: dict[tuple[int, int], str] = {
    (4, 4): "What confirms the role of universal synthesizer in {domain}?",
    (9, 9): "How does final epistemic containment fold the totality back into origin symmetry in {domain}?",
}


# ---------------------------------------------------------------------------
# 19 spectrum questions — indexed by (point_a, point_b)
# From Spec 03a Q37-Q55
# ---------------------------------------------------------------------------

SPECTRUM_QUESTIONS: dict[tuple[tuple[int, int], tuple[int, int]], str] = {
    ((0, 0), (9, 9)): "What diagonal spectrum defines the longest uninterrupted field of force-paired knowledge in {domain}?",
    ((0, 1), (9, 8)): "What tension manifests between offset vertical polarities in {domain}?",
    ((0, 2), (9, 7)): "What dynamic between secondaries encodes nuanced relationships in {domain}?",
    ((0, 3), (9, 6)): "What diagonal field carries mirrored harmonic intent in {domain}?",
    ((0, 4), (9, 5)): "What intersectional convergence frames a resonance of central axis inversion in {domain}?",
    ((0, 5), (9, 4)): "What mirrored spectrum balances opposing phase channels in {domain}?",
    ((0, 6), (9, 3)): "What axial rotation produces lateral constraint in {domain}?",
    ((0, 7), (9, 2)): "What reversal mirror is expressed in opposing phase lag in {domain}?",
    ((0, 8), (9, 1)): "What diagonal returns to near-origin configuration in {domain}?",
    ((0, 9), (9, 0)): "What final spectrum defines the inversion between start and end in {domain}?",
    ((1, 0), (8, 9)): "What interior-facing spectrum cross-links secondaries across opposing edge regions in {domain}?",
    ((2, 0), (7, 9)): "What intermediate diagonal translates structural tension into spectral arc in {domain}?",
    ((3, 0), (6, 9)): "What mid-range spectrum amplifies edge-center integration in {domain}?",
    ((4, 0), (5, 9)): "What direct axial alignment overlays mirrored projections in {domain}?",
    ((5, 0), (4, 9)): "What inwardly reversing diagonal manifests dynamic inversion in {domain}?",
    ((6, 0), (3, 9)): "What force corridor overlays reversal with asymmetry in {domain}?",
    ((7, 0), (2, 9)): "What counter-spectral swing defines displaced reciprocity in {domain}?",
    ((8, 0), (1, 9)): "What nearly-terminal spectrum refines terminal edges of {domain}?",
    ((9, 0), (0, 9)): "What full-spectrum inversion completes edge-to-edge totality in {domain}?",
}


# ---------------------------------------------------------------------------
# 45 nexus pair definitions (undirected)
# From Spec 03 nexus definitions
# ---------------------------------------------------------------------------

NEXUS_CONTENT: dict[tuple[str, str], str] = {
    ("ontology", "epistemology"): "How does the nature of what exists determine what can be known, and how does knowing reshape what is recognized as existing?",
    ("ontology", "axiology"): "How does the nature of existence ground what can be valued, and how do values determine which entities are recognized?",
    ("ontology", "teleology"): "How do existing entities bear purpose, and how does purpose call entities into recognized existence?",
    ("ontology", "phenomenology"): "How does existence present itself to experience, and how does experience constitute what is recognized as real?",
    ("ontology", "praxeology"): "How does the structure of what exists enable or constrain action, and how does action alter what exists?",
    ("ontology", "methodology"): "How does the nature of existence determine which methods of inquiry are valid, and how do methods reveal or construct entities?",
    ("ontology", "semiotics"): "How do existing entities generate signs, and how do signs constitute the recognition of entities?",
    ("ontology", "hermeneutics"): "How does the nature of what exists shape how it is interpreted, and how does interpretation reconstitute what is understood to exist?",
    ("ontology", "heuristics"): "How does the structure of existence determine which problem-solving strategies are viable, and how do strategies reshape perceived reality?",
    ("epistemology", "axiology"): "How does justified knowledge determine what is worth valuing, and how do values shape what counts as knowledge?",
    ("epistemology", "teleology"): "How does knowledge direct purpose, and how does purpose determine what is worth knowing?",
    ("epistemology", "phenomenology"): "How does knowledge relate to lived experience, and how does experience generate or undermine claims to knowledge?",
    ("epistemology", "praxeology"): "How does knowing inform acting, and how does acting produce or revise knowledge?",
    ("epistemology", "methodology"): "How do justified beliefs determine valid methods, and how do methods produce justified beliefs?",
    ("epistemology", "semiotics"): "How does knowledge encode into signs, and how do signs carry or distort epistemic content?",
    ("epistemology", "hermeneutics"): "How does established knowledge frame interpretation, and how does interpretation challenge or extend knowledge?",
    ("epistemology", "heuristics"): "How does knowledge inform strategy, and how do strategies reveal knowledge that formal methods miss?",
    ("axiology", "teleology"): "How do values define purpose, and how does purpose reveal which values are operative?",
    ("axiology", "phenomenology"): "How do values shape experience, and how does experience challenge or validate value claims?",
    ("axiology", "praxeology"): "How do values motivate action, and how do the outcomes of action revise what is valued?",
    ("axiology", "methodology"): "How do values determine which methods are acceptable, and how do methods produce value judgments?",
    ("axiology", "semiotics"): "How are values communicated through signs, and how do semiotic structures privilege certain values?",
    ("axiology", "hermeneutics"): "How do values frame interpretation, and how does interpretation reveal hidden value commitments?",
    ("axiology", "heuristics"): "How do values constrain strategy, and how do strategic outcomes reshape value hierarchies?",
    ("teleology", "phenomenology"): "How does purpose structure experience, and how does experience reveal or subvert intended purpose?",
    ("teleology", "praxeology"): "How does purpose direct action, and how does action fulfill, redirect, or abandon purpose?",
    ("teleology", "methodology"): "How does purpose select method, and how do methodological constraints reshape achievable purpose?",
    ("teleology", "semiotics"): "How is purpose encoded in communication, and how do semiotic structures enable or obscure purpose?",
    ("teleology", "hermeneutics"): "How does purpose frame interpretation, and how does interpretation reveal purposes not consciously intended?",
    ("teleology", "heuristics"): "How does purpose constrain strategy, and how do pragmatic strategies reshape what purposes are pursued?",
    ("phenomenology", "praxeology"): "How does experience motivate action, and how does action transform the quality of experience?",
    ("phenomenology", "methodology"): "How does experience inform method, and how do methods structure what can be experienced?",
    ("phenomenology", "semiotics"): "How does experience generate meaning, and how do signs shape what is experienceable?",
    ("phenomenology", "hermeneutics"): "How does lived experience frame interpretation, and how does interpretation deepen or distort experience?",
    ("phenomenology", "heuristics"): "How does experience inform practical strategy, and how do strategies alter the texture of experience?",
    ("praxeology", "methodology"): "How does action require method, and how do methods constrain or enable forms of action?",
    ("praxeology", "semiotics"): "How is action communicated, and how do communicative structures shape what actions are conceivable?",
    ("praxeology", "hermeneutics"): "How is action interpreted, and how does interpretation of past action shape future action?",
    ("praxeology", "heuristics"): "How do strategies structure action, and how does action under uncertainty refine available strategies?",
    ("methodology", "semiotics"): "How do methods produce signs, and how do semiotic conventions determine which methods are communicable?",
    ("methodology", "hermeneutics"): "How do methods frame interpretation, and how does interpretive practice challenge methodological assumptions?",
    ("methodology", "heuristics"): "How do formal methods relate to informal strategies, and how do heuristic discoveries become formalized methods?",
    ("semiotics", "hermeneutics"): "How do signs invite interpretation, and how does interpretive practice generate new semiotic conventions?",
    ("semiotics", "heuristics"): "How do signs encode strategies, and how do strategic adaptations produce new signs?",
    ("hermeneutics", "heuristics"): "How does interpretation inform practical strategy, and how do strategies for managing the unknown reshape interpretive frames?",
}

CENTRAL_GEM_CONTENT = (
    "What singular coherence emerges when the extremes of existence, knowing, "
    "valuing, purposing, experiencing, acting, systematizing, communicating, "
    "interpreting, and strategizing are held simultaneously in mutual awareness?"
)


# ---------------------------------------------------------------------------
# Generation functions
# ---------------------------------------------------------------------------

def generate_all_branches() -> list[dict]:
    """Generate the 10 branch nodes."""
    nodes = []
    for i, branch in enumerate(ALL_BRANCHES):
        defn = BRANCH_DEFINITIONS[branch]
        nodes.append({
            "id": branch,
            "type": "branch",
            "tier": 1,
            "core_question": defn["core_question"],
            "construction_template": defn["construction_template"],
            "x_axis_name": defn["x_axis_name"],
            "x_axis_low": defn["x_axis_low"],
            "x_axis_high": defn["x_axis_high"],
            "y_axis_name": defn["y_axis_name"],
            "y_axis_low": defn["y_axis_low"],
            "y_axis_high": defn["y_axis_high"],
            "causal_order": i,
            "provenance": "canonical",
            "mutable": False,
        })
    return nodes


def generate_all_constructs() -> list[dict]:
    """Generate all 1000 construct nodes (100 per branch × 10 branches)."""
    nodes = []
    for branch in ALL_BRANCHES:
        domain = DOMAIN_REPLACEMENTS[branch]
        for x in range(10):
            for y in range(10):
                base_q = BASE_QUESTIONS.get((x, y))
                if base_q is None:
                    raise ValueError(f"Missing base question for position ({x}, {y})")

                question = base_q.replace("{domain}", domain)
                cls = classify(x, y)
                pot = potency(x, y)

                revisited_base = REVISITED_QUESTIONS.get((x, y))
                question_revisited = revisited_base.replace("{domain}", domain) if revisited_base else None

                tags = derive_tags(question, branch, cls)

                nodes.append({
                    "id": f"{branch}.{x}_{y}",
                    "type": "construct",
                    "tier": 2,
                    "branch": branch,
                    "x": x,
                    "y": y,
                    "classification": cls,
                    "potency": pot,
                    "question": question,
                    "question_revisited": question_revisited,
                    "description": f"{cls.title()} construct at ({x},{y}) in {branch}: {question}",
                    "tags": tags,
                    "spectrum_ids": [],  # populated during edge generation
                    "condensed_gems": [],
                    "provenance": "canonical",
                    "mutable": False,
                })
    return nodes


def generate_all_nexi() -> list[dict]:
    """Generate all 90 directional nexus nodes (45 pairs × 2 directions)."""
    nodes = []
    for (branch_a, branch_b), content in NEXUS_CONTENT.items():
        # A→B direction
        nodes.append({
            "id": f"nexus.{branch_a}.{branch_b}",
            "type": "nexus",
            "source_branch": branch_a,
            "target_branch": branch_b,
            "content": content,
            "provenance": "canonical",
            "mutable": False,
        })
        # B→A direction (same content, reversed source/target)
        nodes.append({
            "id": f"nexus.{branch_b}.{branch_a}",
            "type": "nexus",
            "source_branch": branch_b,
            "target_branch": branch_a,
            "content": content,
            "provenance": "canonical",
            "mutable": False,
        })
    return nodes


def generate_central_gem() -> dict:
    """Generate the single central gem node."""
    return {
        "id": "central_gem",
        "type": "central_gem",
        "content": CENTRAL_GEM_CONTENT,
        "provenance": "canonical",
        "mutable": False,
    }


def generate_all_edges(constructs: list[dict] | None = None) -> list[dict]:
    """Generate all 1459 canonical edges.

    If constructs is provided, populates their spectrum_ids in place.
    """
    edges: list[dict] = []
    construct_index = {c["id"]: c for c in constructs} if constructs else {}

    # 1. HAS_CONSTRUCT edges (1000)
    for branch in ALL_BRANCHES:
        for x in range(10):
            for y in range(10):
                edges.append({
                    "source_id": branch,
                    "target_id": f"{branch}.{x}_{y}",
                    "relation": HAS_CONSTRUCT,
                })

    # 2. PRECEDES edges (9)
    for i in range(len(ALL_BRANCHES) - 1):
        edges.append({
            "source_id": ALL_BRANCHES[i],
            "target_id": ALL_BRANCHES[i + 1],
            "relation": PRECEDES,
        })

    # 3. SPECTRUM_OPPOSITION edges (180 = 18 per branch × 10)
    for branch in ALL_BRANCHES:
        domain = DOMAIN_REPLACEMENTS[branch]
        spectrums = generate_spectrums(branch)
        for sid, a_id, b_id in spectrums:
            # Parse positions from IDs
            ax, ay = map(int, a_id.split(".")[1].split("_"))
            bx, by = map(int, b_id.split(".")[1].split("_"))

            # Look up spectrum question (may be None)
            pair_key = tuple(sorted([(ax, ay), (bx, by)]))
            spectrum_q = (
                SPECTRUM_QUESTIONS.get(pair_key)
                or SPECTRUM_QUESTIONS.get((pair_key[1], pair_key[0]))
            )
            question = spectrum_q.replace("{domain}", domain) if spectrum_q else None

            edges.append({
                "source_id": a_id,
                "target_id": b_id,
                "relation": SPECTRUM_OPPOSITION,
                "spectrum_id": sid,
                "strength": 0.6,
                "question": question,
                "source": "geometric",
            })

            # Populate spectrum_ids on construct nodes if provided
            if construct_index:
                if a_id in construct_index:
                    construct_index[a_id]["spectrum_ids"].append(sid)
                if b_id in construct_index:
                    construct_index[b_id]["spectrum_ids"].append(sid)

    # 4. NEXUS_SOURCE edges (90)
    for (branch_a, branch_b) in NEXUS_CONTENT:
        edges.append({
            "source_id": f"nexus.{branch_a}.{branch_b}",
            "target_id": branch_a,
            "relation": NEXUS_SOURCE,
        })
        edges.append({
            "source_id": f"nexus.{branch_b}.{branch_a}",
            "target_id": branch_b,
            "relation": NEXUS_SOURCE,
        })

    # 5. NEXUS_TARGET edges (90)
    for (branch_a, branch_b) in NEXUS_CONTENT:
        edges.append({
            "source_id": f"nexus.{branch_a}.{branch_b}",
            "target_id": branch_b,
            "relation": NEXUS_TARGET,
        })
        edges.append({
            "source_id": f"nexus.{branch_b}.{branch_a}",
            "target_id": branch_a,
            "relation": NEXUS_TARGET,
        })

    # 6. CENTRAL_GEM_LINK edges (90)
    for (branch_a, branch_b) in NEXUS_CONTENT:
        edges.append({
            "source_id": "central_gem",
            "target_id": f"nexus.{branch_a}.{branch_b}",
            "relation": CENTRAL_GEM_LINK,
        })
        edges.append({
            "source_id": "central_gem",
            "target_id": f"nexus.{branch_b}.{branch_a}",
            "relation": CENTRAL_GEM_LINK,
        })

    return edges


def generate_all_canonical() -> tuple[list[dict], list[dict]]:
    """Generate all canonical nodes and edges.

    Returns (nodes, edges) ready for SqliteStore.initialize_canonical().
    """
    branches = generate_all_branches()
    constructs = generate_all_constructs()
    nexi = generate_all_nexi()
    gem = generate_central_gem()

    nodes = branches + constructs + nexi + [gem]
    edges = generate_all_edges(constructs)

    return nodes, edges
