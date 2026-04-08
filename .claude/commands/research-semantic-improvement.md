# Research: Semantic Bridge Improvement

Design a research plan to advance a philosophical intent measurement instrument from its current literary text benchmark score to 20/20 across Shakespeare, Genesis, Marx, MLK, Newton, Aristotle, Tao Te Ching, and Descartes. The instrument embodies a twelve-face geometric manifold where each face is a 12x12 grid with constitutive character on the x-axis and dispositional orientation on the y-axis. Its parser inverts three inference layers — axis meta-meaning, polarity convention, and sub-dimensions — by projecting intent tokens onto pre-computed GloVe 100d direction vectors. Remaining failures stem from: word polysemy where context determines domain, centroid broadness where some faces attract generic vocabulary, and vocabulary gaps where literary terms fall outside the word bridge. The research plan must systematically evaluate: (1) multi-sense static embeddings that provide sense-specific vectors without runtime neural inference — assess LMMS, sensEmbed, DeConf, and AutoExtend for GloVe compatibility and numpy-only resolution; (2) smooth inverse frequency sentence composition (Arora et al. 2017) as a replacement for simple word averaging — assess whether the principal component removal step sharpens face discrimination; (3) counter-fitting with antonym-only constraints and no face-cohort attraction to avoid centroid destabilization; (4) product quantization or dimensionality-indexed vocabulary expansion to cover 50K words within 10MB artifact budget; (5) character n-gram approximation for out-of-vocabulary literary terms using pre-computed prefix/suffix tables. For each technique, provide: expected improvement rationale, mathematical formulation, numpy implementation sketch, artifact size estimate, and risk assessment. Rank by expected impact on the specific benchmark failures.

## Constraints

- **Runtime**: numpy only. No torch, tensorflow, onnxruntime, spacy, gensim, nltk.
- **Artifacts**: Ship with pip package. Under 10MB total.
- **Build time**: Any tool on developer machine. GloVe 6B already cached.
- **Architecture**: GeometricBridge loads pre-computed numpy arrays, intent parser tokenizes + looks up + averages. Improvements produce better arrays, not change runtime flow.

## Context

Read these files before researching:
- `docs/CONSTRUCT-v2.md` — the philosophical geometry specification
- `docs/specs/semantic-bridge-algorithms.md` — current algorithm specifications
- `scripts/build_semantic_bridge.py` — current build script
- `src/advanced_prompting_engine/math/semantic.py` — runtime GeometricBridge
- `Documentation/Temporary/Execution/Results-V2Rebuild.md` — current benchmark results

## Before Starting

Read the context files listed above to understand:
- Current benchmark score and specific failures
- What techniques have already been tried (check Results doc)
- Current algorithm specifications
- Current build script implementation

Do NOT assume any specific score or failure pattern — read the current state from the project files.

## Research Questions

For each technique in the main prompt above, search the web, academic papers, and open-source projects. Also investigate:

1. **Retrofitting parameter tuning**: What settings work for domain-specific retrofitting? Variants that avoid destabilization? Search: "retrofitting word vectors parameters", "counter-fitting tuning".

2. **Sense-aware static embeddings**: Models with MULTIPLE vectors per word? Search: "sense embeddings", "multi-prototype embeddings", "LMMS", "sensEmbed", "DeConf", "AutoExtend".

3. **SIF sentence composition**: Smooth inverse frequency (Arora 2017) — does PCA removal step help domain discrimination? Search: "SIF embeddings", "smooth inverse frequency", "sentence embeddings without deep learning".

4. **Vocabulary expansion without size explosion**: Product quantization, dimensionality-indexed compression. Search: "embedding compression", "product quantization word vectors".

5. **OOV term approximation**: Character n-gram methods without FastText models. Search: "mimick model", "subword embeddings without neural networks", "character-level word embeddings".

## Assessment Criteria

For each technique found, assess:
- Does it work with numpy only at runtime?
- What's the artifact size impact?
- What's the expected quality improvement for the specific failures found in the results doc?
- How complex is the build-time implementation?
- Are there open-source implementations or reference code?

Recommend the top 3 most promising techniques with implementation sketches.
