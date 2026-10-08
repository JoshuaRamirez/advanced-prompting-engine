"""Abstract base class for embedding providers.

Authoritative source: ADR-015 (Pluggable Cloud Vector Embeddings).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import numpy as np


class BaseEmbeddingProvider(ABC):
    """Abstract interface for text embedding providers."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique provider identifier (e.g. 'local', 'openai', 'gemini')."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the specific model identifier being used."""
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return the output vector dimensionality (e.g. 1024, 2048, 3072)."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check whether the provider is properly configured and available."""
        ...

    @abstractmethod
    def embed_text(self, text: str) -> np.ndarray | None:
        """Embed a natural language text string into a normalized dense float32 vector.

        Returns:
            np.ndarray of shape (dimensions,), L2-normalized (norm=1.0),
            or None if embedding failed or provider is unavailable.
        """
        ...
