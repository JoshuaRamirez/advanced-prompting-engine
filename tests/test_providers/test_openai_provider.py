"""Tests for OpenAI cloud embedding provider."""

import json
import urllib.error
from unittest import mock
import numpy as np
import pytest

from advanced_prompting_engine.providers.openai import OpenAIEmbeddingProvider


class TestOpenAIEmbeddingProvider:
    def test_availability(self):
        p1 = OpenAIEmbeddingProvider(api_key=None)
        assert not p1.is_available()

        p2 = OpenAIEmbeddingProvider(api_key="   ")
        assert not p2.is_available()

        p3 = OpenAIEmbeddingProvider(api_key="sk-test-key")
        assert p3.is_available()
        assert p3.provider_name == "openai"
        assert p3.model_name == "text-embedding-3-large"
        assert p3.dimensions == 3072

    def test_empty_string_returns_none(self):
        p = OpenAIEmbeddingProvider(api_key="sk-test-key")
        assert p.embed_text("") is None
        assert p.embed_text("   ") is None

    def test_successful_embedding(self):
        p = OpenAIEmbeddingProvider(api_key="sk-test-key", dimensions=3072)
        mock_vec = [0.1] * 3072
        mock_response_data = json.dumps({
            "object": "list",
            "data": [{"object": "embedding", "index": 0, "embedding": mock_vec}],
            "model": "text-embedding-3-large",
        }).encode("utf-8")

        mock_resp = mock.MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = mock_response_data
        mock_resp.__enter__.return_value = mock_resp

        with mock.patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            vec = p.embed_text("Design an ethical framework")
            assert vec is not None
            assert isinstance(vec, np.ndarray)
            assert vec.shape == (3072,)
            assert np.isclose(np.linalg.norm(vec), 1.0)
            mock_urlopen.assert_called_once()

    def test_http_error_graceful_fallback(self):
        p = OpenAIEmbeddingProvider(api_key="sk-test-key")
        err = urllib.error.HTTPError("https://api.openai.com/v1/embeddings", 401, "Unauthorized", {}, None)

        with mock.patch("urllib.request.urlopen", side_effect=err):
            vec = p.embed_text("Test prompt")
            assert vec is None

    def test_timeout_graceful_fallback(self):
        p = OpenAIEmbeddingProvider(api_key="sk-test-key")
        with mock.patch("urllib.request.urlopen", side_effect=TimeoutError("Connection timed out")):
            vec = p.embed_text("Test prompt")
            assert vec is None

    def test_connection_error_graceful_fallback(self):
        p = OpenAIEmbeddingProvider(api_key="sk-test-key")
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Network unreachable")):
            vec = p.embed_text("Test prompt")
            assert vec is None
