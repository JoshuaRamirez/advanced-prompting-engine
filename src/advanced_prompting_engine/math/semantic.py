"""Geometric bridge — loads pre-computed BGE-derived face relevance and axis
projections at runtime (ADR-013).

The artifacts are generated offline by scripts/build_semantic_bridge.py using
BAAI/bge-large-en-v1.5 at native 1024 dimensions. At runtime, this module
loads pre-computed arrays from the package data directory and provides fast
numpy-only lookups:

  1. face_relevance(tokens) — IDF²-weighted discriminative face similarity
  2. axis_projection(tokens, face, axis) — IDF-weighted axis projection [0,1]
  3. phase_weighting(tokens) — IDF-weighted phase similarity per face (Technique F)
  4. question_position(tokens, face) — IDF-weighted question-matched (x,y) (Technique D)

Enhanced with:
  - Contextual disambiguation for polysemous words (Alg 2)
  - N-gram/phrase vocabulary for multi-word lookups (Alg 3)
  - Phase-aware face weighting from phase centroids (Technique F)
  - Per-face question position matching (Technique D)

No embedding model or ML library is needed at runtime — only numpy. If the
artifact files are absent (developer has not run the build script), the
bridge reports is_loaded=False and all queries degrade gracefully.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from advanced_prompting_engine.graph.schema import ALL_FACES, CUBE_PAIRS, FACE_PHASES


class GeometricBridge:
    """Pre-computed word-to-face similarity and axis projection lookup.

    Loaded artifacts:
        _face_sim: shape (vocab_size, 12) — discriminative face similarity
                   (cosine to centroid minus mean across centroids)
        _axis_proj: shape (vocab_size, 24) — pre-normalized axis projections
                    in [0,1] where 0=low pole, 1=high pole
        _idf: shape (vocab_size,) — IDF-like weights from frequency rank
        _vocab: word (lowercase, unstemmed) -> row index
        _faces: face names in column order

    Disambiguation:
        _disambig_face_sim: shape (N_senses, 12)
        _disambig_axis_proj: shape (N_senses, 24)
        _disambig_meta: {trigger_word: [{context_words, sense_idx, override_type, threshold}]}

    Phrases:
        _phrase_keys: set of canonical phrase strings in the vocabulary
        _surface_to_canonical: surface form -> canonical form for phrases with stop words
    """

    def __init__(self):
        self._face_sim: np.ndarray | None = None
        self._axis_proj: np.ndarray | None = None
        self._idf: np.ndarray | None = None
        self._vocab: dict[str, int] = {}
        self._faces: list[str] = []
        # Disambiguation
        self._disambig_face_sim: np.ndarray | None = None
        self._disambig_axis_proj: np.ndarray | None = None
        self._disambig_meta: dict[str, list[dict]] = {}
        # Phrases
        self._phrase_keys: set[str] = set()
        self._surface_to_canonical: dict[str, str] = {}
        # Phase weighting (Technique F)
        self._phase_centroids: np.ndarray | None = None
        self._word_phase_sim: np.ndarray | None = None
        self._phase_names: list[str] = []
        # Question position matching (Technique D)
        self._word_question_x: np.ndarray | None = None
        self._word_question_y: np.ndarray | None = None

    def load(self) -> None:
        """Load the pre-computed geometric bridge from package data.

        Silently sets is_loaded=False if artifact files are missing.
        """
        try:
            data_dir = Path(__file__).resolve().parent.parent / "data"
            npz_path = data_dir / "semantic_bridge.npz"
            vocab_path = data_dir / "semantic_vocab.json"

            if not npz_path.exists() or not vocab_path.exists():
                return

            with np.load(str(npz_path)) as npz:
                face_sim_raw = npz["face_sim"]
                # Partial per-face column centering: subtract half of each
                # face's mean across vocabulary. Faces with very "specific"
                # centroids (ethics, methodology) otherwise accumulate
                # systematic negative bias from generic tokens. Full
                # centering over-corrects — ontology/teleology are
                # genuinely broader, their positive bias is partly real
                # signal. 0.5 is a pragmatic midpoint found by benchmark.
                col_means = face_sim_raw.mean(axis=0, keepdims=True)
                self._face_sim = (face_sim_raw - 0.2 * col_means).astype(np.float32)
                self._axis_proj = npz["axis_proj"]
                self._idf = npz["idf"]
                self._faces = [str(f) for f in npz["faces"]]
                # Load disambiguation arrays if present
                if "disambig_face_sim" in npz:
                    self._disambig_face_sim = npz["disambig_face_sim"]
                if "disambig_axis_proj" in npz:
                    self._disambig_axis_proj = npz["disambig_axis_proj"]
                # Load phase weighting arrays (Technique F)
                if "phase_centroids" in npz:
                    self._phase_centroids = npz["phase_centroids"]
                if "word_phase_sim" in npz:
                    self._word_phase_sim = npz["word_phase_sim"]
                # Load question position maps (Technique D)
                if "word_question_x" in npz:
                    self._word_question_x = npz["word_question_x"]
                if "word_question_y" in npz:
                    self._word_question_y = npz["word_question_y"]

            with open(vocab_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            # Handle both old format (flat dict) and new format (structured)
            if isinstance(raw_data, dict) and "words" in raw_data:
                self._vocab = raw_data["words"]
                # Load disambiguation metadata
                if "disambiguation" in raw_data:
                    self._disambig_meta = raw_data["disambiguation"]
                # Load phrase keys
                if "phrases" in raw_data:
                    self._phrase_keys = set(raw_data["phrases"])
                # Load surface-to-canonical mapping
                if "surface_to_canonical" in raw_data:
                    self._surface_to_canonical = raw_data["surface_to_canonical"]
                # Load phase names
                if "phase_names" in raw_data:
                    self._phase_names = raw_data["phase_names"]
            else:
                # Old flat format — word -> index only
                self._vocab = raw_data

        except Exception:
            # Any load failure -> degrade gracefully
            self._face_sim = None
            self._axis_proj = None
            self._idf = None
            self._vocab = {}
            self._faces = []
            self._disambig_face_sim = None
            self._disambig_axis_proj = None
            self._disambig_meta = {}
            self._phrase_keys = set()
            self._surface_to_canonical = {}
            self._phase_centroids = None
            self._word_phase_sim = None
            self._phase_names = []
            self._word_question_x = None
            self._word_question_y = None

    def _lookup_sense(self, token: str, all_tokens: list[str]) -> int | None:
        """Check if token is a disambiguation trigger and find matching sense.

        Returns the sense_idx if a context match is found (>= threshold context
        words present in all_tokens), or None if no disambiguation applies.
        """
        if not self._disambig_meta or token not in self._disambig_meta:
            return None

        token_set = set(all_tokens)
        entries = self._disambig_meta[token]

        for entry in entries:
            context_words = set(entry["context_words"])
            threshold = entry.get("threshold", 2)
            matches = len(context_words & token_set)
            if matches >= threshold:
                return entry["sense_idx"]

        return None

    def face_relevance(self, tokens: list[str]) -> dict[str, float]:
        """Phase 1: IDF-weighted average of discriminative face similarity.

        For each token present in the vocabulary, accumulate its discriminative
        face similarity row weighted by its IDF. Normalize by total IDF weight.
        Result is per-face relevance (can be negative — higher is more relevant).

        Disambiguation: if a token triggers a sense override, use the override
        face_sim row instead of the standard vocabulary row.

        Tokens not in vocabulary are silently ignored. If no tokens match or
        bridge is not loaded, returns all zeros.
        """
        if not self.is_loaded:
            return {f: 0.0 for f in ALL_FACES}

        indices = []
        override_rows = []  # (face_sim_row, idf_weight) for disambiguated tokens

        for token in tokens:
            # Check disambiguation first
            sense_idx = self._lookup_sense(token, tokens)
            if sense_idx is not None and self._disambig_face_sim is not None:
                override_rows.append((
                    self._disambig_face_sim[sense_idx],
                    self._idf[self._vocab[token]] if token in self._vocab else 0.5,
                ))
                continue

            idx = self._vocab.get(token)
            if idx is not None:
                indices.append(idx)

        if not indices and not override_rows:
            return {f: 0.0 for f in ALL_FACES}

        # Combine standard and override rows
        all_rows = []
        all_weights = []

        if indices:
            all_rows.append(self._face_sim[indices])
            all_weights.append(self._idf[indices])

        for row, weight in override_rows:
            all_rows.append(row[np.newaxis, :])
            all_weights.append(np.array([weight], dtype=np.float32))

        rows = np.concatenate(all_rows, axis=0)
        weights = np.concatenate(all_weights, axis=0)

        # Aggressive IDF: raise to a power so that rare face-specific words
        # dominate the weighted average. Common words (low idf) still pass
        # through stop-word filtering but their high-power-damped weights
        # prevent them from drowning the signal from rare specific vocabulary
        # (e.g., "brotherhood", "creed", "justice" for ethics on MLK).
        weights = weights ** 2

        total_weight = weights.sum()

        if total_weight < 1e-9:
            return {f: 0.0 for f in ALL_FACES}

        weighted_avg = (rows * weights[:, np.newaxis]).sum(axis=0) / total_weight

        raw_scores = {face: float(weighted_avg[i]) for i, face in enumerate(self._faces)}

        # Contrastive cube-pair dampening is disabled. Even at reduced
        # strengths (tested 0.1, 0.3) the mechanism net-hurts benchmark
        # accuracy because legitimate philosophical content frequently
        # co-activates paired faces (ethics+axiology for moral rhetoric,
        # epistemology+methodology for scientific texts, phenomenology+
        # aesthetics for dramatic criticism). Pair-suppression punishes
        # exactly those legitimate recognitions.
        return raw_scores

    def _apply_cube_contrast(self, scores: dict[str, float]) -> dict[str, float]:
        """Dampen the weaker member of each cube pair.

        For each of the 6 complementary pairs, if one face scores higher,
        transfer a fraction of the loser's score to the winner. This enforces
        the cube model's prediction that paired faces should not co-activate
        equally — the intent is either more theoretical or more applied.
        """
        result = dict(scores)
        contrast_strength = 0.1  # fraction of difference to transfer

        for face_a, face_b in CUBE_PAIRS:
            if face_a not in result or face_b not in result:
                continue
            sa = result[face_a]
            sb = result[face_b]
            if sa == sb:
                continue
            diff = abs(sa - sb)
            transfer = diff * contrast_strength
            if sa > sb:
                result[face_a] += transfer
                result[face_b] -= transfer
            else:
                result[face_b] += transfer
                result[face_a] -= transfer

        return result

    def axis_projection(self, tokens: list[str], face: str, axis: str) -> tuple[float, float]:
        """Phase 2: IDF-weighted average of pre-computed axis projections.

        Returns:
            scalar: float in [0, 1] — 0 = low pole, 1 = high pole
            confidence: float in [0, 1] — deviation from center * consistency

        The confidence measure captures two properties:
          1. How far from center (0.5) the average projection is
          2. How consistent the projections are across matched tokens (low variance)

        Disambiguation: if a token triggers a sense override, use the override
        axis_proj row instead of the standard vocabulary row.
        """
        if not self.is_loaded:
            return 0.5, 0.0

        # Determine axis column index: face_idx * 2 + axis_offset
        try:
            face_idx = self._faces.index(face)
        except ValueError:
            return 0.5, 0.0

        axis_offset = 0 if axis == "x" else 1
        col = face_idx * 2 + axis_offset

        indices = []
        override_entries = []  # (projection_value, idf_weight)

        for token in tokens:
            # Check disambiguation first
            sense_idx = self._lookup_sense(token, tokens)
            if sense_idx is not None and self._disambig_axis_proj is not None:
                proj_val = float(self._disambig_axis_proj[sense_idx, col])
                idf_val = self._idf[self._vocab[token]] if token in self._vocab else 0.5
                override_entries.append((proj_val, idf_val))
                continue

            idx = self._vocab.get(token)
            if idx is not None:
                indices.append(idx)

        if not indices and not override_entries:
            return 0.5, 0.0

        # Collect all projections and weights
        all_projections = []
        all_weights = []

        if indices:
            all_projections.append(self._axis_proj[indices, col])
            all_weights.append(self._idf[indices])

        for proj_val, idf_val in override_entries:
            all_projections.append(np.array([proj_val], dtype=np.float32))
            all_weights.append(np.array([idf_val], dtype=np.float32))

        projections = np.concatenate(all_projections)
        weights = np.concatenate(all_weights)
        total_weight = weights.sum()

        if total_weight < 1e-9:
            return 0.5, 0.0

        # IDF-weighted mean projection
        scalar = float((projections * weights).sum() / total_weight)

        # Confidence: deviation from center * consistency
        deviation = abs(scalar - 0.5) * 2.0  # 0 at center, 1 at poles

        # Consistency: 1 - normalized weighted std
        weighted_var = float(((projections - scalar) ** 2 * weights).sum() / total_weight)
        std = np.sqrt(weighted_var)
        # Max possible std is 0.5 (all values at 0 or 1)
        consistency = max(0.0, 1.0 - std / 0.5)

        confidence = deviation * consistency

        # Clamp scalar to [0, 1]
        scalar = max(0.0, min(1.0, scalar))
        confidence = max(0.0, min(1.0, confidence))

        return scalar, confidence

    def phase_weighting(self, tokens: list[str]) -> dict[str, float]:
        """Compute phase-aware face weights from IDF-weighted word-phase similarity.

        For each token in the vocabulary, look up its pre-computed cosine
        similarity to each of 3 phase centroids (comprehension, evaluation,
        application). IDF-weight the similarities, normalize to [0, 1], then
        map each face to its phase's score.

        Returns {face: phase_weight} where weight is in [0, 1].
        """
        if not self.is_loaded or self._word_phase_sim is None:
            return {f: 0.5 for f in ALL_FACES}

        indices = []
        for token in tokens:
            idx = self._vocab.get(token)
            if idx is not None and idx < self._word_phase_sim.shape[0]:
                indices.append(idx)

        if not indices:
            return {f: 0.5 for f in ALL_FACES}

        # IDF-weighted average of word-phase similarities
        rows = self._word_phase_sim[indices]  # (n_tokens, 3)
        weights = self._idf[indices]          # (n_tokens,)
        total_weight = weights.sum()

        if total_weight < 1e-9:
            return {f: 0.5 for f in ALL_FACES}

        phase_scores = (rows * weights[:, np.newaxis]).sum(axis=0) / total_weight  # (3,)

        # Normalize to [0, 1]: shift and scale so min -> 0, max -> 1
        ps_min = phase_scores.min()
        ps_max = phase_scores.max()
        ps_range = ps_max - ps_min
        if ps_range > 1e-9:
            phase_normed = (phase_scores - ps_min) / ps_range
        else:
            phase_normed = np.full(3, 0.5)

        # Map phase names to indices
        phase_index = {name: i for i, name in enumerate(self._phase_names)}

        # Map each face to its phase score
        result: dict[str, float] = {}
        for face in ALL_FACES:
            phase = FACE_PHASES.get(face, "comprehension")
            pidx = phase_index.get(phase)
            if pidx is not None:
                result[face] = float(phase_normed[pidx])
            else:
                result[face] = 0.5

        return result

    def question_position(self, tokens: list[str], face: str) -> tuple[int, int] | None:
        """Compute IDF-weighted question-matched grid position for a face.

        For each token, looks up the pre-computed best-matching question
        position within the given face. Returns the IDF-weighted average
        position, rounded to nearest grid integer.

        Returns (x, y) or None if no tokens match or data not loaded.
        """
        if not self.is_loaded or self._word_question_x is None:
            return None

        try:
            face_idx = self._faces.index(face)
        except ValueError:
            return None

        indices = []
        for token in tokens:
            idx = self._vocab.get(token)
            if idx is not None and idx < self._word_question_x.shape[0]:
                indices.append(idx)

        if not indices:
            return None

        # IDF-weighted average of question positions
        x_vals = self._word_question_x[indices, face_idx].astype(np.float32)
        y_vals = self._word_question_y[indices, face_idx].astype(np.float32)
        weights = self._idf[indices]
        total_weight = weights.sum()

        if total_weight < 1e-9:
            return None

        avg_x = float((x_vals * weights).sum() / total_weight)
        avg_y = float((y_vals * weights).sum() / total_weight)

        # Round to nearest grid position, clamp to [0, 11]
        x = max(0, min(11, round(avg_x)))
        y = max(0, min(11, round(avg_y)))

        return (x, y)

    @property
    def is_loaded(self) -> bool:
        """True if artifact files were successfully loaded."""
        return self._face_sim is not None

    @property
    def has_phase_data(self) -> bool:
        """True if phase weighting artifacts are loaded."""
        return self._word_phase_sim is not None and len(self._phase_names) > 0

    @property
    def has_question_data(self) -> bool:
        """True if question position map artifacts are loaded."""
        return self._word_question_x is not None

    @property
    def phrase_keys(self) -> set[str]:
        """Set of canonical phrase strings recognized by the bridge."""
        return self._phrase_keys

    @property
    def surface_to_canonical(self) -> dict[str, str]:
        """Mapping from surface phrase forms (with stop words) to canonical forms."""
        return self._surface_to_canonical
