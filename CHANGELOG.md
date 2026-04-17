# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-04-16

### Added
- **BGE-large-en-v1.5 as sole embedding source** at native 1024d (ADR-013). Replaces GloVe + Model2Vec paths. Runtime remains numpy-only; BGE is a build-time dependency under a new `[build]` optional extra (`sentence-transformers`, `torch`, `wordfreq`, `nltk`).
- `wordfreq` for frequency ordering and top-N vocabulary selection — no more GloVe dependency of any kind.
- `FACE_VERNACULAR` dictionary — targeted object-level vocabulary for underperforming faces (ethics, axiology, methodology) only. Added at 4x weight in face centroid construction.
- `scripts/expand_pole_synonyms.py` — WordNet-based pole-synonym expansion proposals for human review.
- ADR-013: rationale for BGE as the sole build-time embedding source.

### Changed
- Build script rewritten (~2080 → ~770 lines). Deleted Model2Vec path, face-informed QR+PCA reduction, 400K→15K vocab trimming, OOV expansion, counter-fitting machinery. Single unified vocab.
- Questions and phrases are now encoded as **full sentences** through BGE, not as IDF-weighted word-vector averages.
- `face_relevance` uses **IDF² weighting** — rare face-specific vocabulary dominates the weighted average; common tokens no longer drown signal.
- 20% per-face column centering applied at artifact load — corrects systematic bias where "specific" face centroids (ethics, methodology) accumulated negative bias from generic tokens.
- Cube-pair contrast dampening **disabled**: the mechanism punished legitimate co-activations (ethics+axiology on moral rhetoric, epistemology+methodology on scientific texts). Re-enable only if evidence supports it.
- `docs/specs/semantic-bridge-algorithms.md` updated for BGE pipeline.

### Measurement
- Benchmark: `scripts/benchmark_8texts.py` score improved from **13/20 → 17/20** (+31%).
- Aesthetics moved from rank #10 to #1 on Aristotle's Poetics; methodology now hits top-6 on Newton; phenomenology-dominates-everything ceiling broken.

### Removed
- GloVe download/loading code paths.
- Model2Vec integration and PCA reduction machinery.
- `select_runtime_vocab` 400K→15K trimming (vocab is assembled directly from what's needed).
- `expand_vocab_by_question_proximity` OOV expansion pass.
- Counter-fitting SGD (retired pending evidence that contextual embeddings still benefit).

## [0.6.0] - 2026-04-13

### Added
- Synthesis/guidance layer in construction bridge (Stage 8): dominant dimensions, neglected dimensions with gap statements, strongest harmonization pair with cube pair concern, plain-language summary.
- Focused output mode: `create_prompt_basis(focused=true)` returns ~3KB guidance-centric output instead of ~695KB full pipeline data.
- `interpret_basis` MCP tool: takes construction basis JSON and returns markdown-formatted interpretation with dominant dimensions, gaps, and strongest resonance.
- `ape://examples` MCP resource: 4 annotated example intents demonstrating engine output interpretation.
- Per-face action guidance in `ape://axiom_manifest` resource: "If strongly activated: X. If weak: consider Y."
- `docs/GEOMETRY-NOTES.md`: latent polyhedral properties and structural capacities.
- 27 new tests: phase weighting, question position, disambiguation, phrase detection, MCP tool handlers.

### Changed
- MCP prompts rewritten with face definitions, interpretation guidance, and usage instructions.
- External surface: 4 tools (was 3), 4 resources (was 3), 4 prompts.
- 327 tests (up from 300).

### Fixed
- Dead causal propagation code removed (~40 lines).
- Float equality guard in gem computation (`== 0` → `< 1e-10`).
- Raw discriminative scores captured before phase mutation in intent parser.
- Test fixture expanded SYMMETRIC_RELATIONS for production graph parity.
- Consistent ALL_FACES fallback in face_relevance no-match paths.

## [0.5.0] - 2026-04-09

### Added
- Phase-aware face weighting: 3 phase centroids (comprehension/evaluation/application) provide 30% modulation on face relevance scores. Pre-computed per-word phase similarity matrix.
- Expanded contextual disambiguation: 15 trigger words with 15 context-aware senses (up from 8/10). Covers physics→methodology, drama→aesthetics, rhetoric→semiotics contexts.
- Per-face question position matching: pre-computed per-word best-matching question within each face. Phase 2 blends axis projection (40%) with question-matched position (60%).
- Question-guided vocabulary expansion: 15K→20K words selected by proximity to 1728 construction question embeddings (not generic frequency). Covers literary/archaic terms like "imitation", "catharsis", "sovereignty".
- Benchmark script (scripts/benchmark_8texts.py): 8-text literary benchmark across Shakespeare, Genesis, Marx, MLK, Newton, Aristotle, Tao Te Ching, Descartes.
- Model2Vec integration (conditional): if distilled sentence transformer exists at build time, uses Model2Vec vectors instead of GloVe. Currently disabled (GloVe outperforms for this domain).
- Semantic bridge algorithm specification (docs/specs/semantic-bridge-algorithms.md).
- `/pre-release` and `/release` project commands.
- `/research-semantic-improvement` research command.

### Changed
- Contrastive cube-pair dampening: 30% score transfer within each complementary pair, enforcing theoretical/applied distinction.
- Synonym decontamination: refined pole synonyms for Ethics, Aesthetics, Teleology, Axiology, Phenomenology, Praxeology to reduce cross-face vocabulary overlap.

### Performance
- Literary text benchmark: 18/20 expected faces in top 6 (up from 14/20 at v0.4.0 keyword-only baseline).
- Remaining 2 misses (MLK teleology, Newton methodology) are at the fundamental limit of word-level static embeddings.
- 300 tests passing (up from 261).

## [0.4.0] - 2026-04-07

### Added
- Geometry-integral intent parser: the parser IS the Construct's inference machinery running in reverse. Phase 1 projects intent onto face centroids (discriminative cosine similarity). Phase 2 projects onto axis direction vectors (high_pole - low_pole). Phase 3 maps scalars to grid via polarity convention.
- GloVe 6B 100d semantic bridge: 15K-word vocabulary with pre-computed face similarity and axis projection matrices. Built at dev time, ships as ~2MB numpy artifacts. Zero ML runtime dependencies.
- Contextual disambiguation table: 8 polysemous trigger words (state, compelled, right, deep, forces, heaven, tragedy, action) with 10 context-aware senses. Overrides face/axis scores when >= 2 context indicator words are present.
- N-gram phrase embeddings: 92 curated phrases (domain replacements, pole pair bigrams, philosophical key phrases). Greedy longest-match tokenizer with surface-to-canonical mapping.
- Contrastive cube-pair dampening: within each complementary pair, transfers 30% of score difference from weaker to stronger face.
- 46 pole synonym clusters (~320 curated words) for GloVe centroid construction.
- GeometricBridge class (replaces SemanticBridge): face_relevance() + axis_projection() with disambiguation and phrase support.
- 39 new tests for GeometricBridge and geometry-integral parser.
- Semantic bridge algorithm specification (docs/specs/semantic-bridge-algorithms.md).
- Build script (scripts/build_semantic_bridge.py) with pole self-test validation (all 24 axes pass).

### Changed
- Intent parser no longer uses TF-IDF or keyword matching for face/position selection — replaced by geometric projection.
- Tokenizer is now unstemmed (GloVe needs word forms) with expanded stop-word list (~95 words).
- Face centroids built from authored layers only (core questions + sub-dimension labels + pole synonyms) — NOT from derived question templates.

### Removed
- Keyword-based face matching (_FACE_KEYWORDS dictionary).
- TF-IDF dependency in Stage 1 (intent parser no longer queries construct questions).
- Stemming in intent parser tokenizer.

### Performance
- Literary text benchmark: 15/20 expected faces in top 6 across 8 benchmark texts (Shakespeare, Bible, Marx, MLK, Newton, Aristotle, Tao Te Ching, Descartes).
- 300 tests passing.

## [0.3.0] - 2026-04-07

### Changed (breaking)
- **12-face rebuild**: Complete reconstruction from 10-branch/10×10 to 12-face/12×12 architecture.
- 12 philosophical domains (added Ethics and Aesthetics as distinct faces; Axiology reframed as evaluative theory).
- 12×12 grids (144 points per face, 1728 total constructs, up from 1000).
- Invariant axis meta-meaning: x = constitutive character, y = dispositional orientation.
- Polarity convention: low = constrained/foundational, high = expansive/exploratory on all axes.
- "Face" terminology replaces "branch" throughout (backward-compat aliases retained).
- Graph: 1873 nodes, 2279 edges (up from 1101/1696).
- 66 unique nexus pairs (up from 45), 132 directional gems (up from 90), 12 spokes (up from 10).

### Added
- Cube pairing model: 6 complementary pairs with harmonization through shared surfaces.
- Nexus stratification: 6 paired + 48 adjacent + 12 opposite = 66, with tier-modulated computation.
- Positional correspondence: inter-face relationships via shared coordinate system (replaces 237 declared cross-face edges).
- Harmonization module: paired face resonance scoring with bidirectional positional alignment.
- Weight-modulated activation radius in construct resolver (face relevance affects activation footprint).
- Gem magnitude incorporates positional correspondence + cube tier modulation.
- Central gem coherence uses coefficient of variation for spoke differentiation.
- Meaning hierarchy in output: corners → integration, edges → demarcation, midpoints → axial_balance, center → composition.
- Causal phase classification: comprehension (1-5), evaluation (6-7), application (8-12).
- 144 authored question templates across 5 zones (corners, edge midpoints, other edge, near-edge interior, deep interior).
- 66 nexus definitions (21 new for Ethics/Aesthetics pairs).
- 66 first-principles compliance tests covering all 12 architectural principles.
- CONSTRUCT-v2.md specification (18 core commitments, 15 sections).
- CONSTRUCT-v2-questions.md (all 144 templates).
- Work effort triad (Roadmap, WorkEffort, Results).

### Removed
- 237 declared cross-face point-to-point edges (replaced by positional correspondence).
- 5 graph algorithm modules: spectral embedding, community detection, centrality, CSP, distance (v2 geometry is regular — computation is coordinate math).
- v1 specification files: CONSTRUCT.md, CONSTRUCT-INTEGRATION.md, 12 specs/ files.
- Spectrum questions and revisited questions (v2 derives spectrum meaning from sub-dimensions).

## [0.2.0] - 2026-04-01

### Added
- 170 canonical cross-branch edges (116 COMPATIBLE_WITH + 54 TENSIONS_WITH) connecting corner constructs across all 45 nexus pairs. Each edge philosophically derived from nexus definitions with justification.
- Sub-dimensional interpretation in construction basis output: `position_summary`, `x_interpretation`, `y_interpretation` with 7 strength levels (Strongly/Leaning/Slightly/Balanced).
- Compact output mode: `compact=true` on `create_prompt_basis` returns ~2KB summary instead of ~52KB full output.
- Cross-branch edge integrity tests (7 validations: valid IDs, no same-branch, no contradictions, all nexus pairs represented, valid relations, strengths in range).
- Orchestrator tests: stress_test, triangulate, deepen (graph mutation safety verified).
- Tool tests: extend_schema add_construct/add_relation with contradiction detection.

### Changed
- Total canonical edges: 1459 → 1629 (170 cross-branch edges added).
- Direct tensions now nonzero for diverse coordinates (was always 0).
- Gem harmony computation now produces differentiated results.

## [0.1.1] - 2026-03-30

### Added
- CI/CD workflows: test matrix (Python 3.10--3.13), build verification, PyPI publishing via trusted publisher.
- SECURITY.md, CONTRIBUTING.md, CHANGELOG.md, `.editorconfig`, `py.typed` marker.

### Fixed
- MCP tool parameter types for FastMCP compatibility.
- 4 data bugs in canonical graph data; removed dead spectrum lookup code.
- 3 bugs from second code review.

### Changed
- Improved NL intent matching with per-branch TF-IDF, two-phase resolution, and diversification.
- Comprehensive `.gitignore` for Python projects.

## [0.1.0] - 2026-03-27

### Added
- Initial release of the Universal Prompt Creation Engine.
- 10-axis philosophical manifold (Ontology, Epistemology, Axiology, Teleology, Phenomenology, Praxeology, Methodology, Semiotics, Hermeneutics, Heuristics).
- 3-level schema: Axiom Layer (10 branches), Schema Layer (10x10 grids, 1000 constructs), Coordinate Layer.
- Inter-branch architecture: 90 directional nexi, 90 gems, 10 spokes, 1 central gem.
- 8-stage pipeline: Intent Parser, Coordinate Resolver, Position Computer, Construct Resolver, Tension Analyzer, Nexus/Gem Analyzer, Spoke Analyzer, Construction Bridge.
- Multi-pass orchestrator: stress_test, triangulate, deepen.
- 3 MCP tools: `create_prompt_basis`, `explore_space`, `extend_schema`.
- SQLite persistence with canonical/user data separation.
- Spectral embedding cache and TF-IDF cache with lifecycle management.
- 12 Architecture Decision Records.

[0.7.0]: https://github.com/JoshuaRamirez/advanced-prompting-engine/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/JoshuaRamirez/advanced-prompting-engine/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/JoshuaRamirez/advanced-prompting-engine/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/JoshuaRamirez/advanced-prompting-engine/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/JoshuaRamirez/advanced-prompting-engine/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/JoshuaRamirez/advanced-prompting-engine/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/JoshuaRamirez/advanced-prompting-engine/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/JoshuaRamirez/advanced-prompting-engine/releases/tag/v0.1.0
