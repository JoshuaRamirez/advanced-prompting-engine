"""Geometric bridge — loads pre-computed GloVe-derived face relevance and axis
projections at runtime.

The artifacts are generated offline by scripts/build_semantic_bridge.py. At
runtime, this module loads three pre-computed arrays from the package data
directory and provides fast numpy-only lookups:

  1. face_relevance(tokens) — IDF-weighted discriminative face similarity
  2. axis_projection(tokens, face, axis) — IDF-weighted axis projection [0,1]

Enhanced with:
  - Contextual disambiguation for polysemous words (Alg 2)
  - N-gram/phrase vocabulary for multi-word lookups (Alg 3)

No GloVe vectors are needed at runtime. If the artifact files are absent
(developer has not run the build script), the bridge reports is_loaded=False
and all queries degrade gracefully.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from advanced_prompting_engine.graph.schema import ALL_FACES, CUBE_PAIRS


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
                self._face_sim = npz["face_sim"]
                self._axis_proj = npz["axis_proj"]
                self._idf = npz["idf"]
                self._faces = [str(f) for f in npz["faces"]]
                # Load disambiguation arrays if present
                if "disambig_face_sim" in npz:
                    self._disambig_face_sim = npz["disambig_face_sim"]
                if "disambig_axis_proj" in npz:
                    self._disambig_axis_proj = npz["disambig_axis_proj"]

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
            return {f: 0.0 for f in self._faces}

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
        total_weight = weights.sum()

        if total_weight < 1e-9:
            return {f: 0.0 for f in self._faces}

        weighted_avg = (rows * weights[:, np.newaxis]).sum(axis=0) / total_weight

        raw_scores = {face: float(weighted_avg[i]) for i, face in enumerate(self._faces)}

        # Contrastive cube-pair dampening
        return self._apply_cube_contrast(raw_scores)

    def _apply_cube_contrast(self, scores: dict[str, float]) -> dict[str, float]:
        """Dampen the weaker member of each cube pair.

        For each of the 6 complementary pairs, if one face scores higher,
        transfer a fraction of the loser's score to the winner. This enforces
        the cube model's prediction that paired faces should not co-activate
        equally — the intent is either more theoretical or more applied.
        """
        result = dict(scores)
        contrast_strength = 0.3  # fraction of difference to transfer

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

    @property
    def is_loaded(self) -> bool:
        """True if artifact files were successfully loaded."""
        return self._face_sim is not None

    @property
    def phrase_keys(self) -> set[str]:
        """Set of canonical phrase strings recognized by the bridge."""
        return self._phrase_keys

    @property
    def surface_to_canonical(self) -> dict[str, str]:
        """Mapping from surface phrase forms (with stop words) to canonical forms."""
        return self._surface_to_canonical
