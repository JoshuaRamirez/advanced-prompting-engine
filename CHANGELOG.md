# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.1.1]: https://github.com/JoshuaRamirez/advanced-prompting-engine/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/JoshuaRamirez/advanced-prompting-engine/releases/tag/v0.1.0
