# Roadmap: V2 Construct Rebuild

## Strategic Goal

Rebuild the Universal Prompt Creation Engine from a 10-branch/10x10 architecture to a 12-face/12x12 architecture based on the v2 Construct specification. Complete replacement, no merge.

## Why

The Construct expanded from 10 to 12 philosophical domains (Ethics and Aesthetics split from Axiology). The grid size matches the face count (12x12). The v2 spec introduces axis meta-meaning, polarity convention, cube pairing, nexus stratification, positional correspondence, and harmonization — none of which existed in v1. The changes are too pervasive for incremental patching.

## What

- Rewrite all source files in `src/advanced_prompting_engine/` to implement the v2 spec
- Update or replace all documentation in `docs/`
- Rewrite all tests
- Validate that the engine starts, computes, and produces correct output

## Capabilities (bottom-up)

| # | Capability | Description |
|---|---|---|
| 1 | v2 Specification | CONSTRUCT-v2.md, question templates, DESIGN.md, ADRs |
| 2 | Data Layer | schema.py, grid.py, canonical.py, store.py |
| 3 | Graph Access | query.py, mutation.py |
| 4 | Caches | embedding.py (evaluate need), tfidf.py |
| 5 | Math Modules | Drop 5 unnecessary modules, rethink 3, update 2 |
| 6 | Pipeline Stages | 8 stages updated for v2 geometry |
| 7 | MCP Server | server.py, tools/*.py — surface stable, internals change |
| 8 | Tests | Full test rewrite |
| 9 | Integration | End-to-end validation |
