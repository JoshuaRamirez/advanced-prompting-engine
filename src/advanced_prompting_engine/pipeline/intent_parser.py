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

    Enhanced with greedy longest-match phrase detection: trigrams are checked
    before bigrams before unigrams. Matched phrases consume their component
    words (no double-counting).
    """

    def __init__(self, geometric_bridge):
        self._bridge = geometric_bridge
        # Pre-compute phrase lookup structures from the bridge
        self._phrase_vocab: set[str] = set()
        self._surface_to_canonical: dict[str, str] = {}
        self._max_phrase_len: int = 0
        if geometric_bridge is not None and geometric_bridge.is_loaded:
            self._phrase_vocab = geometric_bridge.phrase_keys
            self._surface_to_canonical = geometric_bridge.surface_to_canonical
            if self._phrase_vocab:
                self._max_phrase_len = max(
                    len(p.split()) for p in self._phrase_vocab
                )

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

        # Technique F: Phase-aware modulation of face scores
        if self._bridge.has_phase_data:
            phase_weights = self._bridge.phase_weighting(tokens)
            for face in ALL_FACES:
                # Phase provides a 30% modulation, not a replacement
                face_scores[face] *= (0.7 + 0.3 * phase_weights.get(face, 0.5))

        # Normalize face scores to weights in [0.1, 1.0]
        score_values = list(face_scores.values())
        min_score = min(score_values) if score_values else 0.0
        max_score = max(score_values) if score_values else 0.0
        score_range = max_score - min_score

        face_weights: dict[str, float] = {}
        for face in ALL_FACES:
            raw_score = face_scores.get(face, 0.0)
            if score_range > 1e-9:
                normalized = (raw_score - min_score) / score_range
            else:
                normalized = 0.5
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

            ax_x = self._scalar_to_grid(x_scalar)
            ax_y = self._scalar_to_grid(y_scalar)

            # Technique D: Blend axis projection with question-matched position
            if self._bridge.has_question_data:
                q_pos = self._bridge.question_position(tokens, face)
                if q_pos is not None:
                    qx, qy = q_pos
                    # Question match gets higher weight (0.6) — carries
                    # position-specific vocabulary from 1728 construction questions
                    x = max(0, min(11, round(0.4 * ax_x + 0.6 * qx)))
                    y = max(0, min(11, round(0.4 * ax_y + 0.6 * qy)))
                else:
                    x, y = ax_x, ax_y
            else:
                x, y = ax_x, ax_y

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
        """Tokenize with greedy longest-match phrase detection.

        Processing order:
          1. Lowercase, strip punctuation, split into raw words
          2. Forward scan with greedy longest-match: for each position, try
             trigrams then bigrams (both canonical and surface forms). Matched
             phrases consume their component words.
          3. Unmatched words pass through standard stop-word filtering.

        Phrases are emitted as their canonical form (stop words already removed
        at build time). Component words of matched phrases are NOT emitted
        individually — no double-counting.
        """
        cleaned = text.lower()
        for ch in "?.,;:!'\"()[]{}—-–/":
            cleaned = cleaned.replace(ch, " ")
        raw_words = cleaned.split()

        if not self._phrase_vocab or not raw_words:
            return [w for w in raw_words if w not in _STOP_WORDS and len(w) > 1]

        # Phase stop words used during build for canonical forms
        phrase_stop_words = {"and", "of", "the", "or", "a", "an", "in", "on", "to", "for"}

        tokens: list[str] = []
        i = 0
        n = len(raw_words)

        while i < n:
            matched = False
            # Try longest phrases first (up to max_phrase_len words)
            max_len = min(self._max_phrase_len, n - i)

            for length in range(max_len, 1, -1):
                window = raw_words[i:i + length]
                surface = " ".join(window)

                # Check surface form -> canonical mapping
                canonical = self._surface_to_canonical.get(surface)
                if canonical and canonical in self._phrase_vocab:
                    tokens.append(canonical)
                    i += length
                    matched = True
                    break

                # Check canonical form directly (stop words removed from window)
                canonical_words = [
                    w for w in window if w not in phrase_stop_words
                ]
                if len(canonical_words) >= 2:
                    canonical = " ".join(canonical_words)
                    if canonical in self._phrase_vocab:
                        tokens.append(canonical)
                        i += length
                        matched = True
                        break

            if not matched:
                w = raw_words[i]
                if w not in _STOP_WORDS and len(w) > 1:
                    tokens.append(w)
                i += 1

        return tokens

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
