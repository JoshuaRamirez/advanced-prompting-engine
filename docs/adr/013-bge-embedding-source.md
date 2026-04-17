# ADR-013: BGE-large-en-v1.5 as Sole Embedding Source

**Date**: 2026-04-16
**Status**: Accepted
**Supersedes (for embeddings)**: ADR-008 rationale on "no ML dependency" — clarifies scope to *runtime* only

## Context

The GeometricBridge projects natural-language intent onto the Construct's 12
faces and 24 axis directions using pre-computed per-word artifacts. Prior
builds used GloVe 6B 100d or Model2Vec (distilled sentence-transformer) with
a face-informed QR+PCA reduction to 100 dimensions.

Observed failure on the 8-text literary benchmark: baseline score 13/20,
with phenomenology dominating top-1 in 6/8 texts and axiology / hermeneutics
/ aesthetics structurally suppressed at ranks 9-11. This is the "domain
ceiling" symptom described in the GloVe-upgrade analysis: static per-word
vectors cannot disambiguate philosophical vocabulary by context, cannot
compose multi-word concepts except by averaging, and inherit corpus
mismatches from their 2014-era training data.

## Decision

Replace the build-time embedding source with **BAAI/bge-large-en-v1.5** at
its **native 1024 dimensions**. No dimensionality reduction. No fallback
chain. GloVe and Model2Vec paths are removed entirely.

Frequency ordering and top-N vocabulary selection derive from **wordfreq**.
GloVe is no longer a dependency of any kind.

## Rationale

- **Contextual encoding** breaks the single-word-in-null-context ceiling for
  phrases, questions, and multi-word pole synonyms.
- **Native dimensionality preserves information.** The QR+PCA face-informed
  reduction existed only to compensate for Model2Vec compression to 100d.
  With BGE at 1024d and no compression, that compensation machinery is
  retired.
- **Artifact size is dim-independent.** The shipped npz stores projections
  (N × 12 face_sim, N × 24 axis_proj, N × 3 phase_sim), not raw vectors.
  Embedding dim affects build-time compute only.
- **Runtime remains pure.** BGE is a build-time dependency under the
  `[build]` extra. Plugin consumers install only `numpy`, `networkx`, `mcp`
  and receive the pre-computed artifacts. ADR-005 holds.
- **wordfreq is a principled frequency blend** (SUBTLEX + Wikipedia +
  Google Books + Twitter + news + Reddit, geometric-mean weighted). DIY
  combination of corpora would be less rigorous.

## Consequences

- **Positive**: BGE-quality contextual embeddings applied to every word,
  phrase, and question.
- **Positive**: Questions and phrases encoded as **full sentences** rather
  than as IDF-weighted word-vector averages. This uses BGE's contextual
  strength where it matters most.
- **Positive**: Deleted ~1300 lines from the build script — no face-informed
  projection, no counter-fitting (disabled for first measurement), no OOV
  expansion pass, no 400K→15K trimming.
- **Positive**: Vocabulary is a single unified set (no full/runtime split).
  Only words that will appear in shipped artifacts are encoded.
- **Neutral**: Build time increases substantially (BGE is a 335M-param
  transformer vs. Model2Vec's static lookup). GPU recommended; CPU works
  for ~20-30K vocab in reasonable time.
- **Trade-off**: `[build]` extra adds sentence-transformers + torch +
  wordfreq + nltk (~600 MB of libraries) on developer machines. Not shipped.
- **Open**: Retrofitting / counter-fitting is disabled for this phase to
  isolate the embedding-source variable. A future decision will determine
  whether contextual embeddings still benefit from it.

## Related

- ADR-005 — numpy as sole runtime dependency (unchanged)
- ADR-008 — TF-IDF/tag intent parsing rationale (still applies to the
  runtime bridge; "no ML at runtime" is preserved)
- ADR-012 — spoke behavioral signature (consumer of face_sim/axis_proj
  artifacts; unaffected)
