"""Configuration parser for embedding providers.

Reads configuration from environment variables (and local .env if present)
with fallback defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    """Lightweight .env loader without external dependencies."""
    candidate_paths = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent.parent.parent / ".env",
    ]
    for p in candidate_paths:
        if p.is_file():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
            except Exception:
                pass
            break


@dataclass(frozen=True)
class EmbeddingConfig:
    """Immutable configuration for text embedding providers."""

    provider: str = "local"  # 'local', 'openai', 'gemini'
    openai_api_key: str | None = None
    openai_model: str = "text-embedding-3-large"
    openai_dimensions: int = 3072
    gemini_api_key: str | None = None
    gemini_model: str = "text-embedding-005"
    gemini_dimensions: int = 2048
    timeout: float = 5.0

    @classmethod
    def from_env(cls) -> EmbeddingConfig:
        """Create configuration by reading environment variables and local .env."""
        _load_dotenv()

        provider = os.getenv("APE_EMBEDDING_PROVIDER", "local").strip().lower()
        if provider not in ("local", "openai", "gemini", "google"):
            provider = "local"
        if provider == "google":
            provider = "gemini"

        openai_key = os.getenv("APE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        gemini_key = (
            os.getenv("APE_GEMINI_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )

        openai_model = os.getenv("APE_OPENAI_MODEL", "text-embedding-3-large").strip()
        gemini_model = os.getenv("APE_GEMINI_MODEL", "text-embedding-005").strip()

        try:
            openai_dims = int(os.getenv("APE_OPENAI_DIMENSIONS", "3072"))
        except ValueError:
            openai_dims = 3072

        try:
            gemini_dims = int(os.getenv("APE_GEMINI_DIMENSIONS", "2048"))
        except ValueError:
            gemini_dims = 2048

        try:
            timeout = float(os.getenv("APE_EMBEDDING_TIMEOUT", "5.0"))
        except ValueError:
            timeout = 5.0

        return cls(
            provider=provider,
            openai_api_key=openai_key.strip() if openai_key else None,
            openai_model=openai_model,
            openai_dimensions=openai_dims,
            gemini_api_key=gemini_key.strip() if gemini_key else None,
            gemini_model=gemini_model,
            gemini_dimensions=gemini_dims,
            timeout=max(0.5, timeout),
        )
