"""Tests for embedding provider configuration parsing."""

import os
from unittest import mock
import pytest

from advanced_prompting_engine.providers.config import EmbeddingConfig


class TestEmbeddingConfig:
    def test_default_config(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            config = EmbeddingConfig.from_env()
            assert config.provider == "local"
            assert config.openai_api_key is None
            assert config.gemini_api_key is None
            assert config.openai_model == "text-embedding-3-large"
            assert config.openai_dimensions == 3072
            assert config.gemini_model == "text-embedding-005"
            assert config.gemini_dimensions == 2048
            assert config.timeout == 5.0

    def test_openai_env_config(self):
        env = {
            "APE_EMBEDDING_PROVIDER": "openai",
            "APE_OPENAI_API_KEY": "sk-test-key-123",
            "APE_OPENAI_MODEL": "text-embedding-3-small",
            "APE_OPENAI_DIMENSIONS": "1536",
            "APE_EMBEDDING_TIMEOUT": "2.5",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = EmbeddingConfig.from_env()
            assert config.provider == "openai"
            assert config.openai_api_key == "sk-test-key-123"
            assert config.openai_model == "text-embedding-3-small"
            assert config.openai_dimensions == 1536
            assert config.timeout == 2.5

    def test_fallback_standard_keys(self):
        env = {
            "APE_EMBEDDING_PROVIDER": "openai",
            "OPENAI_API_KEY": "sk-std-key-456",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = EmbeddingConfig.from_env()
            assert config.provider == "openai"
            assert config.openai_api_key == "sk-std-key-456"

    def test_gemini_env_config(self):
        env = {
            "APE_EMBEDDING_PROVIDER": "gemini",
            "GEMINI_API_KEY": "AIzaSyTest789",
            "APE_GEMINI_MODEL": "text-embedding-004",
            "APE_GEMINI_DIMENSIONS": "768",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = EmbeddingConfig.from_env()
            assert config.provider == "gemini"
            assert config.gemini_api_key == "AIzaSyTest789"
            assert config.gemini_model == "text-embedding-004"
            assert config.gemini_dimensions == 768

    def test_google_alias(self):
        env = {
            "APE_EMBEDDING_PROVIDER": "google",
            "GOOGLE_API_KEY": "AIzaSyGoogleKey",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = EmbeddingConfig.from_env()
            assert config.provider == "gemini"
            assert config.gemini_api_key == "AIzaSyGoogleKey"

    def test_invalid_provider_falls_back_to_local(self):
        env = {
            "APE_EMBEDDING_PROVIDER": "unsupported_provider",
        }
        with mock.patch.dict(os.environ, env, clear=True):
            config = EmbeddingConfig.from_env()
            assert config.provider == "local"
