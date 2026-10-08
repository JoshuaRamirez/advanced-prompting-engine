"""Factory for resolving and instantiating embedding providers.

Authoritative source: ADR-015 (Pluggable Cloud Vector Embeddings).
"""

from __future__ import annotations

import logging

from advanced_prompting_engine.providers.base import BaseEmbeddingProvider
from advanced_prompting_engine.providers.config import EmbeddingConfig
from advanced_prompting_engine.providers.gemini import GeminiEmbeddingProvider
from advanced_prompting_engine.providers.local import LocalEmbeddingProvider
from advanced_prompting_engine.providers.openai import OpenAIEmbeddingProvider

logger = logging.getLogger(__name__)


def get_embedding_provider(config: EmbeddingConfig | None = None) -> BaseEmbeddingProvider:
    """Instantiate and return the configured embedding provider.

    Defaults to LocalEmbeddingProvider if unconfigured, if provider is 'local',
    or if configured cloud provider lacks required credentials.
    """
    if config is None:
        config = EmbeddingConfig.from_env()

    if config.provider == "openai":
        provider = OpenAIEmbeddingProvider(
            api_key=config.openai_api_key,
            model=config.openai_model,
            dimensions=config.openai_dimensions,
            timeout=config.timeout,
        )
        if provider.is_available():
            logger.info("Initialized OpenAI embedding provider (%s, %dd)", config.openai_model, config.openai_dimensions)
            return provider
        else:
            logger.warning("OpenAI embedding requested but API key is missing — falling back to local provider")
            return LocalEmbeddingProvider()

    elif config.provider == "gemini":
        provider = GeminiEmbeddingProvider(
            api_key=config.gemini_api_key,
            model=config.gemini_model,
            dimensions=config.gemini_dimensions,
            timeout=config.timeout,
        )
        if provider.is_available():
            logger.info("Initialized Gemini embedding provider (%s, %dd)", config.gemini_model, config.gemini_dimensions)
            return provider
        else:
            logger.warning("Gemini embedding requested but API key is missing — falling back to local provider")
            return LocalEmbeddingProvider()

    return LocalEmbeddingProvider()
