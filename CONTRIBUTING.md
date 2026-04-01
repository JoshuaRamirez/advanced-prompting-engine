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

## Project Structure

- `src/advanced_prompting_engine/` -- Package source code
- `tests/` -- Test suite (mirrors source structure)
- `docs/` -- Design specification, Construct specification, ADRs

See `CLAUDE.md` for the full project structure and conventions.

## Code Conventions

- **One class per file.** Even small classes get their own module.
- **No direct NetworkX calls outside `graph/`.** All graph access goes through the Query or Mutation layers.
- **Pipeline stages are internal.** They are never exposed as MCP tools.
- **Type hints on all functions.** The package ships a `py.typed` marker (PEP 561).
- **Concise comments preferred.** Use doc-comments on stable public interfaces.

## Making Changes

1. Fork the repository and create a feature branch from `main`.
2. Make your changes, following the conventions above.
3. Add or update tests for any changed behavior.
4. Run the full test suite: `pytest tests/ -v`
5. Verify the package builds: `python -m build`
6. Submit a pull request against `main`.

## Pull Request Guidelines

- Keep PRs focused on a single concern.
- Reference any related issues in the PR description.
- Ensure CI passes (tests across Python 3.10--3.13, syntax check, build verification).
- Do not modify canonical graph data (`graph/canonical.py`) without discussion.

## Architecture Decisions

Significant design changes should be proposed as Architecture Decision Records (ADRs) in `docs/adr/`. Read the existing ADRs before proposing changes to understand prior decisions and their rationale.

## Bug Reports and Feature Requests

- Use [GitHub Issues](https://github.com/JoshuaRamirez/advanced-prompting-engine/issues).
- For bugs, include: Python version, OS, steps to reproduce, expected vs. actual behavior.
- For features, describe the use case and how it relates to the existing Construct model.

## Security Issues

Do not open public issues for security vulnerabilities. See [SECURITY.md](SECURITY.md) for responsible disclosure instructions.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
