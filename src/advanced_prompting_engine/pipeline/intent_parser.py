"""Stage 1 — Intent Parser: natural language -> partial coordinate.

Authoritative source: CONSTRUCT-v2.md (8-stage forward pass, Stage 1).
Geometry-integral parsing built from the Construct's own authored layers:

  Phase 1: Face relevance via GeometricBridge discriminative face similarity
           (IDF-weighted GloVe cosine to authored-layer centroids minus mean)
  Phase 2: Axis projection via GeometricBridge pre-computed direction vectors
           (IDF-weighted dot product onto high_pole - low_pole direction)
  Phase 3: Scalar-to-grid mapping via polarity convention (0.0 -> 0, 1.0 -> 11)
"""

from __future__ import annotations

from advanced_prompting_engine.graph.schema import (
    ALL_FACES,
    GRID_SIZE,
    PipelineState,
)

# Minimum face relevance (discriminative) to consider a face actively matched.
# Discriminative scores can be negative; only positive scores indicate above-average relevance.
RELEVANCE_THRESHOLD = 0.0

# Minimum combined confidence (average of x and y axis confidence) to emit a coordinate
CONFIDENCE_THRESHOLD = 0.05

# Stop words for tokenization — functional words that carry no domain signal in GloVe space.
# Expanded beyond the original stemmed set: GloVe needs full word forms, so we must
# filter out common function words, pronouns, modals, and auxiliaries that dilute
# discriminative face relevance when left in the token set.
_STOP_WORDS = frozenset({
    # Determiners and articles
    "a", "an", "the", "this", "that", "these", "those",
    # Prepositions
    "at", "in", "on", "of", "from", "to", "into", "as", "by", "with",
    "through", "between", "within", "upon", "along", "across", "about",
    "over", "under", "after", "before", "during", "against", "toward",
    "towards", "among", "around", "without",
    # Conjunctions
    "and", "or", "but", "nor", "yet", "so", "if", "then", "than",
    # Pronouns
    "it", "its", "he", "she", "we", "us", "me", "my", "our", "your",
    "you", "they", "them", "their", "his", "her",
    # Question words
    "what", "how", "which", "where", "when", "who", "whom", "why",
    # Auxiliaries and modals
    "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had", "having",
    "do", "does", "did", "doing",
    "can", "could", "will", "would", "shall", "should",
    "may", "might", "must", "need", "ought",
    # Common low-signal verbs and adverbs
    "not", "no", "also", "just", "only", "very", "too", "more", "most",
    "some", "any", "all", "each", "every", "both", "such",
    "here", "there", "now", "already", "still", "even",
})


class IntentParser:
    """Stage 1: Map natural language intent to partial grid coordinates.

    Uses the GeometricBridge to determine face relevance and axis positions
    from pre-computed GloVe-derived artifacts. No TF-IDF cache or query layer
    needed — all geometry is baked into the bridge at build time.
    """

    def __init__(self, geometric_bridge):
        self._bridge = geometric_bridge

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

        # Graceful degradation: if bridge not loaded, all faces get None
        if self._bridge is None or not self._bridge.is_loaded:
            state.partial_coordinate = {f: None for f in ALL_FACES}
            return

        # --- Phase 1: Face relevance ---
        face_scores = self._bridge.face_relevance(tokens)

        # Normalize face scores to weights in [0.1, 1.0]
        # Discriminative scores can be negative; shift so minimum maps to 0
        score_values = list(face_scores.values())
        min_score = min(score_values) if score_values else 0.0
        max_score = max(score_values) if score_values else 0.0
        score_range = max_score - min_score

        face_weights: dict[str, float] = {}
        for face in ALL_FACES:
            raw_score = face_scores.get(face, 0.0)
            if score_range > 1e-9:
                normalized = (raw_score - min_score) / score_range  # [0, 1]
            else:
                normalized = 0.5  # uniform if no differentiation
            # Map to [0.1, 1.0] — every face gets at least 0.1 base weight
            face_weights[face] = 0.1 + 0.9 * normalized

        # --- Phase 2 & 3: Axis projection + scalar-to-grid ---
        partial: dict[str, dict | None] = {}

        for face in ALL_FACES:
            x_scalar, x_conf = self._bridge.axis_projection(tokens, face, "x")
            y_scalar, y_conf = self._bridge.axis_projection(tokens, face, "y")

            avg_confidence = (x_conf + y_conf) / 2.0

            # If discriminative relevance is below threshold AND confidence is
            # very low, let coordinate resolver fill this face
            disc_score = face_scores.get(face, 0.0)
            if disc_score < RELEVANCE_THRESHOLD and avg_confidence < CONFIDENCE_THRESHOLD:
                partial[face] = None
                continue

            x = self._scalar_to_grid(x_scalar)
            y = self._scalar_to_grid(y_scalar)

            # Weight combines face relevance (Phase 1) with axis confidence (Phase 2)
            weight = face_weights[face] * (0.7 + 0.3 * avg_confidence)
            weight = max(0.1, min(1.0, weight))

            partial[face] = {
                "x": x,
                "y": y,
                "weight": weight,
                "confidence": avg_confidence,
            }

        state.partial_coordinate = partial

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize: lowercased, unstemmed, stop-word filtered.

        GloVe needs actual word forms, not stems. Punctuation is stripped
        but word morphology is preserved.
        """
        cleaned = text.lower()
        for ch in "?.,;:!'\"()[]{}—-–/":
            cleaned = cleaned.replace(ch, " ")
        words = cleaned.split()
        return [w for w in words if w not in _STOP_WORDS and len(w) > 1]

    def _scalar_to_grid(self, scalar: float) -> int:
        """Map a [0, 1] scalar to grid position 0–11 via polarity convention.

        0.0 (low pole) -> 0
        1.0 (high pole) -> 11
        Linear mapping with clamping.
        """
        max_coord = GRID_SIZE - 1
        pos = round(scalar * max_coord)
        return max(0, min(max_coord, pos))

    def _validate_coordinate(self, coord: dict):
        """Validate a pre-formed coordinate dictionary."""
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
