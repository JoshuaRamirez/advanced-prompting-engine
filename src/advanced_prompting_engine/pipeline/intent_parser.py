"""Stage 1 — Intent Parser: natural language -> partial coordinate.

Authoritative source: CONSTRUCT-v2.md (8-stage forward pass, Stage 1),
ADR-013 (BGE local embedding), ADR-015 (Pluggable Cloud Vector Embeddings).

Supports two execution paths:
  1. Cloud Path (opt-in): Live high-dimensional vector embeddings (OpenAI 3072d,
     Gemini 2048d) projected onto continuous face centroids and axis vectors.
  2. Local Path (default): Pre-computed BGE 1024d GeometricBridge token/phrase lookup.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
import numpy as np

from advanced_prompting_engine.graph.schema import (
    ALL_FACES,
    GRID_SIZE,
    PipelineState,
)

if TYPE_CHECKING:
    from advanced_prompting_engine.math.cloud_bridge import CloudSemanticBridge
    from advanced_prompting_engine.math.semantic import GeometricBridge
    from advanced_prompting_engine.providers.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)

# Minimum face relevance (discriminative) to consider a face actively matched.
# Discriminative scores can be negative; only positive scores indicate above-average relevance.
RELEVANCE_THRESHOLD = 0.0

# Minimum combined confidence (average of x and y axis confidence) to emit a coordinate
CONFIDENCE_THRESHOLD = 0.05

# Stop words for tokenization — functional words that carry no domain signal.
# BGE needs full word forms, so we must filter out common function words,
# pronouns, modals, and auxiliaries that dilute discriminative face relevance
# when left in the token set.
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

    Supports both cloud vector embeddings (OpenAI 3072d, Gemini 2048d) and
    local GeometricBridge pre-computed artifacts.
    """

    def __init__(
        self,
        geometric_bridge: GeometricBridge | None = None,
        embedding_provider: BaseEmbeddingProvider | None = None,
        cloud_bridge: CloudSemanticBridge | None = None,
    ):
        self._bridge = geometric_bridge
        self._provider = embedding_provider
        self._cloud_bridge = cloud_bridge

        # Pre-compute phrase lookup structures from the local bridge
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

        # Try cloud embedding path if active and available
        if (
            self._provider is not None
            and self._provider.provider_name != "local"
            and self._provider.is_available()
            and self._cloud_bridge is not None
            and self._cloud_bridge.is_loaded
        ):
            try:
                intent_vec = self._provider.embed_text(intent)
                if intent_vec is not None:
                    self._execute_cloud(state, intent_vec)
                    return
                logger.debug("Cloud embedding returned None — falling back to local bridge")
            except Exception as e:
                logger.warning("Cloud embedding failed (%s) — falling back to local bridge", e)

        # Default / Fallback: Local GeometricBridge path
        self._execute_local(state, intent)

    def _execute_cloud(self, state: PipelineState, intent_vec: np.ndarray):
        """Execute Stage 1 using high-dimensional cloud vector projections."""
        if self._cloud_bridge is None:
            state.partial_coordinate = {f: None for f in ALL_FACES}
            return

        # Phase 1: Face relevance
        face_scores = self._cloud_bridge.face_relevance(intent_vec)
        raw_disc_scores = dict(face_scores)

        # Phase-aware modulation
        if self._cloud_bridge.has_phase_data:
            phase_weights = self._cloud_bridge.phase_weighting(intent_vec)
            for face in ALL_FACES:
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

        # Phase 2 & 3: Axis projection + scalar-to-grid
        partial: dict[str, dict | None] = {}

        for face in ALL_FACES:
            x_scalar, x_conf = self._cloud_bridge.axis_projection(intent_vec, face, "x")
            y_scalar, y_conf = self._cloud_bridge.axis_projection(intent_vec, face, "y")

            avg_confidence = (x_conf + y_conf) / 2.0

            disc_score = raw_disc_scores.get(face, 0.0)
            if disc_score < RELEVANCE_THRESHOLD and avg_confidence < CONFIDENCE_THRESHOLD:
                partial[face] = None
                continue

            ax_x = self._scalar_to_grid(x_scalar)
            ax_y = self._scalar_to_grid(y_scalar)

            weight = face_weights[face] * (0.7 + 0.3 * avg_confidence)
            weight = max(0.1, min(1.0, weight))

            partial[face] = {
                "x": ax_x,
                "y": ax_y,
                "weight": weight,
                "confidence": avg_confidence,
            }

        state.partial_coordinate = partial

    def _execute_local(self, state: PipelineState, intent: str):
        """Execute Stage 1 using local GeometricBridge pre-computed artifacts."""
        tokens = self._tokenize(intent)

        # Graceful degradation: if bridge not loaded, all faces get None
        if self._bridge is None or not self._bridge.is_loaded:
            state.partial_coordinate = {f: None for f in ALL_FACES}
            return

        # --- Phase 1: Face relevance ---
        face_scores = self._bridge.face_relevance(tokens)
        raw_disc_scores = dict(face_scores)

        # Technique F: Phase-aware modulation of face scores
        if self._bridge.has_phase_data:
            phase_weights = self._bridge.phase_weighting(tokens)
            for face in ALL_FACES:
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

            disc_score = raw_disc_scores.get(face, 0.0)
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
                    x = max(0, min(11, round(0.4 * ax_x + 0.6 * qx)))
                    y = max(0, min(11, round(0.4 * ax_y + 0.6 * qy)))
                else:
                    x, y = ax_x, ax_y
            else:
                x, y = ax_x, ax_y

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
        """Tokenize with greedy longest-match phrase detection."""
        cleaned = text.lower()
        for ch in "?.,;:!'\"()[]{}—-–/":
            cleaned = cleaned.replace(ch, " ")
        raw_words = cleaned.split()

        if not self._phrase_vocab or not raw_words:
            return [w for w in raw_words if w not in _STOP_WORDS and len(w) > 1]

        phrase_stop_words = {"and", "of", "the", "or", "a", "an", "in", "on", "to", "for"}

        tokens: list[str] = []
        i = 0
        n = len(raw_words)

        while i < n:
            matched = False
            max_len = min(self._max_phrase_len, n - i)

            for length in range(max_len, 1, -1):
                window = raw_words[i:i + length]
                surface = " ".join(window)

                canonical = self._surface_to_canonical.get(surface)
                if canonical and canonical in self._phrase_vocab:
                    tokens.append(canonical)
                    i += length
                    matched = True
                    break

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
        """Map a [0, 1] scalar to grid position 0–11 via polarity convention."""
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
