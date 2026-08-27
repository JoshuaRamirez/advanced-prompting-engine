"""Cloud semantic bridge — projects live cloud embedding vectors onto the 12-face manifold.

Authoritative source: ADR-015 (Pluggable Cloud Vector Embeddings).
Zero runtime ML dependencies — pure numpy vector projections.
"""

from __future__ import annotations

import logging
from pathlib import Path
import numpy as np

from advanced_prompting_engine.graph.schema import ALL_FACES, FACE_PHASES

logger = logging.getLogger(__name__)


class CloudSemanticBridge:
    """Projects high-dimensional continuous embedding vectors onto the 12-face Construct."""

    def __init__(self):
        self._face_centroids: np.ndarray | None = None  # (12, D)
        self._faces: list[str] = list(ALL_FACES)
        self._axis_directions: np.ndarray | None = None  # (24, D)
        self._cal_low: np.ndarray | None = None          # (24,)
        self._cal_high: np.ndarray | None = None         # (24,)
        self._phase_centroids: np.ndarray | None = None  # (3, D)
        self._phase_names: list[str] = ["comprehension", "evaluation", "application"]
        self._provider: str = ""
        self._dimensions: int = 0
        self._is_loaded: bool = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def has_phase_data(self) -> bool:
        return self._phase_centroids is not None

    def load(self, provider: str = "openai", dimensions: int = 3072) -> bool:
        """Load the pre-computed cloud anchor matrices for the specified provider."""
        data_dir = Path(__file__).resolve().parent.parent / "data"

        candidate_files = [
            data_dir / f"cloud_anchors_{provider}_{dimensions}.npz",
            data_dir / f"cloud_anchors_{provider}.npz",
        ]

        npz_path: Path | None = None
        for cand in candidate_files:
            if cand.exists():
                npz_path = cand
                break

        if npz_path is None:
            logger.debug("Cloud anchor file not found for provider %s (%dd)", provider, dimensions)
            self._is_loaded = False
            return False

        try:
            with np.load(str(npz_path)) as npz:
                self._face_centroids = npz["face_centroids"].astype(np.float32)
                self._axis_directions = npz["axis_directions"].astype(np.float32)
                self._cal_low = npz["cal_low"].astype(np.float32)
                self._cal_high = npz["cal_high"].astype(np.float32)
                if "faces" in npz:
                    self._faces = [str(f) for f in npz["faces"]]
                if "phase_centroids" in npz:
                    self._phase_centroids = npz["phase_centroids"].astype(np.float32)
                if "phase_names" in npz:
                    self._phase_names = [str(p) for p in npz["phase_names"]]

            self._provider = provider
            self._dimensions = self._face_centroids.shape[1]
            self._is_loaded = True
            logger.info("Loaded cloud anchors for %s (%dd)", provider, self._dimensions)
            return True
        except Exception as e:
            logger.warning("Failed to load cloud anchor file %s: %s", npz_path, e)
            self._is_loaded = False
            return False

    def face_relevance(self, intent_vector: np.ndarray) -> dict[str, float]:
        """Compute discriminative face similarity from a normalized intent vector."""
        if not self._is_loaded or self._face_centroids is None:
            return {f: 0.0 for f in self._faces}

        # Dot product with each of the 12 face centroids
        raw_sim = np.dot(self._face_centroids, intent_vector)  # shape (12,)
        mean_sim = float(np.mean(raw_sim))

        # Discriminative score = similarity - mean across faces
        disc_sim = raw_sim - mean_sim

        return {face: float(disc_sim[i]) for i, face in enumerate(self._faces)}

    def phase_weighting(self, intent_vector: np.ndarray) -> dict[str, float]:
        """Compute phase-aware face weighting from phase centroids."""
        if not self._is_loaded or self._phase_centroids is None:
            return {f: 0.5 for f in ALL_FACES}

        raw_sim = np.dot(self._phase_centroids, intent_vector)  # shape (3,)
        min_s = float(np.min(raw_sim))
        max_s = float(np.max(raw_sim))
        spread = max_s - min_s

        if spread > 1e-9:
            norm_phase = (raw_sim - min_s) / spread
        else:
            norm_phase = np.array([0.5, 0.5, 0.5], dtype=np.float32)

        phase_map = {name: float(norm_phase[i]) for i, name in enumerate(self._phase_names)}

        result: dict[str, float] = {}
        for face in ALL_FACES:
            p = FACE_PHASES.get(face, "comprehension")
            result[face] = phase_map.get(p, 0.5)
        return result

    def axis_projection(self, intent_vector: np.ndarray, face: str, axis: str) -> tuple[float, float]:
        """Project intent vector onto high-pole/low-pole axis direction.

        Returns:
            (scalar_in_0_1, confidence_in_0_1)
        """
        if not self._is_loaded or self._axis_directions is None:
            return (0.5, 0.0)

        try:
            face_idx = self._faces.index(face)
        except ValueError:
            return (0.5, 0.0)

        axis_offset = 0 if axis == "x" else 1
        axis_idx = face_idx * 2 + axis_offset

        direction = self._axis_directions[axis_idx]
        cal_low = float(self._cal_low[axis_idx]) if self._cal_low is not None else -0.3
        cal_high = float(self._cal_high[axis_idx]) if self._cal_high is not None else 0.3

        proj = float(np.dot(direction, intent_vector))
        span = cal_high - cal_low

        if span > 1e-9:
            scalar = (proj - cal_low) / span
        else:
            scalar = 0.5

        clamped_scalar = max(0.0, min(1.0, scalar))

        # Confidence is higher when the projection distinctly leans towards a pole
        confidence = min(1.0, max(0.05, abs(clamped_scalar - 0.5) * 2.0))

        return (clamped_scalar, confidence)
