"""Canonical graph data — generates all 1101 nodes and 1629 edges.

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
CANONICAL_VERSION = "0.1.2"

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
    # Midpoints — dual 4 (spec source questions Q12, Q19, Q26, Q33)
    (5, 0): "What resonant field defines transitional knowledge zones in {domain}?",
    (9, 5): "What energetic recoil or redirection signals inversion from external to internal force in {domain}?",
    (5, 9): "What terminal convergence mirrors the primary center of {domain}?",
    (0, 5): "What balanced state reflects both ascending and descending tension in {domain}?",
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
# Canonical cross-branch edges (197 total)
# Derived from 45 nexus definitions × 16 corner pairings each.
# Each edge: (source_id, target_id, relation, strength, nexus_pair, justification)
# ---------------------------------------------------------------------------

CANONICAL_CROSS_BRANCH_EDGES: list[tuple[str, str, str, float, str, str]] = [
    # === Ontology ↔ Epistemology (6) ===
    ("ontology.0_0", "epistemology.0_0", "COMPATIBLE_WITH", 0.8, "ontology-epistemology", "particular static entities are the natural objects of empirical certainty"),
    ("ontology.9_0", "epistemology.9_0", "COMPATIBLE_WITH", 0.8, "ontology-epistemology", "universal static categories are the natural objects of rational certainty"),
    ("ontology.0_9", "epistemology.9_0", "TENSIONS_WITH", 0.7, "ontology-epistemology", "changing particulars resist fixed rational categorization"),
    ("ontology.9_9", "epistemology.0_0", "TENSIONS_WITH", 0.7, "ontology-epistemology", "evolving universal categories resist empirical certainty at a fixed point"),
    ("ontology.0_9", "epistemology.0_9", "COMPATIBLE_WITH", 0.7, "ontology-epistemology", "changing particulars are best known through revisable empirical observation"),
    ("ontology.9_9", "epistemology.9_9", "COMPATIBLE_WITH", 0.7, "ontology-epistemology", "evolving universals are best known through provisional rational inference"),
    # === Ontology ↔ Axiology (4) ===
    ("ontology.0_0", "axiology.0_0", "COMPATIBLE_WITH", 0.7, "ontology-axiology", "particular static entities are naturally valued intrinsically by individuals"),
    ("ontology.9_0", "axiology.9_9", "COMPATIBLE_WITH", 0.7, "ontology-axiology", "fixed universal categories serve as instruments for collective organization"),
    ("ontology.0_9", "axiology.9_9", "TENSIONS_WITH", 0.5, "ontology-axiology", "evolving particulars resist collective instrumentalization"),
    ("ontology.9_9", "axiology.0_0", "TENSIONS_WITH", 0.5, "ontology-axiology", "evolving universals resist individual intrinsic valuation"),
    # === Ontology ↔ Teleology (5) ===
    ("ontology.0_0", "teleology.0_0", "COMPATIBLE_WITH", 0.7, "ontology-teleology", "particular static entities naturally serve immediate intentional purposes"),
    ("ontology.9_9", "teleology.9_9", "COMPATIBLE_WITH", 0.8, "ontology-teleology", "evolving universals align with ultimate emergent purpose"),
    ("ontology.0_0", "teleology.9_9", "TENSIONS_WITH", 0.7, "ontology-teleology", "fixed particulars resist bearing emergent ultimate purpose"),
    ("ontology.9_0", "teleology.9_0", "COMPATIBLE_WITH", 0.7, "ontology-teleology", "fixed universal categories embody intentional ultimate purpose"),
    ("ontology.0_9", "teleology.0_9", "COMPATIBLE_WITH", 0.7, "ontology-teleology", "changing particulars naturally produce immediate emergent purposes"),
    # === Ontology ↔ Phenomenology (4) ===
    ("ontology.0_0", "phenomenology.0_0", "COMPATIBLE_WITH", 0.8, "ontology-phenomenology", "fixed particulars naturally present as observable surface phenomena"),
    ("ontology.9_9", "phenomenology.9_9", "COMPATIBLE_WITH", 0.7, "ontology-phenomenology", "evolving universals are constituted through deep subjective experience"),
    ("ontology.0_0", "phenomenology.9_9", "TENSIONS_WITH", 0.6, "ontology-phenomenology", "fixed particulars resist constitution through deep subjective experience"),
    ("ontology.9_0", "phenomenology.9_0", "TENSIONS_WITH", 0.5, "ontology-phenomenology", "universal categories resist reduction to surface subjective impression"),
    # === Ontology ↔ Praxeology (4) ===
    ("ontology.0_0", "praxeology.0_0", "COMPATIBLE_WITH", 0.7, "ontology-praxeology", "fixed particulars naturally elicit individual reactive response"),
    ("ontology.9_9", "praxeology.9_9", "COMPATIBLE_WITH", 0.7, "ontology-praxeology", "evolving universals require coordinated proactive engagement"),
    ("ontology.0_0", "praxeology.9_9", "TENSIONS_WITH", 0.6, "ontology-praxeology", "fixed particulars resist requiring coordinated proactive initiative"),
    ("ontology.9_0", "praxeology.9_0", "COMPATIBLE_WITH", 0.5, "ontology-praxeology", "fixed universal structures enable coordinated reactive response"),
    # === Ontology ↔ Methodology (5) ===
    ("ontology.9_0", "methodology.0_0", "COMPATIBLE_WITH", 0.8, "ontology-methodology", "fixed universal categories are naturally analyzed through deduction"),
    ("ontology.0_9", "methodology.9_9", "COMPATIBLE_WITH", 0.8, "ontology-methodology", "changing particulars are best understood through inductive synthesis"),
    ("ontology.9_0", "methodology.9_9", "TENSIONS_WITH", 0.7, "ontology-methodology", "fixed universal categories resist inductive construction from cases"),
    ("ontology.0_0", "methodology.0_0", "COMPATIBLE_WITH", 0.6, "ontology-methodology", "particular static entities yield to analytic deductive examination"),
    ("ontology.0_9", "methodology.0_0", "TENSIONS_WITH", 0.6, "ontology-methodology", "changing particulars resist fixed analytic deductive decomposition"),
    # === Ontology ↔ Semiotics (3) ===
    ("ontology.0_0", "semiotics.0_0", "COMPATIBLE_WITH", 0.7, "ontology-semiotics", "fixed particulars generate explicit syntactic signs"),
    ("ontology.9_9", "semiotics.9_9", "COMPATIBLE_WITH", 0.7, "ontology-semiotics", "evolving universals constitute recognition through implicit semantic signs"),
    ("ontology.0_0", "semiotics.9_9", "TENSIONS_WITH", 0.5, "ontology-semiotics", "fixed particulars resist constitution through implicit semantic meaning"),
    # === Ontology ↔ Hermeneutics (4) ===
    ("ontology.0_0", "hermeneutics.0_0", "COMPATIBLE_WITH", 0.8, "ontology-hermeneutics", "fixed particulars are naturally interpreted literally as the author intended"),
    ("ontology.9_9", "hermeneutics.9_9", "COMPATIBLE_WITH", 0.8, "ontology-hermeneutics", "evolving universals are reconstituted through figurative reader interpretation"),
    ("ontology.0_0", "hermeneutics.9_9", "TENSIONS_WITH", 0.7, "ontology-hermeneutics", "fixed particulars resist figurative reader reinterpretation"),
    ("ontology.9_0", "hermeneutics.9_0", "COMPATIBLE_WITH", 0.6, "ontology-hermeneutics", "universal categories are expressed through intentional figurative abstraction"),
    # === Ontology ↔ Heuristics (5) ===
    ("ontology.0_0", "heuristics.0_0", "COMPATIBLE_WITH", 0.7, "ontology-heuristics", "fixed particular entities are best addressed by systematic conservative strategy"),
    ("ontology.9_9", "heuristics.9_9", "COMPATIBLE_WITH", 0.7, "ontology-heuristics", "evolving universals require intuitive exploratory strategy"),
    ("ontology.0_0", "heuristics.9_9", "TENSIONS_WITH", 0.6, "ontology-heuristics", "fixed particulars resist requiring intuitive exploratory strategy"),
    ("ontology.9_9", "heuristics.0_0", "TENSIONS_WITH", 0.6, "ontology-heuristics", "evolving universals resist systematic conservative constraints"),
    ("ontology.0_9", "heuristics.0_9", "COMPATIBLE_WITH", 0.5, "ontology-heuristics", "changing particulars benefit from systematic exploratory strategy"),
    # === Epistemology ↔ Axiology (4) ===
    ("epistemology.0_0", "axiology.9_0", "COMPATIBLE_WITH", 0.7, "epistemology-axiology", "verified empirical facts naturally serve individual instrumental value"),
    ("epistemology.9_0", "axiology.0_9", "COMPATIBLE_WITH", 0.6, "epistemology-axiology", "proven rational truths carry intrinsic collective worth"),
    ("epistemology.0_9", "axiology.0_0", "TENSIONS_WITH", 0.5, "epistemology-axiology", "provisional empirical observations resist grounding stable intrinsic individual value"),
    ("epistemology.9_9", "axiology.9_9", "COMPATIBLE_WITH", 0.5, "epistemology-axiology", "speculative rational inference serves collective instrumental ends"),
    # === Epistemology ↔ Teleology (5) ===
    ("epistemology.0_0", "teleology.0_0", "COMPATIBLE_WITH", 0.8, "epistemology-teleology", "empirical certainty directs immediate intentional purpose"),
    ("epistemology.9_0", "teleology.9_0", "COMPATIBLE_WITH", 0.8, "epistemology-teleology", "rational certainty directs ultimate intentional purpose"),
    ("epistemology.0_9", "teleology.0_9", "COMPATIBLE_WITH", 0.7, "epistemology-teleology", "provisional observation produces immediate emergent purpose"),
    ("epistemology.9_9", "teleology.9_9", "COMPATIBLE_WITH", 0.7, "epistemology-teleology", "provisional rational inference aligns with ultimate emergent purpose"),
    ("epistemology.0_0", "teleology.9_9", "TENSIONS_WITH", 0.6, "epistemology-teleology", "empirical certainty resists directing toward emergent ultimate purpose"),
    # === Epistemology ↔ Phenomenology (4) ===
    ("epistemology.0_0", "phenomenology.0_0", "COMPATIBLE_WITH", 0.8, "epistemology-phenomenology", "empirical certainty aligns with objective surface experience"),
    ("epistemology.9_9", "phenomenology.9_9", "COMPATIBLE_WITH", 0.6, "epistemology-phenomenology", "provisional rational inference engages deep subjective experience"),
    ("epistemology.0_0", "phenomenology.9_9", "TENSIONS_WITH", 0.7, "epistemology-phenomenology", "empirical certainty cannot access deep subjective experience"),
    ("epistemology.9_0", "phenomenology.0_9", "TENSIONS_WITH", 0.5, "epistemology-phenomenology", "rational certainty tensions with objective deep pre-reflective structure"),
    # === Epistemology ↔ Praxeology (4) ===
    ("epistemology.0_0", "praxeology.0_0", "COMPATIBLE_WITH", 0.7, "epistemology-praxeology", "empirical certainty informs individual reactive action"),
    ("epistemology.9_0", "praxeology.9_9", "COMPATIBLE_WITH", 0.6, "epistemology-praxeology", "rational certainty enables coordinated proactive action"),
    ("epistemology.0_9", "praxeology.0_9", "COMPATIBLE_WITH", 0.6, "epistemology-praxeology", "provisional empirical knowledge drives individual proactive testing"),
    ("epistemology.9_9", "praxeology.9_0", "TENSIONS_WITH", 0.5, "epistemology-praxeology", "provisional rational inference tensions with coordinated reactive demands"),
    # === Epistemology ↔ Methodology (5) ===
    ("epistemology.0_0", "methodology.0_0", "COMPATIBLE_WITH", 0.8, "epistemology-methodology", "empirical certainty and analytic deduction mutually validate"),
    ("epistemology.9_0", "methodology.9_0", "COMPATIBLE_WITH", 0.7, "epistemology-methodology", "rational certainty aligns with synthetic deductive construction"),
    ("epistemology.0_9", "methodology.0_9", "COMPATIBLE_WITH", 0.8, "epistemology-methodology", "provisional empirical knowledge aligns with analytic inductive method"),
    ("epistemology.9_9", "methodology.9_9", "COMPATIBLE_WITH", 0.7, "epistemology-methodology", "provisional rational inference aligns with synthetic inductive method"),
    ("epistemology.0_0", "methodology.9_9", "TENSIONS_WITH", 0.6, "epistemology-methodology", "empirical certainty resists synthetic inductive reconstruction"),
    # === Epistemology ↔ Semiotics (3) ===
    ("epistemology.0_0", "semiotics.0_0", "COMPATIBLE_WITH", 0.7, "epistemology-semiotics", "empirical certainty encodes naturally into explicit syntactic signs"),
    ("epistemology.9_9", "semiotics.9_9", "COMPATIBLE_WITH", 0.6, "epistemology-semiotics", "provisional rational inference travels through implicit semantic signs"),
    ("epistemology.0_0", "semiotics.9_9", "TENSIONS_WITH", 0.6, "epistemology-semiotics", "empirical certainty is distorted by implicit semantic encoding"),
    # === Epistemology ↔ Hermeneutics (4) ===
    ("epistemology.0_0", "hermeneutics.0_0", "COMPATIBLE_WITH", 0.8, "epistemology-hermeneutics", "empirical certainty frames literal author-intent interpretation"),
    ("epistemology.9_9", "hermeneutics.9_9", "COMPATIBLE_WITH", 0.7, "epistemology-hermeneutics", "provisional reasoning invites figurative reader-response interpretation"),
    ("epistemology.0_0", "hermeneutics.9_9", "TENSIONS_WITH", 0.7, "epistemology-hermeneutics", "empirical certainty resists figurative reader reinterpretation"),
    ("epistemology.9_0", "hermeneutics.9_0", "COMPATIBLE_WITH", 0.6, "epistemology-hermeneutics", "rational certainty expressed through intentional figurative abstraction"),
    # === Epistemology ↔ Heuristics (4) ===
    ("epistemology.0_0", "heuristics.0_0", "COMPATIBLE_WITH", 0.7, "epistemology-heuristics", "empirical certainty supports systematic conservative strategy"),
    ("epistemology.9_9", "heuristics.9_9", "COMPATIBLE_WITH", 0.7, "epistemology-heuristics", "provisional reasoning partners with intuitive exploratory strategy"),
    ("epistemology.0_0", "heuristics.9_9", "TENSIONS_WITH", 0.6, "epistemology-heuristics", "empirical certainty resists intuitive exploratory strategy"),
    ("epistemology.0_9", "heuristics.0_9", "COMPATIBLE_WITH", 0.6, "epistemology-heuristics", "provisional empirical knowledge benefits from systematic exploration"),
    # === Axiology ↔ Teleology (4) ===
    ("axiology.0_0", "teleology.0_0", "COMPATIBLE_WITH", 0.7, "axiology-teleology", "intrinsic individual value defines immediate intentional purpose"),
    ("axiology.9_9", "teleology.9_9", "COMPATIBLE_WITH", 0.7, "axiology-teleology", "instrumental collective value aligns with ultimate emergent purpose"),
    ("axiology.0_0", "teleology.9_9", "TENSIONS_WITH", 0.6, "axiology-teleology", "intrinsic individual value resists ultimate emergent purpose"),
    ("axiology.9_0", "teleology.9_0", "COMPATIBLE_WITH", 0.6, "axiology-teleology", "instrumental individual value serves ultimate intentional purpose"),
    # === Axiology ↔ Phenomenology (4) ===
    ("axiology.0_0", "phenomenology.9_9", "COMPATIBLE_WITH", 0.7, "axiology-phenomenology", "intrinsic individual value is validated through deep subjective experience"),
    ("axiology.9_9", "phenomenology.0_0", "COMPATIBLE_WITH", 0.6, "axiology-phenomenology", "instrumental collective value is validated through objective surface observation"),
    ("axiology.0_0", "phenomenology.0_0", "TENSIONS_WITH", 0.5, "axiology-phenomenology", "intrinsic value is challenged by reduction to objective surface experience"),
    ("axiology.0_9", "phenomenology.9_9", "COMPATIBLE_WITH", 0.6, "axiology-phenomenology", "intrinsic collective value shaped through deep subjective shared experience"),
    # === Axiology ↔ Praxeology (4) ===
    ("axiology.0_0", "praxeology.0_9", "COMPATIBLE_WITH", 0.7, "axiology-praxeology", "intrinsic individual value motivates individual proactive initiative"),
    ("axiology.9_9", "praxeology.9_9", "COMPATIBLE_WITH", 0.7, "axiology-praxeology", "instrumental collective value motivates coordinated proactive action"),
    ("axiology.0_0", "praxeology.9_0", "TENSIONS_WITH", 0.6, "axiology-praxeology", "intrinsic individual value tensions with coordinated reactive demands"),
    ("axiology.9_0", "praxeology.0_0", "COMPATIBLE_WITH", 0.5, "axiology-praxeology", "instrumental individual value motivates individual reactive response"),
    # === Axiology ↔ Methodology (4) ===
    ("axiology.0_0", "methodology.0_0", "COMPATIBLE_WITH", 0.6, "axiology-methodology", "intrinsic individual value favors analytic deductive rigor"),
    ("axiology.9_9", "methodology.9_9", "COMPATIBLE_WITH", 0.6, "axiology-methodology", "instrumental collective value favors synthetic inductive pragmatism"),
    ("axiology.0_0", "methodology.9_9", "TENSIONS_WITH", 0.5, "axiology-methodology", "intrinsic individual value resists synthetic inductive methods"),
    ("axiology.0_9", "methodology.0_9", "COMPATIBLE_WITH", 0.5, "axiology-methodology", "intrinsic collective value aligns with analytic inductive discovery"),
    # === Axiology ↔ Semiotics (3) ===
    ("axiology.0_0", "semiotics.0_9", "COMPATIBLE_WITH", 0.6, "axiology-semiotics", "intrinsic individual value communicates through explicit semantic meaning"),
    ("axiology.9_9", "semiotics.9_0", "COMPATIBLE_WITH", 0.5, "axiology-semiotics", "instrumental collective value encoded through implicit syntactic convention"),
    ("axiology.0_0", "semiotics.9_0", "TENSIONS_WITH", 0.5, "axiology-semiotics", "intrinsic value resists implicit syntactic encoding"),
    # === Axiology ↔ Hermeneutics (4) ===
    ("axiology.0_0", "hermeneutics.0_0", "COMPATIBLE_WITH", 0.7, "axiology-hermeneutics", "intrinsic individual value frames literal author-intent interpretation"),
    ("axiology.9_9", "hermeneutics.9_9", "COMPATIBLE_WITH", 0.6, "axiology-hermeneutics", "instrumental collective value revealed through figurative reader-response"),
    ("axiology.0_0", "hermeneutics.9_9", "TENSIONS_WITH", 0.6, "axiology-hermeneutics", "intrinsic individual value resists figurative reader reinterpretation"),
    ("axiology.0_9", "hermeneutics.0_9", "COMPATIBLE_WITH", 0.5, "axiology-hermeneutics", "intrinsic collective value frames literal reader-response"),
    # === Axiology ↔ Heuristics (4) ===
    ("axiology.0_0", "heuristics.0_0", "COMPATIBLE_WITH", 0.7, "axiology-heuristics", "intrinsic individual value constrains toward systematic conservative strategy"),
    ("axiology.9_9", "heuristics.9_9", "COMPATIBLE_WITH", 0.6, "axiology-heuristics", "instrumental collective value permits intuitive exploratory strategy"),
    ("axiology.0_0", "heuristics.9_9", "TENSIONS_WITH", 0.6, "axiology-heuristics", "intrinsic individual value resists intuitive exploratory risk"),
    ("axiology.9_0", "heuristics.9_0", "COMPATIBLE_WITH", 0.5, "axiology-heuristics", "instrumental individual value aligns with intuitive conservative caution"),
    # === Teleology ↔ Phenomenology (4) ===
    ("teleology.0_0", "phenomenology.0_0", "COMPATIBLE_WITH", 0.7, "teleology-phenomenology", "immediate intentional purpose structures objective surface experience"),
    ("teleology.9_9", "phenomenology.9_9", "COMPATIBLE_WITH", 0.7, "teleology-phenomenology", "ultimate emergent purpose revealed through deep subjective experience"),
    ("teleology.0_0", "phenomenology.9_9", "TENSIONS_WITH", 0.6, "teleology-phenomenology", "immediate intentional purpose resists deep subjective subversion"),
    ("teleology.0_9", "phenomenology.9_0", "COMPATIBLE_WITH", 0.5, "teleology-phenomenology", "immediate emergent purpose revealed through subjective surface impression"),
    # === Teleology ↔ Praxeology (4) ===
    ("teleology.0_0", "praxeology.0_0", "COMPATIBLE_WITH", 0.8, "teleology-praxeology", "immediate intentional purpose directs individual reactive action"),
    ("teleology.9_0", "praxeology.9_9", "COMPATIBLE_WITH", 0.8, "teleology-praxeology", "ultimate intentional purpose directs coordinated proactive action"),
    ("teleology.9_9", "praxeology.0_0", "TENSIONS_WITH", 0.6, "teleology-praxeology", "ultimate emergent purpose tensions with individual reactive response"),
    ("teleology.0_9", "praxeology.0_9", "COMPATIBLE_WITH", 0.7, "teleology-praxeology", "immediate emergent purpose drives individual proactive initiative"),
    # === Teleology ↔ Methodology (4) ===
    ("teleology.0_0", "methodology.0_0", "COMPATIBLE_WITH", 0.7, "teleology-methodology", "immediate intentional purpose selects analytic deductive method"),
    ("teleology.9_9", "methodology.9_9", "COMPATIBLE_WITH", 0.7, "teleology-methodology", "ultimate emergent purpose reshapes toward synthetic inductive method"),
    ("teleology.9_0", "methodology.0_0", "COMPATIBLE_WITH", 0.6, "teleology-methodology", "ultimate intentional purpose sustains analytic deductive method"),
    ("teleology.0_0", "methodology.9_9", "TENSIONS_WITH", 0.6, "teleology-methodology", "immediate intentional purpose resists synthetic inductive emergence"),
    # === Teleology ↔ Semiotics (3) ===
    ("teleology.0_0", "semiotics.0_0", "COMPATIBLE_WITH", 0.7, "teleology-semiotics", "immediate intentional purpose encoded through explicit syntactic signals"),
    ("teleology.9_9", "semiotics.9_9", "COMPATIBLE_WITH", 0.6, "teleology-semiotics", "ultimate emergent purpose carried through implicit semantic meaning"),
    ("teleology.0_0", "semiotics.9_9", "TENSIONS_WITH", 0.5, "teleology-semiotics", "immediate intentional purpose resists implicit semantic obscurity"),
    # === Teleology ↔ Hermeneutics (3) ===
    ("teleology.0_0", "hermeneutics.0_0", "COMPATIBLE_WITH", 0.8, "teleology-hermeneutics", "immediate intentional purpose frames literal author-intent interpretation"),
    ("teleology.9_9", "hermeneutics.9_9", "COMPATIBLE_WITH", 0.7, "teleology-hermeneutics", "ultimate emergent purpose reveals through figurative reader-response"),
    ("teleology.0_0", "hermeneutics.9_9", "TENSIONS_WITH", 0.7, "teleology-hermeneutics", "immediate intentional purpose resists figurative reader reinterpretation"),
    # === Teleology ↔ Heuristics (4) ===
    ("teleology.0_0", "heuristics.0_0", "COMPATIBLE_WITH", 0.7, "teleology-heuristics", "immediate intentional purpose constrains toward systematic conservative strategy"),
    ("teleology.9_9", "heuristics.9_9", "COMPATIBLE_WITH", 0.7, "teleology-heuristics", "ultimate emergent purpose demands intuitive exploratory strategy"),
    ("teleology.0_0", "heuristics.9_9", "TENSIONS_WITH", 0.6, "teleology-heuristics", "immediate intentional purpose resists intuitive exploratory risk"),
    ("teleology.9_0", "heuristics.0_0", "COMPATIBLE_WITH", 0.5, "teleology-heuristics", "ultimate intentional purpose sustains systematic conservative strategy"),
    # === Phenomenology ↔ Praxeology (3) ===
    ("phenomenology.0_0", "praxeology.0_0", "COMPATIBLE_WITH", 0.7, "phenomenology-praxeology", "objective surface experience motivates individual reactive action"),
    ("phenomenology.9_9", "praxeology.0_9", "COMPATIBLE_WITH", 0.6, "phenomenology-praxeology", "deep subjective experience motivates individual proactive initiative"),
    ("phenomenology.0_0", "praxeology.9_9", "TENSIONS_WITH", 0.5, "phenomenology-praxeology", "objective surface experience tensions with coordinated proactive initiative"),
    # === Phenomenology ↔ Methodology (3) ===
    ("phenomenology.0_0", "methodology.0_0", "COMPATIBLE_WITH", 0.7, "phenomenology-methodology", "objective surface experience informs analytic deductive method"),
    ("phenomenology.9_9", "methodology.9_9", "COMPATIBLE_WITH", 0.6, "phenomenology-methodology", "deep subjective experience structures synthetic inductive method"),
    ("phenomenology.0_0", "methodology.9_9", "TENSIONS_WITH", 0.5, "phenomenology-methodology", "objective surface experience resists synthetic inductive structuring"),
    # === Phenomenology ↔ Semiotics (3) ===
    ("phenomenology.0_0", "semiotics.0_0", "COMPATIBLE_WITH", 0.7, "phenomenology-semiotics", "objective surface experience generates explicit syntactic meaning"),
    ("phenomenology.9_9", "semiotics.9_9", "COMPATIBLE_WITH", 0.7, "phenomenology-semiotics", "deep subjective experience generates implicit semantic meaning"),
    ("phenomenology.0_0", "semiotics.9_9", "TENSIONS_WITH", 0.6, "phenomenology-semiotics", "objective surface experience resists implicit semantic shaping"),
    # === Phenomenology ↔ Hermeneutics (3) ===
    ("phenomenology.0_0", "hermeneutics.0_0", "COMPATIBLE_WITH", 0.6, "phenomenology-hermeneutics", "objective surface experience frames literal author-intent interpretation"),
    ("phenomenology.9_9", "hermeneutics.9_9", "COMPATIBLE_WITH", 0.8, "phenomenology-hermeneutics", "deep subjective experience deepens figurative reader-response interpretation"),
    ("phenomenology.9_9", "hermeneutics.0_0", "TENSIONS_WITH", 0.6, "phenomenology-hermeneutics", "deep subjective experience resists reduction to literal author-intent"),
    # === Phenomenology ↔ Heuristics (3) ===
    ("phenomenology.0_0", "heuristics.0_0", "COMPATIBLE_WITH", 0.6, "phenomenology-heuristics", "objective surface experience informs systematic conservative strategy"),
    ("phenomenology.9_9", "heuristics.9_9", "COMPATIBLE_WITH", 0.6, "phenomenology-heuristics", "deep subjective experience informs intuitive exploratory strategy"),
    ("phenomenology.0_0", "heuristics.9_9", "TENSIONS_WITH", 0.5, "phenomenology-heuristics", "objective surface experience resists intuitive exploratory strategy"),
    # === Praxeology ↔ Methodology (3) ===
    ("praxeology.0_0", "methodology.0_0", "COMPATIBLE_WITH", 0.7, "praxeology-methodology", "individual reactive action requires analytic deductive method"),
    ("praxeology.9_9", "methodology.9_9", "COMPATIBLE_WITH", 0.7, "praxeology-methodology", "coordinated proactive action enables synthetic inductive method"),
    ("praxeology.0_0", "methodology.9_9", "TENSIONS_WITH", 0.6, "praxeology-methodology", "individual reactive action resists synthetic inductive approach"),
    # === Praxeology ↔ Semiotics (3) ===
    ("praxeology.9_9", "semiotics.0_0", "COMPATIBLE_WITH", 0.6, "praxeology-semiotics", "coordinated proactive action communicated through explicit syntactic structures"),
    ("praxeology.0_0", "semiotics.9_9", "TENSIONS_WITH", 0.5, "praxeology-semiotics", "individual reactive action resists implicit semantic communication"),
    ("praxeology.0_9", "semiotics.0_9", "COMPATIBLE_WITH", 0.5, "praxeology-semiotics", "individual proactive action communicates through explicit semantic meaning"),
    # === Praxeology ↔ Hermeneutics (3) ===
    ("praxeology.0_0", "hermeneutics.0_0", "COMPATIBLE_WITH", 0.6, "praxeology-hermeneutics", "individual reactive action interpreted literally as intended"),
    ("praxeology.9_9", "hermeneutics.9_9", "COMPATIBLE_WITH", 0.5, "praxeology-hermeneutics", "coordinated proactive action reinterpreted through figurative reader-response"),
    ("praxeology.0_0", "hermeneutics.9_9", "TENSIONS_WITH", 0.5, "praxeology-hermeneutics", "individual reactive action resists figurative reader reinterpretation"),
    # === Praxeology ↔ Heuristics (3) ===
    ("praxeology.0_0", "heuristics.0_0", "COMPATIBLE_WITH", 0.7, "praxeology-heuristics", "individual reactive action structured by systematic conservative strategy"),
    ("praxeology.9_9", "heuristics.9_9", "COMPATIBLE_WITH", 0.6, "praxeology-heuristics", "coordinated proactive action refined through intuitive exploratory strategy"),
    ("praxeology.0_0", "heuristics.9_9", "TENSIONS_WITH", 0.5, "praxeology-heuristics", "individual reactive action resists intuitive exploratory risk"),
    # === Methodology ↔ Semiotics (3) ===
    ("methodology.0_0", "semiotics.0_0", "COMPATIBLE_WITH", 0.7, "methodology-semiotics", "analytic deductive method produces explicit syntactic signs"),
    ("methodology.9_9", "semiotics.9_9", "COMPATIBLE_WITH", 0.6, "methodology-semiotics", "synthetic inductive method communicates through implicit semantic signs"),
    ("methodology.0_0", "semiotics.9_9", "TENSIONS_WITH", 0.5, "methodology-semiotics", "analytic deductive method resists implicit semantic encoding"),
    # === Methodology ↔ Hermeneutics (3) ===
    ("methodology.0_0", "hermeneutics.0_0", "COMPATIBLE_WITH", 0.8, "methodology-hermeneutics", "analytic deductive method frames literal author-intent interpretation"),
    ("methodology.9_9", "hermeneutics.9_9", "COMPATIBLE_WITH", 0.7, "methodology-hermeneutics", "synthetic inductive method challenges assumptions through figurative reader-response"),
    ("methodology.0_0", "hermeneutics.9_9", "TENSIONS_WITH", 0.6, "methodology-hermeneutics", "analytic deductive method resists figurative reader reinterpretation"),
    # === Methodology ↔ Heuristics (4) ===
    ("methodology.0_0", "heuristics.0_0", "COMPATIBLE_WITH", 0.8, "methodology-heuristics", "analytic deductive method aligns with systematic conservative strategy"),
    ("methodology.9_9", "heuristics.9_9", "COMPATIBLE_WITH", 0.7, "methodology-heuristics", "synthetic inductive method discovers through intuitive exploratory strategy"),
    ("methodology.0_0", "heuristics.9_9", "TENSIONS_WITH", 0.7, "methodology-heuristics", "formal analytic deduction resists informal intuitive exploration"),
    ("methodology.9_9", "heuristics.0_0", "TENSIONS_WITH", 0.5, "methodology-heuristics", "synthetic induction resists systematic conservative constraints"),
    # === Semiotics ↔ Hermeneutics (4) ===
    ("semiotics.0_0", "hermeneutics.0_0", "COMPATIBLE_WITH", 0.8, "semiotics-hermeneutics", "explicit syntactic signs invite literal author-intent interpretation"),
    ("semiotics.9_9", "hermeneutics.9_9", "COMPATIBLE_WITH", 0.8, "semiotics-hermeneutics", "implicit semantic signs generate figurative reader-response interpretation"),
    ("semiotics.0_0", "hermeneutics.9_9", "TENSIONS_WITH", 0.7, "semiotics-hermeneutics", "explicit syntactic signs resist figurative reader reinterpretation"),
    ("semiotics.9_9", "hermeneutics.0_0", "TENSIONS_WITH", 0.7, "semiotics-hermeneutics", "implicit semantic signs resist literal author-intent reading"),
    # === Semiotics ↔ Heuristics (3) ===
    ("semiotics.0_0", "heuristics.0_0", "COMPATIBLE_WITH", 0.6, "semiotics-heuristics", "explicit syntactic signs encode systematic conservative strategies"),
    ("semiotics.9_9", "heuristics.9_9", "COMPATIBLE_WITH", 0.6, "semiotics-heuristics", "implicit semantic signs carry intuitive exploratory adaptations"),
    ("semiotics.0_0", "heuristics.9_9", "TENSIONS_WITH", 0.5, "semiotics-heuristics", "explicit syntactic signs resist intuitive exploratory encoding"),
    # === Hermeneutics ↔ Heuristics (4) ===
    ("hermeneutics.0_0", "heuristics.0_0", "COMPATIBLE_WITH", 0.7, "hermeneutics-heuristics", "literal author-intent interpretation informs systematic conservative strategy"),
    ("hermeneutics.9_9", "heuristics.9_9", "COMPATIBLE_WITH", 0.7, "hermeneutics-heuristics", "figurative reader-response reshapes intuitive exploratory strategy"),
    ("hermeneutics.0_0", "heuristics.9_9", "TENSIONS_WITH", 0.6, "hermeneutics-heuristics", "literal interpretation resists intuitive exploratory reframing"),
    ("hermeneutics.9_9", "heuristics.0_0", "TENSIONS_WITH", 0.5, "hermeneutics-heuristics", "figurative reader-response resists systematic conservative constraints"),
]


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
    """Generate all 1629 canonical edges.

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
            # Keys are sorted so ((0,9),(9,0)) matches regardless of edge direction
            pair_key = tuple(sorted([(ax, ay), (bx, by)]))
            spectrum_q = SPECTRUM_QUESTIONS.get(pair_key)
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

    # 7. CANONICAL_CROSS_BRANCH edges (197)
    for src, tgt, rel, strength, nexus_pair, justification in CANONICAL_CROSS_BRANCH_EDGES:
        edges.append({
            "source_id": src,
            "target_id": tgt,
            "relation": rel,
            "strength": strength,
            "source": "canonical_cross_branch",
            "nexus_pair": nexus_pair,
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
