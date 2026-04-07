"""Canonical graph data — generates all face, construct, nexus, and gem nodes.

Authoritative source: CONSTRUCT-v2.md (§3–§14), CONSTRUCT-v2-questions.md.
Contains 144 base question templates, 66 nexus definitions, and all generation
functions for the v2 12-face Construct.

v2 changes from v1:
  - 12 faces (was 10 branches), 144 constructs per face (was 100), 1728 total
  - 66 nexus pairs (was 45) — adds ethics and aesthetics
  - Positional correspondence replaces declared cross-face edges
  - Spectrum meaning derived from sub-dimensions, not separate authored questions
  - 12x12 grid with dual midpoints (positions 5 and 6)
"""

from __future__ import annotations

from advanced_prompting_engine.graph.grid import (
    classify,
    generate_spectrums,
    potency,
)
from advanced_prompting_engine.graph.schema import (
    ALL_FACES,
    CENTRAL_GEM_LINK,
    CUBE_PAIRS,
    DOMAIN_REPLACEMENTS,
    FACE_DEFINITIONS,
    GRID_SIZE,
    HAS_CONSTRUCT,
    NEXUS_SOURCE,
    NEXUS_TARGET,
    NexusTier,
    PRECEDES,
    SPECTRUM_OPPOSITION,
)

# Current canonical version
CANONICAL_VERSION = "2.0.0"


# ---------------------------------------------------------------------------
# Stop words for tag derivation
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


def stem(word: str) -> str:
    """Minimal suffix-stripping stemmer. Consistency > accuracy."""
    if len(word) <= 4:
        return word
    for suffix in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def derive_tags(question: str, face: str, classification: str) -> list[str]:
    """Extract tags from a parameterized question.

    Filters stop words, stems remaining tokens, appends face name and
    classification as trailing tags.
    """
    words = question.lower().replace("?", "").replace(",", "").replace("'", "").split()
    filtered = [w for w in words if w not in STOP_WORDS and len(w) > 1]
    stemmed = list(dict.fromkeys(stem(w) for w in filtered))  # deduplicate, preserve order
    stemmed.append(face)
    stemmed.append(classification)
    return stemmed


# ---------------------------------------------------------------------------
# 144 base questions — indexed by (x, y)
# From CONSTRUCT-v2-questions.md. All use {domain} placeholder for face
# parameterization via DOMAIN_REPLACEMENTS.
# ---------------------------------------------------------------------------

BASE_QUESTIONS: dict[tuple[int, int], str] = {
    # ===================================================================
    # Zone 1: Corners (4 templates)
    # ===================================================================
    (0, 0): "What is the irreducible fixed commitment that {domain} demands before anything else can be built — the foundational given that admits no negotiation and no motion?",
    (11, 0): "What does {domain} look like when its full scope has been mapped and settled — when comprehensiveness itself has become a stable foundation rather than an ongoing effort?",
    (0, 11): "Where does {domain} become most alive in its simplest form — where a single elemental truth refuses to stay still and instead drives continuous transformation?",
    (11, 11): "What emerges when {domain} operates without structural constraint or temporal anchor — when the widest possible understanding and the freest possible movement are recognized as the same thing?",

    # ===================================================================
    # Zone 2: Edge Midpoints (8 templates)
    # ===================================================================
    (5, 0): "When {domain} achieves a settled, fully grounded stance, what form does it take if the nature of that grounding neither simplifies to its root element nor expands to full scope, but rests slightly closer to the foundational?",
    (6, 0): "When {domain} achieves a settled, fully grounded stance, what form does it take if the nature of that grounding neither simplifies to its root element nor expands to full scope, but leans slightly toward broader inclusion?",
    (5, 11): "When {domain} operates at maximum fluidity and openness, what emerges if the kind of thing in motion holds itself in near-equilibrium but tilts slightly toward the elemental and irreducible?",
    (6, 11): "When {domain} operates at maximum fluidity and openness, what emerges if the kind of thing in motion holds itself in near-equilibrium but tilts slightly toward the encompassing and synthetic?",
    (0, 5): "When {domain} is stripped to its most foundational form, what does balanced engagement look like — neither fully anchored nor fully in motion, but inclining slightly toward stability?",
    (0, 6): "When {domain} is stripped to its most foundational form, what does balanced engagement look like — neither fully anchored nor fully in motion, but inclining slightly toward adaptiveness?",
    (11, 5): "When {domain} reaches its most comprehensive and encompassing form, what does balanced engagement look like — neither fully anchored nor fully in motion, but inclining slightly toward stability?",
    (11, 6): "When {domain} reaches its most comprehensive and encompassing form, what does balanced engagement look like — neither fully anchored nor fully in motion, but inclining slightly toward adaptiveness?",

    # ===================================================================
    # Zone 3: Other Edge Points (32 templates)
    # ===================================================================

    # --- Bottom Edge (y=0, fully stable tendency) ---
    (1, 0): "When {domain} is grounded in its most stable disposition, what foundational insight emerges from examining its most elemental forms just as they begin to differentiate?",
    (2, 0): "What does {domain} reveal about bedrock commitments when its constitutive nature remains strongly elemental and its tendency toward change is entirely absent?",
    (3, 0): "At full dispositional stability, what happens in {domain} when its constitutive character shifts from elemental purity toward a moderate blend — what new structural possibility appears at that threshold?",
    (4, 0): "How does {domain} express a moderately elemental nature under conditions of complete stability — what constrained but not minimal form takes shape when no dynamism is present?",
    (7, 0): "When {domain} achieves a moderately comprehensive constitutive character while remaining fully stable, what integrated structure becomes possible precisely because nothing is in motion?",
    (8, 0): "What does {domain} consolidate when its nature is moderately comprehensive and its disposition is locked at maximum stability — what settled breadth of scope defines this position?",
    (9, 0): "Under conditions of total dispositional stability, what does {domain} look like when its constitutive scope is strongly comprehensive but has not yet reached full universality?",
    (10, 0): "What final preparation does {domain} make at the boundary of comprehensive scope — strongly expansive yet fully stable — just before reaching the corner where scope and permanence fuse completely?",

    # --- Top Edge (y=11, fully fluid tendency) ---
    (1, 11): "When {domain} operates at maximum fluidity, what does its most elemental form become when nothing about its disposition is fixed — what irreducible kernel persists through total openness?",
    (2, 11): "What does {domain} disclose when its constitutive character is strongly elemental but its tendency is entirely exploratory — how does a simple nature behave under unrestricted movement?",
    (3, 11): "At full dispositional fluidity, what transitional form does {domain} take when its constitutive character is moderately elemental — neither minimal nor central, yet entirely unanchored?",
    (4, 11): "How does {domain} navigate full fluidity when its constitutive nature is moderately elemental — what emerges from a constrained scope given total freedom of engagement?",
    (7, 11): "When {domain} is moderately comprehensive in nature and fully fluid in disposition, what expansive possibility opens that would collapse under more stable conditions?",
    (8, 11): "What does {domain} explore when its constitutive breadth is moderately comprehensive and no dispositional constraint exists — what synthesis becomes available only through complete openness?",
    (9, 11): "Under maximum fluidity, what does {domain} reveal at strongly comprehensive scope — what near-total integration looks like when every tendency is exploratory and nothing is settled?",
    (10, 11): "What does the penultimate reach of {domain} look like — strongly comprehensive and fully fluid — at the threshold where total scope and total openness are about to converge?",

    # --- Left Edge (x=0, fully elemental nature) ---
    (0, 1): "When {domain} is reduced to its most elemental constitutive form, what does a strongly stable disposition preserve — what endures in the simplest possible structure just after it begins to admit any movement at all?",
    (0, 2): "At fully elemental scope, what does {domain} look like when its dispositional orientation is strongly stable but has moved perceptibly away from total fixity — what slight capacity for engagement appears?",
    (0, 3): "What does {domain} encounter at its most elemental when disposition shifts to moderately stable — when the simplest form must accommodate a genuine, if limited, tendency toward engagement?",
    (0, 4): "How does the most elemental form of {domain} express a moderately stable disposition — what balance between stillness and movement is possible at the narrowest constitutive scope?",
    (0, 7): "When {domain} is fully elemental but moderately fluid in disposition, what does its simplest form look like once real dynamism has entered — what basic structure adapts rather than resists?",
    (0, 8): "At its most elemental, what does {domain} gain from a moderately fluid orientation — how does the irreducible foundation of the domain begin to actively participate in change?",
    (0, 9): "What tension does {domain} carry at fully elemental scope when its disposition is strongly fluid — what happens to the simplest structure when nearly all stability has been released?",
    (0, 10): "When {domain} at its most elemental reaches strongly fluid disposition, what does the final approach toward total openness demand of a form that has no constitutive breadth to draw upon?",

    # --- Right Edge (x=11, fully comprehensive nature) ---
    (11, 1): "When {domain} achieves its most comprehensive constitutive scope, what does a strongly stable disposition anchor — what total breadth looks like when it is nearly as fixed as it can be?",
    (11, 2): "At fully comprehensive scope, what does {domain} express when disposition is strongly stable but admits the first perceptible degrees of movement — what begins to stir within total integration?",
    (11, 3): "How does {domain} at full constitutive comprehensiveness manage a moderately stable disposition — what does total scope look like when it must accommodate genuine but contained engagement?",
    (11, 4): "What does {domain} become when it holds the widest possible constitutive nature under moderately stable conditions — what organized breadth emerges when disposition is more balanced than fixed?",
    (11, 7): "When {domain} is fully comprehensive and moderately fluid, what kind of engagement does total scope undertake once real dynamism shapes how that breadth is deployed?",
    (11, 8): "At maximum constitutive comprehensiveness with moderately fluid disposition, what does {domain} actively pursue — what does total integration look like when it is seeking rather than holding?",
    (11, 9): "What does {domain} risk when its scope is fully comprehensive and its disposition strongly fluid — what strain appears when total breadth operates under nearly unconstrained movement?",
    (11, 10): "At fully comprehensive scope and strongly fluid disposition, what does {domain} look like at the threshold before total openness — the widest possible nature about to release its last dispositional constraint?",

    # ===================================================================
    # Zone 4: Near-Edge Interior (36 templates)
    # ===================================================================

    # --- Bottom Ring (y=1, strongly stable disposition) ---
    (1, 1): "What is the most foundational, nearly irreducible commitment that {domain} makes when operating under conditions of maximal stability?",
    (2, 1): "When {domain} holds its disposition firmly stable, what elementary structural distinction first becomes visible as constitutive scope begins to widen?",
    (3, 1): "How does {domain} begin to differentiate its foundational categories while maintaining an unwavering commitment to grounded engagement?",
    (4, 1): "At what threshold does {domain} shift from purely elemental classification toward moderate structural breadth, while its manner of engagement remains deeply anchored?",
    (5, 1): "When the constitutive character of {domain} reaches its midpoint — neither simple nor expansive — what does a thoroughly stable disposition preserve from collapsing into ambiguity?",
    (6, 1): "How does {domain} sustain coherent identity as its constitutive scope crosses center and begins favoring comprehensiveness, while its dispositional posture refuses to move?",
    (7, 1): "What distinguishes moderately comprehensive stances in {domain} that remain tethered to their most grounded dispositional form?",
    (8, 1): "As {domain} approaches structural breadth, what specific tension arises between expansive classification and a disposition that remains close to its most stable expression?",
    (9, 1): "When {domain} operates at nearly full constitutive scope under conditions of near-complete stability, what does it gain in coverage that it sacrifices in anchoring precision?",
    (10, 1): "What does the broadest feasible characterization within {domain} look like when every dispositional impulse is held just one degree above its most grounded extreme?",

    # --- Top Ring (y=10, strongly fluid disposition) ---
    (1, 10): "What is the most elemental expression {domain} can take when its dispositional orientation is at its most fluid and exploratory?",
    (2, 10): "When {domain} holds its engagement at near-maximum openness, what elementary structural distinction persists as the simplest thing that can still move?",
    (3, 10): "How does {domain} begin to widen its constitutive scope while sustaining the highest feasible degree of dispositional fluidity?",
    (4, 10): "At what point does moderately foundational classification in {domain} create a recognizable form within what is otherwise near-total dispositional openness?",
    (5, 10): "When {domain} is constitutively balanced and dispositionally near its fluid extreme, what kind of center holds amid maximum relational motion?",
    (6, 10): "How does {domain} express a constitutive scope that has just crossed center toward comprehensiveness when its dispositional posture is overwhelmingly exploratory?",
    (7, 10): "What does moderate structural breadth look like in {domain} when the manner of engagement is almost entirely open-ended?",
    (8, 10): "As {domain} nears constitutive comprehensiveness under conditions of near-maximal fluidity, what prevents scope from dissolving into formlessness?",
    (9, 10): "When {domain} operates at nearly full breadth with nearly full dispositional openness, what distinguishes this position from the total integration of the nearby corner?",
    (10, 10): "What does {domain} look like at the widest feasible scope and highest feasible fluidity — one step inside the boundary on both axes — where comprehensiveness and openness almost, but do not quite, fuse?",

    # --- Left Ring (x=1, strongly elemental constitution) ---
    (1, 2): "When {domain} takes its first measurable step away from pure stability while remaining constitutively foundational, what new relational possibility opens?",
    (1, 3): "How does {domain} express its most foundational structural identity when its dispositional orientation has moved into a moderately stable register?",
    (1, 4): "When {domain} is constitutively near-elemental, at what degree of dispositional moderation does the foundational form begin to carry directional intent?",
    (1, 5): "What does {domain} look like at its most structurally foundational when the dispositional axis is perfectly balanced — neither anchored nor exploratory?",
    (1, 6): "When {domain} holds an almost-elemental constitution and its disposition tilts just past center toward fluidity, what subtle reorientation occurs?",
    (1, 7): "How does a strongly foundational stance in {domain} accommodate a moderately fluid disposition without losing its elemental identity?",
    (1, 8): "What tension does {domain} carry when its constitutive character is nearly irreducible but its dispositional orientation approaches strong openness?",
    (1, 9): "When {domain} is constitutively one step from pure foundation and dispositionally one step from pure fluidity, what does that near-diagonal opposition produce?",

    # --- Right Ring (x=10, strongly comprehensive constitution) ---
    (10, 2): "When {domain} holds nearly full constitutive scope but its disposition has only just begun to move from stability, what kind of comprehensive structure remains effectively grounded?",
    (10, 3): "How does {domain} sustain broad constitutive coverage when its dispositional orientation enters a moderately stable range — still anchored but no longer maximally so?",
    (10, 4): "At what point does the moderately stable disposition of {domain} begin to test the structural integrity of a near-comprehensive constitutive stance?",
    (10, 5): "What does {domain} look like at its broadest feasible scope when the dispositional axis is perfectly balanced — neither anchored nor exploratory?",
    (10, 6): "When {domain} operates at nearly full constitutive breadth and its disposition tips just past center toward fluidity, what new vulnerability or capacity appears?",
    (10, 7): "How does broad structural comprehensiveness in {domain} respond when its dispositional orientation reaches a moderately fluid register?",
    (10, 8): "What emerges in {domain} when near-comprehensive scope is paired with a dispositional orientation approaching strong openness — a breadth that is almost ready to move?",
    (10, 9): "When {domain} is constitutively one step from maximum scope and dispositionally one step from maximum fluidity, what distinguishes this near-total position from the corner's full commitment?",

    # ===================================================================
    # Zone 5: Deep Interior (64 templates)
    # ===================================================================

    # --- Row y=2 (strongly stable disposition) ---
    (2, 2): "What foundational commitment does the prompt make about {domain} that it treats as too basic to question, and what would shift if that commitment were withdrawn?",
    (3, 2): "Where does the prompt rely on a settled, elemental understanding of {domain} that quietly constrains the range of responses it can receive?",
    (4, 2): "What grounded but moderately developed assumption about {domain} serves as the load-bearing structure beneath the prompt's intent?",
    (5, 2): "When the prompt holds a stable posture toward {domain} without favoring simplicity or complexity, what balanced foundation does it stand on?",
    (6, 2): "What anchored equilibrium in the prompt's treatment of {domain} might appear neutral but actually forecloses certain lines of inquiry?",
    (7, 2): "Where does the prompt assume a broad but firmly settled view of {domain}, and what would happen if that breadth were forced into motion?",
    (8, 2): "What expansive claim about {domain} does the prompt treat as permanently resolved, and is that resolution warranted?",
    (9, 2): "Where does the prompt presume a comprehensive and stable account of {domain} that risks mistaking completeness for correctness?",

    # --- Row y=3 (moderately stable disposition) ---
    (2, 3): "What elemental aspect of {domain} does the prompt assume will hold steady under moderate pressure, and what kind of pressure would prove it wrong?",
    (3, 3): "Where does the prompt's treatment of {domain} settle into a modest, grounded position that neither reaches nor risks, and what does that caution cost?",
    (4, 3): "What moderately foundational understanding of {domain} does the prompt lean on while maintaining a conservative trajectory?",
    (5, 3): "Where does the prompt strike a balance in its constitutive view of {domain} while maintaining a preference for stability, and what does that combination produce?",
    (6, 3): "What slightly synthetic treatment of {domain} does the prompt pair with a grounded disposition, and does the pairing create tension or coherence?",
    (7, 3): "Where does the prompt adopt a moderately comprehensive view of {domain} while resisting exploratory engagement, and what gets suppressed by that resistance?",
    (8, 3): "What broad structural claim about {domain} does the prompt hold in a relatively settled frame, and what phenomena does that framing exclude?",
    (9, 3): "Where does the prompt assert near-comprehensive scope over {domain} while keeping engagement measured, and what would full fluidity reveal that this posture conceals?",

    # --- Row y=4 (moderately stable disposition) ---
    (2, 4): "What simple, enduring feature of {domain} does the prompt invoke as though it were self-evident, and what interpretive work does that apparent simplicity actually perform?",
    (3, 4): "Where does the prompt take a deliberately modest and steady stance toward {domain} that functions as a constraint it never names?",
    (4, 4): "What moderately foundational and moderately grounded understanding of {domain} forms the quiet center of the prompt's intent?",
    (5, 4): "Where does the prompt hold both the nature and the movement of {domain} in a near-equilibrium that favors groundedness, and what instability is that equilibrium suppressing?",
    (6, 4): "What mildly expansive treatment of {domain} does the prompt stabilize through conservative engagement, and what would destabilizing that engagement reveal?",
    (7, 4): "Where does the prompt build a moderately broad view of {domain} on a moderately stable base, and what does that architecture assume will never change?",
    (8, 4): "What comprehensive but cautiously held position on {domain} does the prompt adopt, and where does caution shade into avoidance?",
    (9, 4): "Where does the prompt claim expansive coverage of {domain} while remaining dispositionally conservative, and what does that combination fail to reach?",

    # --- Row y=5 (balanced disposition) ---
    (2, 5): "What elemental aspect of {domain} does the prompt hold in dynamic balance, neither fixing it in place nor releasing it to open movement?",
    (3, 5): "Where does the prompt treat a relatively simple feature of {domain} with an evenly weighted disposition, and what unexpected depth does that balance uncover?",
    (4, 5): "What moderately foundational view of {domain} does the prompt carry with a disposition equally open to stability and exploration, and what emerges from that openness?",
    (5, 5): "At the point of maximum equilibrium, where neither the nature nor the engagement with {domain} is committed to any pole, what does the prompt actually ask for?",
    (6, 5): "Where does the prompt hold a slightly expansive view of {domain} in dispositional equilibrium, and what would tipping that balance in either direction produce?",
    (7, 5): "What moderately comprehensive account of {domain} does the prompt sustain through balanced engagement, and does the balance serve the breadth or constrain it?",
    (8, 5): "Where does the prompt's broad treatment of {domain} meet an uncommitted disposition, and what does that lack of commitment enable that conviction would not?",
    (9, 5): "What near-comprehensive scope over {domain} does the prompt hold in dispositional balance, and is that balance a genuine center or an indecision?",

    # --- Row y=6 (balanced disposition) ---
    (2, 6): "What foundational element of {domain} does the prompt hold with a disposition tilting faintly toward exploration, and what does that tilt invite?",
    (3, 6): "Where does the prompt take a relatively simple view of {domain} while allowing slightly more fluidity than fixity, and what possibilities does that slight asymmetry open?",
    (4, 6): "What moderately elemental feature of {domain} does the prompt engage with a balanced-to-exploratory stance, and what tensions between depth and movement does that create?",
    (5, 6): "Where does the prompt's centered view of {domain} pair with a disposition leaning faintly toward the fluid, and what does that lean do to the meaning of balance?",
    (6, 6): "What mildly expansive and mildly exploratory treatment of {domain} does the prompt adopt, and what does this gentle double departure from center produce that center itself cannot?",
    (7, 6): "Where does the prompt's moderately broad engagement with {domain} meet a balanced disposition with a slight exploratory edge, and what form of inquiry does that combination privilege?",
    (8, 6): "What broad but not maximal view of {domain} does the prompt hold while allowing engagement to drift toward fluidity, and what does that drift make available?",
    (9, 6): "Where does the prompt claim near-total scope over {domain} while holding its disposition just past equilibrium toward exploration, and what does the prompt expect to find that settled comprehension would miss?",

    # --- Row y=7 (moderately fluid disposition) ---
    (2, 7): "What elemental understanding of {domain} does the prompt set in motion, and what happens when something foundational is treated as if it can move?",
    (3, 7): "Where does the prompt take a modestly developed view of {domain} and give it a moderately exploratory trajectory, and what does that trajectory discover that a settled view would not?",
    (4, 7): "What moderately simple feature of {domain} does the prompt engage with notable fluidity, and does that fluidity enrich the feature or dissolve it?",
    (5, 7): "Where does the prompt balance the constitutive nature of {domain} while adopting a moderately exploratory posture, and what forms of {domain} become visible only through that movement?",
    (6, 7): "What slightly expansive treatment of {domain} does the prompt pursue with genuine exploratory momentum, and what does that momentum carry the prompt toward?",
    (7, 7): "Where does the prompt adopt a moderately comprehensive and moderately fluid engagement with {domain}, and what does this double moderation produce that stronger commitments would obscure?",
    (8, 7): "What broad understanding of {domain} does the prompt explore with active fluidity, and where does the breadth of scope conflict with the openness of movement?",
    (9, 7): "Where does the prompt combine near-comprehensive scope over {domain} with moderately fluid engagement, and what emerges at the boundary between knowing widely and remaining open?",

    # --- Row y=8 (moderately fluid disposition) ---
    (2, 8): "What basic building block of {domain} does the prompt set loose into active exploration, and what does that liberation of a foundational element make possible?",
    (3, 8): "Where does the prompt take a relatively elemental aspect of {domain} and subject it to sustained exploratory pressure, and what transformation does that pressure produce?",
    (4, 8): "What moderately simple view of {domain} does the prompt carry with a strongly exploratory disposition, and what does it mean when the mode of engagement outpaces the scope of the claim?",
    (5, 8): "Where does the prompt hold a balanced constitutive view of {domain} while engaging with pronounced fluidity, and what does the prompt seek through movement that it could not find through commitment?",
    (6, 8): "What mildly expansive treatment of {domain} does the prompt pursue with active exploratory energy, and what new territory does that combination open?",
    (7, 8): "Where does the prompt's moderately comprehensive view of {domain} meet a strongly fluid engagement, and what does this asymmetry between breadth and movement generate?",
    (8, 8): "What broad scope over {domain} does the prompt animate with strong exploratory momentum, and what does the prompt risk losing to that momentum?",
    (9, 8): "Where does the prompt combine near-total comprehension of {domain} with vigorous exploratory engagement, and what becomes visible only when comprehensive understanding is itself set in motion?",

    # --- Row y=9 (strongly fluid disposition) ---
    (2, 9): "What foundational element of {domain} does the prompt release into maximum fluidity, and what happens when something meant to anchor is itself allowed to drift?",
    (3, 9): "Where does the prompt take a modestly developed aspect of {domain} and give it the most exploratory trajectory available, and what does that disproportion between scope and movement reveal?",
    (4, 9): "What moderately elemental feature of {domain} does the prompt engage with strongly fluid disposition, and does the fluidity transform the feature or merely destabilize it?",
    (5, 9): "Where does the prompt hold a balanced view of the nature of {domain} while adopting a strongly exploratory posture, and what does it mean to explore from a center rather than from an edge?",
    (6, 9): "What slightly expansive view of {domain} does the prompt carry into strongly fluid engagement, and what does it discover about {domain} that only sustained openness can reach?",
    (7, 9): "Where does the prompt pursue a moderately comprehensive understanding of {domain} with strongly exploratory energy, and what forms of knowledge emerge only in that forward motion?",
    (8, 9): "What broad account of {domain} does the prompt hold while engaging with near-maximum fluidity, and where does the tension between comprehensive scope and radical openness become productive?",
    (9, 9): "Where does the prompt assert both expansive scope and maximum exploratory engagement with {domain}, and what does it mean when nothing is held back and nothing is held still?",
}


# ---------------------------------------------------------------------------
# 66 nexus pair definitions (undirected)
# 45 original v1 pairs (with 9 axiology pairs updated for v2 evaluative
# framing: Absolute→Relative × Quantitative→Qualitative) plus 21 new pairs
# involving ethics and aesthetics.
# ---------------------------------------------------------------------------

NEXUS_CONTENT: dict[tuple[str, str], str] = {
    # === Original 10-domain pairs (36 non-axiology pairs retained from v1) ===
    ("ontology", "epistemology"): "How does the nature of what exists determine what can be known, and how does knowing reshape what is recognized as existing?",
    ("ontology", "teleology"): "How do existing entities bear purpose, and how does purpose call entities into recognized existence?",
    ("ontology", "phenomenology"): "How does existence present itself to experience, and how does experience constitute what is recognized as real?",
    ("ontology", "praxeology"): "How does the structure of what exists enable or constrain action, and how does action alter what exists?",
    ("ontology", "methodology"): "How does the nature of existence determine which methods of inquiry are valid, and how do methods reveal or construct entities?",
    ("ontology", "semiotics"): "How do existing entities generate signs, and how do signs constitute the recognition of entities?",
    ("ontology", "hermeneutics"): "How does the nature of what exists shape how it is interpreted, and how does interpretation reconstitute what is understood to exist?",
    ("ontology", "heuristics"): "How does the structure of existence determine which problem-solving strategies are viable, and how do strategies reshape perceived reality?",
    ("epistemology", "teleology"): "How does knowledge direct purpose, and how does purpose determine what is worth knowing?",
    ("epistemology", "phenomenology"): "How does knowledge relate to lived experience, and how does experience generate or undermine claims to knowledge?",
    ("epistemology", "praxeology"): "How does knowing inform acting, and how does acting produce or revise knowledge?",
    ("epistemology", "methodology"): "How do justified beliefs determine valid methods, and how do methods produce justified beliefs?",
    ("epistemology", "semiotics"): "How does knowledge encode into signs, and how do signs carry or distort epistemic content?",
    ("epistemology", "hermeneutics"): "How does established knowledge frame interpretation, and how does interpretation challenge or extend knowledge?",
    ("epistemology", "heuristics"): "How does knowledge inform strategy, and how do strategies reveal knowledge that formal methods miss?",
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

    # === Axiology pairs (9 — updated for v2: Absolute→Relative × Quantitative→Qualitative) ===
    ("ontology", "axiology"): "How does the nature of existence ground evaluative criteria, and how do standards of worth determine which entities are recognized as mattering?",
    ("epistemology", "axiology"): "How does justified knowledge determine what is worth valuing, and how do evaluative standards shape what counts as knowledge?",
    ("axiology", "teleology"): "How do evaluative criteria define purpose, and how does purpose reveal which standards of worth are operative?",
    ("axiology", "phenomenology"): "How do evaluative standards shape experience, and how does experience challenge or validate claims of worth?",
    ("axiology", "praxeology"): "How do evaluative criteria motivate action, and how do the outcomes of action revise what is deemed worthy?",
    ("axiology", "methodology"): "How do evaluative standards determine which methods are acceptable, and how do methods produce or challenge value judgments?",
    ("axiology", "semiotics"): "How are evaluative standards communicated through signs, and how do semiotic structures privilege certain criteria of worth?",
    ("axiology", "hermeneutics"): "How do evaluative standards frame interpretation, and how does interpretation reveal hidden evaluative commitments?",
    ("axiology", "heuristics"): "How do evaluative criteria constrain strategy, and how do strategic outcomes reshape standards of worth?",

    # === Ethics pairs (11 — new in v2) ===
    ("ontology", "ethics"): "How does the nature of what exists determine what moral obligations can hold, and how do ethical commitments reshape what is recognized as morally significant?",
    ("epistemology", "ethics"): "How does justified knowledge ground moral judgment, and how do ethical obligations shape what counts as morally relevant knowledge?",
    ("axiology", "ethics"): "How do evaluative standards of worth inform moral duty, and how do ethical obligations challenge or validate claims about what is valuable?",
    ("teleology", "ethics"): "How does purpose frame moral obligation, and how do ethical duties constrain or redirect what purposes may be pursued?",
    ("phenomenology", "ethics"): "How does lived experience give rise to moral awareness, and how do ethical obligations structure what is experienced as morally salient?",
    ("ethics", "praxeology"): "How do moral obligations govern action, and how does action under constraint reveal the practical limits of ethical commitment?",
    ("ethics", "methodology"): "How do ethical obligations constrain permissible methods, and how do methodological choices carry moral implications?",
    ("ethics", "semiotics"): "How are moral obligations communicated through signs, and how do semiotic structures enable or obscure ethical content?",
    ("ethics", "hermeneutics"): "How do ethical commitments frame interpretation, and how does interpretation reveal moral obligations not previously recognized?",
    ("ethics", "heuristics"): "How do moral obligations constrain strategic choice, and how do strategies under uncertainty create new ethical demands?",
    ("ethics", "aesthetics"): "How do moral obligations shape aesthetic judgment, and how does aesthetic recognition reveal or challenge ethical commitments?",

    # === Aesthetics pairs (10 — new in v2, ethics-aesthetics counted above) ===
    ("ontology", "aesthetics"): "How does the nature of what exists determine what can be aesthetically recognized, and how does aesthetic perception reconstitute what is understood to be real?",
    ("epistemology", "aesthetics"): "How does justified knowledge inform aesthetic judgment, and how does aesthetic recognition generate or challenge epistemic claims?",
    ("axiology", "aesthetics"): "How do evaluative standards of worth frame aesthetic recognition, and how does aesthetic experience challenge or refine criteria of value?",
    ("teleology", "aesthetics"): "How does purpose shape aesthetic form, and how does aesthetic recognition reveal purposes not consciously intended?",
    ("phenomenology", "aesthetics"): "How does lived experience give rise to aesthetic recognition, and how does aesthetic form structure what can be experienced?",
    ("aesthetics", "praxeology"): "How does aesthetic recognition shape action, and how does purposeful action generate or destroy aesthetic qualities?",
    ("aesthetics", "methodology"): "How does aesthetic recognition constrain or inspire methodological choices, and how do methods produce or foreclose aesthetic possibilities?",
    ("aesthetics", "semiotics"): "How are aesthetic qualities communicated through signs, and how do semiotic structures enable or limit aesthetic recognition?",
    ("aesthetics", "hermeneutics"): "How does aesthetic form invite interpretation, and how does interpretive practice generate new modes of aesthetic recognition?",
    ("aesthetics", "heuristics"): "How does aesthetic recognition inform strategic judgment, and how do practical strategies reshape what is perceived as aesthetically significant?",
}


# ---------------------------------------------------------------------------
# Central gem content
# ---------------------------------------------------------------------------

CENTRAL_GEM_CONTENT = (
    "What singular coherence emerges when the extremes of existence, knowing, "
    "evaluating, purposing, experiencing, judging morally, recognizing form, "
    "acting, systematizing, communicating, interpreting, and strategizing "
    "are held simultaneously in mutual awareness?"
)


# ---------------------------------------------------------------------------
# Cube face adjacency model (provisional — see CONSTRUCT-v2.md §15.3)
#
# The 6 cube faces are:
#   Face A: ontology / praxeology
#   Face B: epistemology / methodology
#   Face C: axiology / ethics
#   Face D: teleology / heuristics
#   Face E: phenomenology / aesthetics
#   Face F: semiotics / hermeneutics
#
# Opposite face pairs (3):
#   A ↔ C  (being/doing vs valuing/judging)
#   B ↔ D  (knowing/method vs purpose/strategy)
#   E ↔ F  (experience/form vs encoding/decoding)
#
# Adjacency: each face shares an edge with all 4 non-opposite faces.
# ---------------------------------------------------------------------------

_CUBE_FACE_LABELS: dict[str, str] = {
    "ontology": "A", "praxeology": "A",
    "epistemology": "B", "methodology": "B",
    "axiology": "C", "ethics": "C",
    "teleology": "D", "heuristics": "D",
    "phenomenology": "E", "aesthetics": "E",
    "semiotics": "F", "hermeneutics": "F",
}

_OPPOSITE_FACES: set[frozenset[str]] = {
    frozenset({"A", "C"}),
    frozenset({"B", "D"}),
    frozenset({"E", "F"}),
}


def _nexus_tier(face_a: str, face_b: str) -> NexusTier:
    """Determine the geometric tier of a nexus between two faces.

    Returns NexusTier.PAIRED if they share a cube face, OPPOSITE if their
    cube faces are across the cube, ADJACENT otherwise.
    """
    label_a = _CUBE_FACE_LABELS[face_a]
    label_b = _CUBE_FACE_LABELS[face_b]

    if label_a == label_b:
        return NexusTier.PAIRED
    if frozenset({label_a, label_b}) in _OPPOSITE_FACES:
        return NexusTier.OPPOSITE
    return NexusTier.ADJACENT


# ---------------------------------------------------------------------------
# Generation functions
# ---------------------------------------------------------------------------

def generate_face_nodes() -> list[dict]:
    """Generate the 12 face (axiom-layer) nodes."""
    nodes = []
    for i, face in enumerate(ALL_FACES):
        defn = FACE_DEFINITIONS[face]
        nodes.append({
            "id": face,
            "type": "face",
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


def generate_constructs(face: str) -> list[dict]:
    """Generate 144 construct nodes for a single face.

    Each node gets a parameterized question from BASE_QUESTIONS, with {domain}
    replaced by the face's DOMAIN_REPLACEMENTS string.
    """
    domain = DOMAIN_REPLACEMENTS[face]
    nodes = []

    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            base_q = BASE_QUESTIONS.get((x, y))
            if base_q is None:
                raise ValueError(
                    f"Missing base question for position ({x}, {y})"
                )

            question = base_q.replace("{domain}", domain)
            cls = classify(x, y)
            pot = potency(x, y)
            tags = derive_tags(question, face, cls)

            nodes.append({
                "id": f"{face}.{x}_{y}",
                "type": "construct",
                "tier": 2,
                "face": face,
                "x": x,
                "y": y,
                "classification": cls,
                "potency": pot,
                "question": question,
                "description": f"{cls.title()} construct at ({x},{y}) in {face}: {question}",
                "tags": tags,
                "spectrum_ids": [],  # populated during edge generation
                "condensed_gems": [],
                "provenance": "canonical",
                "mutable": False,
            })

    return nodes


def generate_precedes_edges() -> list[dict]:
    """Generate the 11 PRECEDES edges from the causal ordering of ALL_FACES."""
    edges: list[dict] = []
    for i in range(len(ALL_FACES) - 1):
        edges.append({
            "source_id": ALL_FACES[i],
            "target_id": ALL_FACES[i + 1],
            "relation": PRECEDES,
        })
    return edges


def generate_nexus_nodes() -> tuple[list[dict], list[dict]]:
    """Generate 66 nexus nodes plus 132 directional edges.

    Each undirected nexus pair produces:
      - 1 nexus node (id: nexus.source.target, canonical sorted order)
      - 2 NEXUS_SOURCE edges (nexus → each face)
      - 2 NEXUS_TARGET edges (nexus → each face, reversed direction)
    Actually, following v1 convention: each pair produces 2 directional nexus
    nodes (A→B and B→A), each with a NEXUS_SOURCE and NEXUS_TARGET edge.

    Returns (nodes, edges).
    """
    nodes: list[dict] = []
    edges: list[dict] = []

    for (face_a, face_b), content in NEXUS_CONTENT.items():
        tier = _nexus_tier(face_a, face_b)

        # A→B direction
        nid_ab = f"nexus.{face_a}.{face_b}"
        nodes.append({
            "id": nid_ab,
            "type": "nexus",
            "source_face": face_a,
            "target_face": face_b,
            "content": content,
            "cube_tier": tier.value,
            "provenance": "canonical",
            "mutable": False,
        })
        edges.append({
            "source_id": nid_ab,
            "target_id": face_a,
            "relation": NEXUS_SOURCE,
        })
        edges.append({
            "source_id": nid_ab,
            "target_id": face_b,
            "relation": NEXUS_TARGET,
        })

        # B→A direction (same content, reversed source/target)
        nid_ba = f"nexus.{face_b}.{face_a}"
        nodes.append({
            "id": nid_ba,
            "type": "nexus",
            "source_face": face_b,
            "target_face": face_a,
            "content": content,
            "cube_tier": tier.value,
            "provenance": "canonical",
            "mutable": False,
        })
        edges.append({
            "source_id": nid_ba,
            "target_id": face_b,
            "relation": NEXUS_SOURCE,
        })
        edges.append({
            "source_id": nid_ba,
            "target_id": face_a,
            "relation": NEXUS_TARGET,
        })

    return nodes, edges


def generate_central_gem() -> tuple[dict, list[dict]]:
    """Generate the single central gem node and its 12 CENTRAL_GEM_LINK edges.

    One link per face (not per nexus) — the central gem connects to each face
    directly.

    Returns (gem_node, edges).
    """
    gem = {
        "id": "central_gem",
        "type": "central_gem",
        "content": CENTRAL_GEM_CONTENT,
        "provenance": "canonical",
        "mutable": False,
    }

    edges: list[dict] = []
    for face in ALL_FACES:
        edges.append({
            "source_id": "central_gem",
            "target_id": face,
            "relation": CENTRAL_GEM_LINK,
        })

    return gem, edges


def generate_spectrum_edges(face: str) -> list[dict]:
    """Generate SPECTRUM_OPPOSITION edges for a single face.

    Delegates to grid.generate_spectrums() for the geometric derivation.
    """
    edges: list[dict] = []
    spectrums = generate_spectrums(face)

    for sid, a_id, b_id in spectrums:
        edges.append({
            "source_id": a_id,
            "target_id": b_id,
            "relation": SPECTRUM_OPPOSITION,
            "spectrum_id": sid,
            "strength": 0.6,
            "source": "geometric",
        })

    return edges


def build_canonical_graph() -> tuple[list[dict], list[dict]]:
    """Orchestrate generation of all canonical nodes and edges.

    Returns (nodes, edges) ready for SqliteStore.initialize_canonical().
    """
    all_nodes: list[dict] = []
    all_edges: list[dict] = []

    # 1. Face nodes (12)
    face_nodes = generate_face_nodes()
    all_nodes.extend(face_nodes)

    # 2. Construct nodes (144 per face × 12 faces = 1728)
    construct_index: dict[str, dict] = {}
    for face in ALL_FACES:
        constructs = generate_constructs(face)
        all_nodes.extend(constructs)
        for c in constructs:
            construct_index[c["id"]] = c

    # 3. HAS_CONSTRUCT edges (1728)
    for face in ALL_FACES:
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                all_edges.append({
                    "source_id": face,
                    "target_id": f"{face}.{x}_{y}",
                    "relation": HAS_CONSTRUCT,
                })

    # 4. PRECEDES edges (11)
    all_edges.extend(generate_precedes_edges())

    # 5. SPECTRUM_OPPOSITION edges (22 per face × 12 faces = 264)
    for face in ALL_FACES:
        spectrum_edges = generate_spectrum_edges(face)
        all_edges.extend(spectrum_edges)
        # Populate spectrum_ids on construct nodes
        for edge in spectrum_edges:
            sid = edge["spectrum_id"]
            for node_id in (edge["source_id"], edge["target_id"]):
                if node_id in construct_index:
                    construct_index[node_id]["spectrum_ids"].append(sid)

    # 6. Nexus nodes (132) and edges (264)
    nexus_nodes, nexus_edges = generate_nexus_nodes()
    all_nodes.extend(nexus_nodes)
    all_edges.extend(nexus_edges)

    # 7. Central gem node (1) and edges (12)
    gem_node, gem_edges = generate_central_gem()
    all_nodes.append(gem_node)
    all_edges.extend(gem_edges)

    return all_nodes, all_edges
