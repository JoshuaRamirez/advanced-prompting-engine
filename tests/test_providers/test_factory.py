"""Tests for provider factory resolution and fallback."""

from advanced_prompting_engine.providers.config import EmbeddingConfig
from advanced_prompting_engine.providers.factory import get_embedding_provider
from advanced_prompting_engine.providers.gemini import GeminiEmbeddingProvider
from advanced_prompting_engine.providers.local import LocalEmbeddingProvider
from advanced_prompting_engine.providers.openai import OpenAIEmbeddingProvider


class TestProviderFactory:
    def test_default_returns_local(self):
        config = EmbeddingConfig(provider="local")
        p = get_embedding_provider(config)
        assert isinstance(p, LocalEmbeddingProvider)
        assert p.provider_name == "local"

    def test_openai_configured(self):
        config = EmbeddingConfig(provider="openai", openai_api_key="sk-test-valid")
        p = get_embedding_provider(config)
        assert isinstance(p, OpenAIEmbeddingProvider)
        assert p.provider_name == "openai"

    def test_openai_missing_key_falls_back_to_local(self):
        config = EmbeddingConfig(provider="openai", openai_api_key=None)
        p = get_embedding_provider(config)
        assert isinstance(p, LocalEmbeddingProvider)

    def test_gemini_configured(self):
        config = EmbeddingConfig(provider="gemini", gemini_api_key="AIzaSyValid")
        p = get_embedding_provider(config)
        assert isinstance(p, GeminiEmbeddingProvider)
        assert p.provider_name == "gemini"

    def test_gemini_missing_key_falls_back_to_local(self):
        config = EmbeddingConfig(provider="gemini", gemini_api_key=None)
        p = get_embedding_provider(config)
        assert isinstance(p, LocalEmbeddingProvider)
