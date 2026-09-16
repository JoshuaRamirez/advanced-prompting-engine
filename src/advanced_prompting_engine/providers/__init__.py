"""Pluggable embedding providers subsystem.

Authoritative source: ADR-015 (Pluggable Cloud Vector Embeddings).
"""

from __future__ import annotations

from advanced_prompting_engine.providers.base import BaseEmbeddingProvider
from advanced_prompting_engine.providers.config import EmbeddingConfig
from advanced_prompting_engine.providers.factory import get_embedding_provider
from advanced_prompting_engine.providers.gemini import GeminiEmbeddingProvider
from advanced_prompting_engine.providers.local import LocalEmbeddingProvider
from advanced_prompting_engine.providers.openai import OpenAIEmbeddingProvider

__all__ = [
    "BaseEmbeddingProvider",
    "EmbeddingConfig",
    "GeminiEmbeddingProvider",
    "LocalEmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "get_embedding_provider",
]
