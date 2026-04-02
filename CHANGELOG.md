# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.2.0]: https://github.com/JoshuaRamirez/advanced-prompting-engine/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/JoshuaRamirez/advanced-prompting-engine/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/JoshuaRamirez/advanced-prompting-engine/releases/tag/v0.1.0
