# Contributing to Advanced Prompting Engine

Thank you for your interest in contributing. This document explains how to get started.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/JoshuaRamirez/advanced-prompting-engine.git
cd advanced-prompting-engine

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run the test suite
pytest tests/ -v
```

## Semantic Bridge Build (for contributors modifying the intent parser)

The intent parser uses pre-computed GloVe-derived artifacts shipped in `src/advanced_prompting_engine/data/`. These artifacts are committed to the repo, so most contributors don't need to rebuild them. **You only need to run the build script if you modify pole synonyms, disambiguation entries, phrase lists, or the build pipeline itself.**

```bash
# First run downloads GloVe 6B (~862MB) to ~/.cache/glove/
# Subsequent runs use the cached file.
python3 scripts/build_semantic_bridge.py
```

The build script:
1. Loads GloVe 6B 100d word vectors (400K words)
2. Selects ~20K runtime vocabulary (top 15K frequent + domain-specific + question-guided expansion)
3. Builds 12 face centroids from authored layers (core questions, sub-dimension labels, pole synonyms)
4. Builds 24 axis direction vectors (high_pole - low_pole per axis)
5. Pre-computes per-word face similarity, axis projections, IDF weights, phase similarity, question positions
6. Computes contextual disambiguation table (15 polysemous triggers)
7. Computes n-gram phrase embeddings (92 curated phrases)
8. Saves artifacts to `src/advanced_prompting_engine/data/`
9. Runs 24 pole self-tests (all must pass)

Output artifacts: `semantic_bridge.npz` (~2MB) + `semantic_vocab.json` (~300KB).

## Project Structure

```
src/advanced_prompting_engine/
  graph/        # Data layer: schema, grid, canonical content, store, query, mutation
  cache/        # Embedding (stub), TF-IDF, centrality (stub), hashing
  math/         # Computation: tension, gem, spoke, harmonization, semantic bridge, TF-IDF, optimization
  pipeline/     # 8-stage forward pass: intent→coordinate→position→constructs→tensions→gems→spokes→output
  orchestrator/ # Multi-pass: stress_test, triangulate, deepen
  tools/        # MCP tool handlers: create_prompt_basis, explore_space, extend_schema
  data/         # Pre-computed semantic bridge artifacts (GloVe-derived)
  server.py     # MCP server setup, tool/resource/prompt registration
```

See `CLAUDE.md` for the full project structure, conventions, and terminology.

## Architecture Overview

The engine is a 12-face philosophical manifold:

- **12 faces** (philosophical domains), each a **12x12 grid** of 144 observation points
- **Axis meta-meaning**: x = constitutive character, y = dispositional orientation
- **Polarity convention**: low (0) = constrained, high (11) = expansive
- **6 cube pairs** for harmonization (theoretical ↔ applied counterparts)
- **66 nexi** stratified by cube model: 6 paired + 48 adjacent + 12 opposite
- **Geometry-integral parser**: inverts the 3 inference layers (axes, polarity, sub-dimensions) via GloVe projection

Key documents:
- `docs/CONSTRUCT-v2.md` — what faces, points, nexi, gems, spokes ARE
- `docs/DESIGN.md` — how the engine implements the specification
- `docs/adr/` — 12 Architecture Decision Records explaining key choices

## Code Conventions

- **"Face" not "branch."** Each domain is a face of the Construct, not a branch.
- **One class per file.** Even small classes get their own module.
- **No direct NetworkX calls outside `graph/`.** All graph access goes through the Query or Mutation layers.
- **Pipeline stages are internal.** Never exposed as MCP tools.
- **Math modules are pure computation.** They take numpy arrays and dicts, not graph objects.
- **Canonical data is immutable.** SQLite triggers prevent modification. User extensions go in separate tables.
- **Concise comments preferred.** Use doc-comments on stable public interfaces.

## Making Changes

1. Fork the repository and create a feature branch from `main`.
2. Make your changes, following the conventions above.
3. Add or update tests for any changed behavior.
4. Run the full test suite: `pytest tests/ -v`
5. If you modified the semantic bridge, rebuild artifacts: `python3 scripts/build_semantic_bridge.py`
6. Verify the package builds: `python -m build`
7. Submit a pull request against `main`.

## Pull Request Guidelines

- Keep PRs focused on a single concern.
- Reference any related issues in the PR description.
- Ensure CI passes (tests across Python 3.10-3.14, syntax check, build verification).
- Do not modify canonical graph data (`graph/canonical.py`) without discussion.
- Do not modify the Construct specification (`docs/CONSTRUCT-v2.md`) without discussion.

## Architecture Decisions

Significant design changes should be proposed as Architecture Decision Records (ADRs) in `docs/adr/`. Read the existing ADRs before proposing changes to understand prior decisions and their rationale. Key ADRs:

- **ADR-002**: 12-axis philosophical manifold with Vector Equilibrium + cube pairing
- **ADR-005**: numpy as sole additional computational dependency (no scipy, no scikit-learn)
- **ADR-008**: Tag-based + TF-IDF intent parsing (no LLM dependency)
- **ADR-009**: Grid-structured schema layer (12x12, invariant axis meta-meaning, polarity convention)

## Bug Reports and Feature Requests

- Use [GitHub Issues](https://github.com/JoshuaRamirez/advanced-prompting-engine/issues).
- For bugs, include: Python version, OS, steps to reproduce, expected vs. actual behavior.
- For features, describe the use case and how it relates to the existing Construct model.

## Security Issues

Do not open public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md) for responsible disclosure instructions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
