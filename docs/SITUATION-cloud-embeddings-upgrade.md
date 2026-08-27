# Situation Report: Cloud Vector Embeddings Upgrade

**Date:** 2026-08-27  
**Status:** Vetted & Planned (Awaiting Execution)  
**Context:** Universal Prompt Creation Engine (`advanced-prompting-engine`) — Claude Code CLI Plugin / MCP Server  

---

## 1. Chronological Timeline & Historical Context

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Pre-v0.7.0    │  ───► │  v0.7.0 (04/16) │  ───► │  v0.8.0 (04/20) │  ───► │ Current (08/27) │
│ GloVe / M2V     │       │ BGE-large 1024d │       │ Math & Routing  │       │ Cloud Vectors   │
│ Static 100d     │       │ Build-time npz  │       │ Still BGE 1024d │       │ 3072d/2048d     │
└─────────────────┘       └─────────────────┘       └─────────────────┘       └─────────────────┘
```

### [2026-04-16] · Version 0.7.0 (ADR-013)
* **Problem:** Static GloVe 100d word vectors suffered from "domain ceiling" — phenomenology dominated 6/8 benchmark texts; axiology, aesthetics, and hermeneutics were structurally suppressed.
* **Decision:** Adopted **`BAAI/bge-large-en-v1.5`** (1024d) as the build-time embedding source. To preserve ADR-005 (zero ML runtime dependencies), `bge-large-en-v1.5` was executed offline in `scripts/build_semantic_bridge.py` to pre-calculate word/phrase projections into `semantic_bridge.npz` and `semantic_vocab.json`.
* **Runtime Reality:** Stage 1 (`IntentParser`) executed tokenization, phrase matching, and IDF²-weighted averaging over static dictionary entries. Benchmark rose from 13/20 to 17/20.

### [2026-04-20] · Version 0.8.0 (ADR-014)
* **Evolution:** Expanded mathematical and heuristic layers without changing the underlying vector model:
  * Directional Resonance for cube pairs (ADR-014).
  * Foundation-Precedence Detection (`precedence.py`).
  * Control-Type Classification: structural, bias, mixed (`control_type.py`).
  * 10 new `DISAMBIGUATION_ENTRIES` for duty-bearing vocabulary.
* **Status Confirmed:** The underlying embedding model in v0.8.0 remains **`BAAI/bge-large-en-v1.5`** at 1024 dimensions.

### [2026-08-27] · The Cloud Upgrade Proposal
* **Identified Opportunity:** The build-time bag-of-words approach in v0.8.0 cannot capture dynamic, full-sentence contextual nuances across multi-clause intents.
* **Core Idea:** Offload the text-processing vector model to a high-dimensional cloud model (OpenAI `text-embedding-3-large` @ 3072d or Google Gemini `text-embedding-005` @ 2048d) while keeping the Claude Code CLI / MCP architecture intact.
* **Requirement:** Must be a **configurable feature, OFF by default** (`APE_EMBEDDING_PROVIDER="local"`), maintaining zero-dependency offline execution by default.

---

## 2. Vetting Phase 1: Conceptual Stress-Testing & Blindspots

During self-vetting of the plan against the core idea, four critical technical blindspots were identified and resolved:

### Blindspot 1: Vector Space Incompatibility (Anchor Dimension Mismatch)
* **Analysis:** A 3072d OpenAI vector or 2048d Gemini vector cannot be compared against 1024d BGE centroids.
* **Resolution:** Pre-compute and ship dedicated, ultra-lightweight cloud anchor files:
  * `cloud_anchors_openai_3072.npz` (~180 KB: 12 face centroids, 24 axis directions, 3 phase anchors).
  * `cloud_anchors_gemini_2048.npz` (~120 KB).
  * *Advantage:* Because they only store the ~39 anchor vectors (no 15,000-word vocabulary needed), they are 90% smaller than the local BGE bridge.

### Blindspot 2: Calibration Drift Across Embedding Models
* **Analysis:** Cosine similarity distributions differ dramatically across models (BGE: ~0.60–0.90; OpenAI: ~0.25–0.65). Fixed scalar mapping would distort grid positions.
* **Resolution:** Each cloud anchor artifact contains its own calibrated `cal_low` and `cal_high` bounds calculated from the canonical pole opposites (`deontological` vs `consequentialist`, `particular` vs `universal`).

### Blindspot 3: Latency & Zero-Exception Offline Fallback
* **Analysis:** Network latency or offline environments must never block or crash a Claude Code session.
* **Resolution:**
  * Strict timeout (default: 5.0 seconds).
  * Automatic graceful fallback to the local BGE `GeometricBridge` upon missing API keys, HTTP errors (401, 429, 500), or timeouts.

### Blindspot 4: Full-Contextual Advantage
* **Analysis:** Replacing static dictionary averaging with live transformer sequence encoding unlocks true multi-clause semantic understanding. Self-attention natively disambiguates polysemous words ("quantum state" vs "police state") without manual token regexes.

---

## 3. Vetting Phase 2: Codebase Reality Audit

An end-to-end inspection of the repository confirmed the exact structural integration points:

| Codebase Element | Reality | Plan Requirement |
|---|---|---|
| **Pipeline Invariance** | Stages 2–8 in `pipeline/` only consume `state.partial_coordinate`. | Changes are strictly isolated to Stage 1 (`IntentParser`) and the math/provider layer. |
| **Dependency Purity (ADR-005)** | Wheel dependencies are strictly `networkx`, `numpy`, `mcp`. | HTTP clients for OpenAI and Gemini are implemented using Python standard library `urllib.request` + `json`. Zero external SDKs added to dependencies. |
| **Wheel Packaging** | `pyproject.toml` uses `hatchling` with `force-include` for data files. | `cloud_anchors_*.npz` files are added to `force-include` to ship inside wheels. |
| **MCP / CLI Integration** | Launched via stdio (`__main__.py` -> `server.py`). | Reads `APE_EMBEDDING_PROVIDER` and API keys from `os.environ` or `.mcp.json` `env` blocks. |
| **Test Suite Baseline** | 366 unit/integration tests pass in ~5.5s offline. | All 366 tests continue passing offline; new provider tests mock HTTP responses cleanly. |

---

## 4. Planned Architecture

```
                                  [User Intent String]
                                           │
                                           ▼
                            [Config: APE_EMBEDDING_PROVIDER]
                             /                            \
              "local" (Default)                  "openai" / "gemini"
                     │                                     │
                     ▼                                     ▼
        ┌─────────────────────────┐           ┌─────────────────────────┐
        │     GeometricBridge     │           │  CloudEmbeddingProvider │
        │  • Tokenize & IDF avg   │           │  • stdlib HTTPS request │
        │  • BGE 1024d static npz │           │  • 3072d / 2048d vector │
        └────────────┬────────────┘           └────────────┬────────────┘
                     │                                     │
                     │                                     ▼
                     │                        ┌─────────────────────────┐
                     │                        │   CloudSemanticBridge   │
                     │                        │  • 12 Face Centroids    │
                     │                        │  • 24 Axis Projections  │
                     │                        │  • 3 Phase Modulation   │
                     │                        └────────────┬────────────┘
                     │                                     │
                     └──────────────────┬──────────────────┘
                                        │
                                        ▼
                         [Stage 1: partial_coordinate]
                                        │
                                        ▼
                            [Stages 2–8: Downstream]
```

---

## 5. Implementation Roadmap

1. **Provider Subsystem (`src/advanced_prompting_engine/providers/`):**
   * `base.py`: Abstract `BaseEmbeddingProvider`.
   * `config.py`: Environment variable configuration (`APE_EMBEDDING_PROVIDER`, keys, models, timeouts).
   * `openai.py`: Standard library HTTPS client for OpenAI (`text-embedding-3-large` @ 3072d).
   * `gemini.py`: Standard library HTTPS client for Gemini (`text-embedding-005` @ 2048d).
   * `factory.py`: Provider instantiation with silent fallback.
2. **Cloud Math Layer (`src/advanced_prompting_engine/math/`):**
   * `cloud_bridge.py`: Matrix multiplications for face relevance, axis projections, and phase weighting.
3. **Data Artifacts & Build Tools:**
   * `src/advanced_prompting_engine/data/cloud_anchors_openai_3072.npz`.
   * `src/advanced_prompting_engine/data/cloud_anchors_gemini_2048.npz`.
   * `scripts/build_cloud_anchors.py`: Generator script for cloud anchors.
   * `pyproject.toml`: Add cloud anchors to `force-include`.
4. **Pipeline Integration:**
   * Update `IntentParser` to route through active provider.
   * Update `PipelineRunner` and `server.py` to initialize provider subsystem.
5. **Documentation & Records:**
   * Create `docs/adr/015-pluggable-cloud-embeddings.md`.
   * Update `README.md` and `CLAUDE.md`.
6. **Testing & Verification:**
   * Provider unit tests (`tests/test_providers/`).
   * Math tests for cloud bridge (`tests/test_math/test_cloud_bridge.py`).
   * Pipeline fallback and integration tests.
   * Full test suite verification (366+ tests passing).
