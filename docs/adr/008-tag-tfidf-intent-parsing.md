# ADR-008: Tag-Based + TF-IDF Intent Parsing (No LLM Dependency)

**Date**: 2026-03-27
**Status**: Accepted

## Context

The Intent Parser must transform natural language intent into a partial coordinate (construct positions across the 10 axiom branches). This requires some form of natural language understanding.

Options:
1. **LLM-based parsing**: Use the calling LLM or an embedded model to interpret intent. High quality but creates a circular dependency (prompt engine depends on an LLM) and violates self-containment.
2. **Embedding model**: Use a pre-trained sentence embedding model (e.g., sentence-transformers) for semantic similarity. Better than keywords but adds a large ML dependency (~500MB+).
3. **Tag matching + TF-IDF**: Each construct carries keyword tags. Match input tokens against tags (fast, high precision). Use TF-IDF cosine similarity against construct descriptions for synonym handling (moderate quality, no ML dependency).
4. **Accept pre-formed coordinates only**: Bypass NL parsing entirely. Shifts all interpretation to the client.

## Decision

Use **two-tier matching: tag overlap + TF-IDF cosine similarity**, both implemented with numpy only. Also accept pre-formed coordinate objects, bypassing the parser entirely.

Matching formula: `combined_score = tag_score × 0.6 + tfidf_score × 0.4`

Weight and confidence are derived separately:
- **confidence** = combined match score (how certain is the construct assignment)
- **weight** = token emphasis (how prominent is this branch in the intent)

## Rationale

- No LLM dependency — the engine is a pure instrument, not a consumer of AI inference
- No ML model dependency — no sentence-transformers, no 500MB downloads
- TF-IDF is mathematically simple, fully deterministic, and implementable in ~50 lines of numpy
- Tag matching provides high-precision first-pass; TF-IDF catches synonyms and related terms
- Pre-formed coordinates give sophisticated clients (especially LLMs that have read the `coordinate_schema` resource) a direct path that bypasses the parser entirely
- The parser only needs to be "good enough" — the Coordinate Resolver (Stage 2) fills gaps and validates, so imperfect parsing is tolerable

## Consequences

- **Positive**: Zero AI/ML dependencies — fully self-contained
- **Positive**: Deterministic — same input always produces same coordinate
- **Positive**: Tag quality is author-controlled — canonical constructs ship with curated tags
- **Positive**: LLM clients can bypass the parser by providing coordinates directly
- **Negative**: Lower quality NL understanding than an LLM-based parser — misses nuance, context, multi-word phrases
- **Negative**: Tag authoring is manual labor — each construct needs well-chosen keywords
- **Negative**: TF-IDF is bag-of-words — word order and sentence structure are ignored
- **Trade-off**: Parsing quality vs. self-containment. Self-containment wins. The engine is an instrument — it should not depend on the thing it is designed to help.
