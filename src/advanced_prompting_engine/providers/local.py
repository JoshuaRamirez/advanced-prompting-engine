"""Local offline embedding provider (default).

Signals that intent parsing should run through the local pre-computed
GeometricBridge artifacts without network calls.
"""

from __future__ import annotations

import numpy as np

from advanced_prompting_engine.providers.base import BaseEmbeddingProvider


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    """Local offline provider — delegates intent parsing to GeometricBridge."""

    @property
    def provider_name(self) -> str:
        return "local"

    @property
    def model_name(self) -> str:
        return "bge-large-en-v1.5"

    @property
    def dimensions(self) -> int:
        return 1024

    def is_available(self) -> bool:
        return True

    def embed_text(self, text: str) -> np.ndarray | None:
        # Local provider relies on GeometricBridge lookup at runtime
        return None
