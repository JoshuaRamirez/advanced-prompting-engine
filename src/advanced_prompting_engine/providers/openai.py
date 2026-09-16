"""OpenAI cloud embedding provider using standard library HTTP client.

Authoritative source: ADR-015 (Pluggable Cloud Vector Embeddings).
Zero external SDK dependencies — uses urllib.request.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
import numpy as np

from advanced_prompting_engine.providers.base import BaseEmbeddingProvider

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Embeds text via OpenAI's Embeddings API (text-embedding-3-large / small)."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-3-large",
        dimensions: int = 3072,
        timeout: float = 5.0,
    ):
        self._api_key = api_key
        self._model = model
        self._dimensions = dimensions
        self._timeout = timeout

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def is_available(self) -> bool:
        return bool(self._api_key and self._api_key.strip())

    def embed_text(self, text: str) -> np.ndarray | None:
        """Embed text using OpenAI's REST API."""
        if not self.is_available():
            logger.debug("OpenAI provider unavailable: API key not set")
            return None

        clean_text = text.strip()
        if not clean_text:
            return None

        url = "https://api.openai.com/v1/embeddings"
        payload = {
            "input": clean_text,
            "model": self._model,
            "encoding_format": "float",
        }
        # text-embedding-3-* models support the dimensions parameter
        if "text-embedding-3" in self._model:
            payload["dimensions"] = self._dimensions

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._api_key}",
            "User-Agent": "advanced-prompting-engine/0.9.0",
        }

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                if resp.status != 200:
                    logger.warning("OpenAI embedding API returned status %d", resp.status)
                    return None
                body = json.loads(resp.read().decode("utf-8"))

            emb_data = body.get("data", [])
            if not emb_data:
                logger.warning("OpenAI response contained no embedding data")
                return None

            raw_vec = emb_data[0].get("embedding")
            if not raw_vec:
                return None

            vec = np.array(raw_vec, dtype=np.float32)
            norm = np.linalg.norm(vec)
            if norm > 1e-9:
                vec = vec / norm
            return vec

        except urllib.error.HTTPError as e:
            logger.warning("OpenAI HTTP error %d: %s", e.code, e.reason)
            return None
        except urllib.error.URLError as e:
            logger.warning("OpenAI connection error: %s", e.reason)
            return None
        except TimeoutError:
            logger.warning("OpenAI embedding request timed out (limit: %.1fs)", self._timeout)
            return None
        except Exception as e:
            logger.warning("OpenAI embedding error: %s", e)
            return None
