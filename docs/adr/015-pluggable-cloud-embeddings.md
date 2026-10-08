# ADR-015: Pluggable Cloud Vector Embeddings

## Status

Proposed (v0.9.0)

## Context

The Stage 1 Intent Parser converts natural language user intent into partial 12-dimensional grid coordinates. In v0.7.0 (ADR-013), `BAAI/bge-large-en-v1.5` was adopted as the build-time embedding source, pre-computing word/phrase projections into `semantic_bridge.npz` and `semantic_vocab.json`.

While this preserved ADR-005 (zero ML runtime dependencies) and improved benchmark scores (13/20 → 17/20), it introduced a runtime bottleneck:
- At runtime, natural language intent is decomposed into individual words/phrases and projected via IDF²-weighted averaging.
- The model cannot perform dynamic, whole-sentence contextual attention at runtime.
- Vocabulary is bounded by the pre-computed dictionary (~15,000 words).

High-dimensional cloud embedding APIs (OpenAI `text-embedding-3-large` at 3072d and Google Gemini `text-embedding-005` at 2048d) offer continuous, whole-sentence semantic representations that can capture complex multi-clause prompt intent.

## Decision

Introduce a **pluggable, opt-in cloud vector embedding architecture** for Stage 1 Intent Parsing, while keeping the local BGE offline pipeline as the default.

### 1. Opt-In Configuration (Default: Local)
The system is controlled via environment variables (or `.mcp.json` `env` blocks):
- `APE_EMBEDDING_PROVIDER`: `"local"` (default), `"openai"`, or `"gemini"`.
- `APE_OPENAI_API_KEY` / `OPENAI_API_KEY`
- `APE_OPENAI_MODEL` (default: `"text-embedding-3-large"`)
- `APE_GEMINI_API_KEY` / `GEMINI_API_KEY` / `GOOGLE_API_KEY`
- `APE_GEMINI_MODEL` (default: `"text-embedding-005"`)
- `APE_EMBEDDING_TIMEOUT` (default: `5.0` seconds)

If unset or set to `"local"`, the engine executes the offline BGE `GeometricBridge` with zero external calls.

### 2. Dependency Purity (ADR-005 Preserved)
To maintain zero additional runtime dependencies, HTTP clients for OpenAI and Gemini are implemented using Python standard library `urllib.request` + `json`. No external SDKs (`openai`, `google-genai`, `requests`) are added to package dependencies.

### 3. Native Cloud Anchor Matrices
Because 3072d/2048d vectors cannot be compared against 1024d BGE centroids, each supported cloud model is paired with a pre-computed anchor artifact:
- `cloud_anchors_openai_3072.npz` (~180 KB)
- `cloud_anchors_gemini_2048.npz` (~120 KB)

Each artifact contains:
- 12 face centroids $(12, D)$
- 24 axis direction vectors $(24, D)$
- Model-calibrated `cal_low` and `cal_high` bounds $(24,)$
- 3 phase centroids $(3, D)$

### 4. Zero-Exception Fallback
If a cloud provider is active but an API key is missing, network is unreachable, or a request times out, the pipeline automatically falls back to the local BGE bridge.

## Consequences

- **Positive:** Full-sentence continuous semantic embedding captures multi-clause nuances and eliminates out-of-vocabulary limitations.
- **Positive:** 3,072 / 2,048 dimensions provide 2–3x greater geometric capacity for separating subtle philosophical dimensions.
- **Positive:** Zero breaking changes; 100% backward compatible and runs offline by default.
- **Positive:** Zero new runtime package dependencies.
- **Trade-off:** Cloud mode requires network access and API credentials when explicitly enabled.

## Related

- ADR-005 — numpy as sole runtime dependency (preserved)
- ADR-008 — tag-tfidf intent parsing (superseded by GeometricBridge and CloudBridge)
- ADR-013 — BGE-large-en-v1.5 as build-time embedding source (retained as local provider)
