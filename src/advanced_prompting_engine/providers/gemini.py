"""Google Gemini cloud embedding provider using standard library HTTP client.

Authoritative source: ADR-015 (Pluggable Cloud Vector Embeddings).
Zero external SDK dependencies — uses urllib.request.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
import numpy as np

from advanced_prompting_engine.providers.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """Embeds text via Google's Gemini / Vertex Embed Content REST API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-005",
        dimensions: int = 2048,
        timeout: float = 5.0,
    ):
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def is_available(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    def embed_text(self, text: str) -> np.ndarray | None:
        """Embed text using Gemini's embedContent REST endpoint."""
        if not self.is_available():
            logger.debug("Gemini provider unavailable: API key not set")
            return None

        clean_text = text.strip()
        if not clean_text:
            return None

        model_path = self._model if self._model.startswith("models/") else f"models/{self._model}"
        encoded_key = urllib.parse.quote(self._api_key)
        url = f"https://generativelanguage.googleapis.com/v1beta/{model_path}:embedContent?key={encoded_key}"

        payload = {
            "model": model_path,
            "content": {
                "parts": [{"text": clean_text}]
            },
            "taskType": "SEMANTIC_SIMILARITY",
        }
        # text-embedding-005 and newer support outputDimensionality
        if self._dimensions:
            payload["outputDimensionality"] = self._dimensions

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "advanced-prompting-engine/0.9.0",
        }

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                if resp.status != 200:
                    logger.warning("Gemini embedding API returned status %d", resp.status)
                    return None
                body = json.loads(resp.read().decode("utf-8"))

            emb_obj = body.get("embedding", {})
            raw_vec = emb_obj.get("values")
            if not raw_vec:
                logger.warning("Gemini response contained no embedding values")
                return None

            vec = np.array(raw_vec, dtype=np.float32)
            norm = np.linalg.norm(vec)
            if norm > 1e-9:
                vec = vec / norm
            return vec

        except urllib.error.HTTPError as e:
            logger.warning("Gemini HTTP error %d: %s", e.code, e.reason)
            return None
        except urllib.error.URLError as e:
            logger.warning("Gemini connection error: %s", e.reason)
            return None
        except TimeoutError:
            logger.warning("Gemini embedding request timed out (limit: %.1fs)", self._timeout)
            return None
        except Exception as e:
            logger.warning("Gemini embedding error: %s", e)
            return None
