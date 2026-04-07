"""Geometric bridge — loads pre-computed GloVe-derived face relevance and axis
projections at runtime.

The artifacts are generated offline by scripts/build_semantic_bridge.py. At
runtime, this module loads three pre-computed arrays from the package data
directory and provides fast numpy-only lookups:

  1. face_relevance(tokens) — IDF-weighted discriminative face similarity
  2. axis_projection(tokens, face, axis) — IDF-weighted axis projection [0,1]

No GloVe vectors are needed at runtime. If the artifact files are absent
(developer has not run the build script), the bridge reports is_loaded=False
and all queries degrade gracefully.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from advanced_prompting_engine.graph.schema import ALL_FACES


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
    """

    def __init__(self):
        self._face_sim: np.ndarray | None = None
        self._axis_proj: np.ndarray | None = None
        self._idf: np.ndarray | None = None
        self._vocab: dict[str, int] = {}
        self._faces: list[str] = []

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

            with open(vocab_path, "r", encoding="utf-8") as f:
                self._vocab = json.load(f)

        except Exception:
            # Any load failure -> degrade gracefully
            self._face_sim = None
            self._axis_proj = None
            self._idf = None
            self._vocab = {}
            self._faces = []

    def face_relevance(self, tokens: list[str]) -> dict[str, float]:
        """Phase 1: IDF-weighted average of discriminative face similarity.

        For each token present in the vocabulary, accumulate its discriminative
        face similarity row weighted by its IDF. Normalize by total IDF weight.
        Result is per-face relevance (can be negative — higher is more relevant).

        Tokens not in vocabulary are silently ignored. If no tokens match or
        bridge is not loaded, returns all zeros.
        """
        if not self.is_loaded:
            return {f: 0.0 for f in ALL_FACES}

        indices = []
        for token in tokens:
            idx = self._vocab.get(token)
            if idx is not None:
                indices.append(idx)

        if not indices:
            return {f: 0.0 for f in self._faces}

        # IDF-weighted average of discriminative similarity rows
        rows = self._face_sim[indices]  # shape (n_matched, 12)
        weights = self._idf[indices]    # shape (n_matched,)
        total_weight = weights.sum()

        if total_weight < 1e-9:
            return {f: 0.0 for f in self._faces}

        weighted_avg = (rows * weights[:, np.newaxis]).sum(axis=0) / total_weight  # shape (12,)

        return {face: float(weighted_avg[i]) for i, face in enumerate(self._faces)}

    def axis_projection(self, tokens: list[str], face: str, axis: str) -> tuple[float, float]:
        """Phase 2: IDF-weighted average of pre-computed axis projections.

        Returns:
            scalar: float in [0, 1] — 0 = low pole, 1 = high pole
            confidence: float in [0, 1] — deviation from center * consistency

        The confidence measure captures two properties:
          1. How far from center (0.5) the average projection is
          2. How consistent the projections are across matched tokens (low variance)
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
        for token in tokens:
            idx = self._vocab.get(token)
            if idx is not None:
                indices.append(idx)

        if not indices:
            return 0.5, 0.0

        projections = self._axis_proj[indices, col]  # shape (n_matched,)
        weights = self._idf[indices]                  # shape (n_matched,)
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
