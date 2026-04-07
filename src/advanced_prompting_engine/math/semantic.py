"""Semantic bridge — loads pre-computed GloVe-derived face relevance at runtime.

The similarity matrix and vocabulary are generated offline by
scripts/build_semantic_bridge.py. At runtime, this module loads the two
artifact files (semantic_bridge.npz, semantic_vocab.json) from the package
data directory and provides a fast numpy-only lookup: given a set of tokens,
return per-face relevance scores.

No GloVe vectors are needed at runtime. If the artifact files are absent
(developer has not run the build script), the bridge reports is_loaded=False
and all queries return uniform zeros — the intent parser falls back to
keyword-only matching.
"""

from __future__ import annotations

import json
import importlib.resources
from pathlib import Path

import numpy as np


class SemanticBridge:
    """Pre-computed word-to-face similarity lookup.

    Attributes:
        _matrix: shape (vocab_size, 12) — row i is word i's cosine
                 similarity to each of the 12 face centroids.
        _vocab: word (lowercase, unstemmed) -> row index in _matrix.
        _faces: face names in the order they appear as columns.
    """

    def __init__(self):
        self._matrix: np.ndarray | None = None
        self._vocab: dict[str, int] = {}
        self._faces: list[str] = []

    def load(self) -> None:
        """Load the pre-computed semantic bridge from package data.

        Silently sets is_loaded=False if artifact files are missing.
        """
        try:
            data_dir = Path(__file__).resolve().parent.parent / "data"
            npz_path = data_dir / "semantic_bridge.npz"
            vocab_path = data_dir / "semantic_vocab.json"

            if not npz_path.exists() or not vocab_path.exists():
                return

            with np.load(str(npz_path)) as npz:
                self._matrix = npz["matrix"]
                self._faces = [str(f) for f in npz["faces"]]

            with open(vocab_path, "r", encoding="utf-8") as f:
                self._vocab = json.load(f)

        except Exception:
            # Any load failure -> degrade gracefully
            self._matrix = None
            self._vocab = {}
            self._faces = []

    def face_relevance(self, tokens: set[str]) -> dict[str, float]:
        """Given a set of tokens, return face -> relevance score in [0, 1].

        For each token present in the vocabulary, its row in the similarity
        matrix is accumulated. The average across all matched tokens gives
        a raw per-face score, which is then normalized to [0, 1].

        Tokens not in the vocabulary are silently ignored. If no tokens
        match or the bridge is not loaded, returns all zeros.
        """
        if not self.is_loaded:
            return {f: 0.0 for f in self._faces} if self._faces else {}

        # Collect row indices for tokens that exist in vocab
        indices = []
        for token in tokens:
            # Try the token as-is (stems are lowercase already)
            idx = self._vocab.get(token)
            if idx is not None:
                indices.append(idx)

        if not indices:
            return {f: 0.0 for f in self._faces}

        # Average the similarity rows for matched tokens
        rows = self._matrix[indices]  # shape (n_matched, 12)
        avg = np.mean(rows, axis=0)   # shape (12,)

        # Normalize to [0, 1]
        min_val = avg.min()
        max_val = avg.max()
        if max_val - min_val > 1e-9:
            normalized = (avg - min_val) / (max_val - min_val)
        else:
            normalized = np.zeros_like(avg)

        return {face: float(normalized[i]) for i, face in enumerate(self._faces)}

    @property
    def is_loaded(self) -> bool:
        """True if artifact files were successfully loaded."""
        return self._matrix is not None
