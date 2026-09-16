"""Tests for Google Gemini cloud embedding provider."""

import json
import urllib.error
from unittest import mock
import numpy as np
import pytest

from advanced_prompting_engine.providers.gemini import GeminiEmbeddingProvider


class TestGeminiEmbeddingProvider:
    def test_availability(self):
        p1 = GeminiEmbeddingProvider(api_key=None)
        assert not p1.is_available()

        p2 = GeminiEmbeddingProvider(api_key="   ")
        assert not p2.is_available()

        p3 = GeminiEmbeddingProvider(api_key="AIzaSyTestKey")
        assert p3.is_available()
        assert p3.provider_name == "gemini"
        assert p3.model_name == "text-embedding-005"
        assert p3.dimensions == 2048

    def test_empty_string_returns_none(self):
        p = GeminiEmbeddingProvider(api_key="AIzaSyTestKey")
        assert p.embed_text("") is None
        assert p.embed_text("   ") is None

    def test_successful_embedding(self):
        p = GeminiEmbeddingProvider(api_key="AIzaSyTestKey", dimensions=2048)
        mock_vec = [0.05] * 2048
        mock_response_data = json.dumps({
            "embedding": {"values": mock_vec},
        }).encode("utf-8")

        mock_resp = mock.MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = mock_response_data
        mock_resp.__enter__.return_value = mock_resp

        with mock.patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
            vec = p.embed_text("Inquire into the epistemological foundations")
            assert vec is not None
            assert isinstance(vec, np.ndarray)
            assert vec.shape == (2048,)
            assert np.isclose(np.linalg.norm(vec), 1.0)
            mock_urlopen.assert_called_once()

    def test_http_error_graceful_fallback(self):
        p = GeminiEmbeddingProvider(api_key="AIzaSyTestKey")
        err = urllib.error.HTTPError("https://generativelanguage.googleapis.com", 403, "Forbidden", {}, None)

        with mock.patch("urllib.request.urlopen", side_effect=err):
            vec = p.embed_text("Test prompt")
            assert vec is None

    def test_timeout_graceful_fallback(self):
        p = GeminiEmbeddingProvider(api_key="AIzaSyTestKey")
        with mock.patch("urllib.request.urlopen", side_effect=TimeoutError("Request timed out")):
            vec = p.embed_text("Test prompt")
            assert vec is None
