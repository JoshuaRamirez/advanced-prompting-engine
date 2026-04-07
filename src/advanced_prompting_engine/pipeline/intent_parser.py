"""Stage 1 — Intent Parser: natural language -> partial coordinate.

Authoritative source: CONSTRUCT-v2.md (8-stage forward pass, Stage 1).
Two-phase matching:
  Phase 1: Determine face relevance by matching intent against face
           core questions and domain terms.
  Phase 2: Within each face, find the best grid position via tag overlap
           and per-face TF-IDF.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.canonical import stem
from advanced_prompting_engine.graph.schema import (
    ALL_FACES,
    DOMAIN_REPLACEMENTS,
    GRID_SIZE,
    PipelineState,
)

MATCH_THRESHOLD = 0.03  # lowered for v2: 144 parameterized templates produce lower tag/TF-IDF overlap

# Stop words for tokenization (same as tag derivation)
_STOP_WORDS = frozenset({
    "what", "is", "the", "of", "a", "an", "at", "in", "from", "how", "does",
    "do", "that", "this", "which", "for", "to", "and", "or", "by", "with",
    "its", "are", "be", "into", "as", "when", "where", "can", "has", "have",
    "through", "between", "within", "upon", "along", "across",
})

# Face semantic keywords — terms that signal relevance to a specific face
# beyond just the face name. Domain-specific, not structural.
# Include common inflections (singular + plural + gerund) to guard against
# stemmer inconsistency (e.g., stem("duty")="duty" but stem("duties")="duti").
def _build_keywords(*words: str) -> set[str]:
    """Stem each word and collect all stems into a set."""
    return {stem(w) for w in words}

_FACE_KEYWORDS: dict[str, set[str]] = {
    "ontology": _build_keywords(
        "entity", "entities", "exist", "exists", "existence", "existing",
        "real", "reality", "being", "beings", "object", "objects",
        "structure", "structures", "category", "categories",
        "relationship", "relationships", "boundary", "boundaries",
        "hierarchy", "component", "thing", "things", "nature", "essence",
    ),
    "epistemology": _build_keywords(
        "know", "knows", "knowing", "knowledge", "known",
        "truth", "truths", "true", "verify", "verification", "verified",
        "evidence", "proof", "proofs", "belief", "beliefs", "believe",
        "justify", "justification", "justified",
        "valid", "validity", "certain", "certainty",
        "empirical", "rational", "fact", "facts", "correct", "correctness",
    ),
    "axiology": _build_keywords(
        "value", "values", "valued", "valuing",
        "worth", "worthy", "good", "quality", "qualities",
        "evaluate", "evaluates", "evaluation", "criteria", "criterion",
        "measure", "measures", "rank", "ranking", "priority", "priorities",
        "standard", "standards", "merit", "significant", "significance",
    ),
    "teleology": _build_keywords(
        "purpose", "purposes", "purposeful",
        "goal", "goals", "end", "ends", "aim", "aims",
        "target", "targets", "outcome", "outcomes", "result", "results",
        "intent", "intention", "intentions", "direct", "direction",
        "achieve", "achievement", "objective", "objectives",
        "why", "reason", "reasons", "cause", "causes",
    ),
    "phenomenology": _build_keywords(
        "experience", "experiences", "experiencing", "experiential",
        "conscious", "consciousness", "perceive", "perception", "perceived",
        "feel", "feeling", "feelings", "aware", "awareness",
        "sense", "senses", "sensing", "sensory",
        "interact", "interaction", "interactions",
        "user", "gesture", "interface", "subjective", "subjectivity",
        "represent", "representation", "present", "flow",
    ),
    "ethics": _build_keywords(
        "obligation", "obligations", "obligated",
        "duty", "duties", "moral", "morals", "morality", "morally",
        "right", "rights", "wrong", "wrongs",
        "permissible", "impermissible", "permission",
        "forbidden", "responsible", "responsibility", "responsibilities",
        "accountable", "accountability",
        "fair", "fairness", "just", "justice", "harm", "harms", "harmful",
        "consent", "trust", "ethical", "unethical",
    ),
    "aesthetics": _build_keywords(
        "beauty", "beautiful", "form", "forms", "formal",
        "elegance", "elegant", "harmony", "harmonious",
        "proportion", "proportional", "style", "styles", "stylistic",
        "taste", "sensory", "perception", "perceptual",
        "design", "designs", "artistic", "art", "arts",
        "grace", "graceful", "sublime", "sublimity", "ugly", "ugliness",
    ),
    "praxeology": _build_keywords(
        "action", "actions", "behavior", "behaviors", "behavioural",
        "act", "acts", "acting", "do", "doing",
        "perform", "performance", "execute", "execution",
        "practice", "practices", "practical",
        "delegate", "invoke", "response", "responses", "respond",
        "initiative", "coordinate", "coordination",
        "react", "reactive", "operate", "operation",
    ),
    "methodology": _build_keywords(
        "method", "methods", "methodical", "methodology", "methodologies",
        "process", "processes", "system", "systems", "systematic", "systematically",
        "approach", "approaches", "technique", "techniques",
        "procedure", "procedures", "procedural",
        "workflow", "framework", "frameworks",
        "construct", "design", "build", "building",
        "test", "testing", "analyze", "analysis", "analytical",
        "iterate", "iteration",
    ),
    "semiotics": _build_keywords(
        "sign", "signs", "signal", "signals", "signaling",
        "meaning", "meanings", "meaningful",
        "communicate", "communicates", "communication",
        "message", "messages", "encode", "encoding", "encoded",
        "decode", "decoding", "symbol", "symbols", "symbolic",
        "semantic", "semantics", "syntax", "syntactic",
        "format", "payload", "convention", "conventions",
    ),
    "hermeneutics": _build_keywords(
        "interpret", "interprets", "interpretation", "interpretive",
        "understand", "understanding", "understood",
        "ambiguity", "ambiguous", "context", "contextual",
        "read", "reading", "translate", "translation",
        "clarify", "clarification", "meaning", "meanings",
        "frame", "framing", "perspective", "perspectives",
        "narrative", "narratives", "exegesis", "text", "texts", "textual",
        "nuance", "nuances", "nuanced",
    ),
    "heuristics": _build_keywords(
        "strategy", "strategies", "strategic",
        "heuristic", "heuristics", "solve", "solving", "solution",
        "problem", "problems", "adapt", "adaptation", "adaptive",
        "fallback", "pragmatic", "pragmatism",
        "rule", "rules", "shortcut", "shortcuts",
        "approximate", "approximation", "trial", "error",
        "explore", "exploration", "exploratory", "robust", "robustness",
    ),
}


class IntentParser:
    """Stage 1: Map natural language intent to partial grid coordinates."""

    def __init__(self, tfidf_cache, query_layer):
        self._tfidf = tfidf_cache
        self._query = query_layer

    def execute(self, state: PipelineState):
        raw = state.raw_input

        # Bypass: pre-formed coordinate dict
        if isinstance(raw, dict):
            self._validate_coordinate(raw)
            state.partial_coordinate = raw
            return

        # Natural language path
        intent = str(raw).strip()
        if not intent:
            state.partial_coordinate = {f: None for f in ALL_FACES}
            return

        tokens = self._tokenize(intent)

        # --- Phase 1: Face relevance ---
        face_relevance: dict[str, float] = {}
        for face in ALL_FACES:
            keywords = _FACE_KEYWORDS.get(face, set())
            face_name_stem = stem(face)
            domain_stems = {stem(w) for w in DOMAIN_REPLACEMENTS[face].split()}

            keyword_overlap = len(tokens & keywords)
            name_match = 1.0 if face_name_stem in tokens else 0.0
            domain_match = len(tokens & domain_stems)

            relevance = keyword_overlap * 1.0 + name_match * 2.0 + domain_match * 1.5
            face_relevance[face] = relevance

        max_relevance = max(face_relevance.values()) if face_relevance else 0.0

        # --- Phase 2: Position matching within each face ---
        partial: dict[str, dict | None] = {}
        face_matched_tokens: dict[str, list[str]] = {f: [] for f in ALL_FACES}

        for face in ALL_FACES:
            relevance = face_relevance[face]

            # Per-face TF-IDF for position selection
            face_tfidf = {
                cid: sim for cid, sim in self._tfidf.query_face(intent, face)
            }

            best_id = None
            best_score = 0.0

            constructs = self._query.list_constructs(face)
            for c in constructs:
                # Tag score
                c_tags = set(c.get("tags", []))
                if not c_tags:
                    tag_score = 0.0
                else:
                    overlap = len(tokens & c_tags)
                    tag_score = overlap / len(c_tags)

                # TF-IDF score (per-face)
                tfidf_score = face_tfidf.get(c["id"], 0.0)

                combined = tag_score * 0.6 + tfidf_score * 0.4

                if combined > best_score:
                    best_score = combined
                    best_id = c["id"]

            if best_score >= MATCH_THRESHOLD and best_id is not None:
                pos_part = best_id.split(".")[1]
                x, y = map(int, pos_part.split("_"))

                # Weight from face relevance (Phase 1) + match confidence (Phase 2)
                if max_relevance > 0:
                    relevance_weight = relevance / max_relevance
                else:
                    relevance_weight = 0.0

                weight = max(0.1, (relevance_weight * 0.7 + best_score * 0.3))

                # Track matched tokens
                c_data = self._query.get_construct_by_id(best_id)
                if c_data:
                    c_tags = set(c_data.get("tags", []))
                    matched = list(tokens & c_tags)
                    face_matched_tokens[face] = matched

                partial[face] = {
                    "x": x,
                    "y": y,
                    "weight": weight,
                    "confidence": best_score,
                }
            else:
                partial[face] = None

        # Phase 3: Diversification — if low-relevance faces landed on the
        # same position as high-relevance ones, mark them as None so the
        # coordinate resolver can fill them with structurally appropriate defaults.
        if max_relevance > 0:
            filled = {f: v for f, v in partial.items() if v is not None}
            if filled:
                from collections import Counter
                pos_counts = Counter((v["x"], v["y"]) for v in filled.values())
                most_common_pos, most_common_count = pos_counts.most_common(1)[0]

                # If > 60% of faces share the same position, it is a degenerate result.
                # Null out low-relevance faces so coordinate resolver can diversify.
                if most_common_count > len(filled) * 0.6:
                    relevance_threshold = max_relevance * 0.3
                    for face in list(partial.keys()):
                        if partial[face] is None:
                            continue
                        entry = partial[face]
                        if (entry["x"], entry["y"]) == most_common_pos:
                            if face_relevance[face] < relevance_threshold:
                                partial[face] = None

        state.partial_coordinate = partial

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize and stem to match the stemmed tags in canonical constructs."""
        words = text.lower().replace("?", "").replace(",", "").replace("'", "").split()
        return {stem(w) for w in words if w not in _STOP_WORDS and len(w) > 1}

    def _validate_coordinate(self, coord: dict):
        max_coord = GRID_SIZE - 1
        for face in ALL_FACES:
            if face not in coord:
                raise ValueError(f"Missing face {face!r} in coordinate")
            entry = coord[face]
            if entry is not None:
                if not isinstance(entry, dict):
                    raise ValueError(f"Face {face!r} entry must be dict or None")
                for key in ("x", "y", "weight"):
                    if key not in entry:
                        raise ValueError(f"Face {face!r} missing {key!r}")
                if not (0 <= entry["x"] <= max_coord and 0 <= entry["y"] <= max_coord):
                    raise ValueError(
                        f"Face {face!r} position ({entry['x']}, {entry['y']}) "
                        f"out of range 0-{max_coord}"
                    )
