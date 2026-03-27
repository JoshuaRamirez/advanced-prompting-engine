# ADR-003: 3-Tool External Surface

**Date**: 2026-03-27
**Status**: Accepted

## Context

Initial design exposed 23 tools organized in 5 tiers (Entry, Schema Discovery, Schema Authoring, Coordinate Computation, Construction Basis). Analysis of LLM client ergonomics revealed:

1. 23 tools creates excessive cognitive load for cold discovery
2. No inherent ordering in a flat MCP tool list — LLM cannot determine sequencing
3. The layered architecture is invisible to the client
4. Most clients need the full pipeline, not individual stages
5. The gap between construction basis and prompt construction was not bridged

## Decision

Reduce external surface to **3 MCP tools**:
- `create_prompt_basis` — primary entry, full pipeline, intent in → construction basis out
- `explore_space` — expert access, graph traversal, stress testing, triangulation
- `extend_schema` — authoring with contradiction detection

The former 23 tools become internal pipeline operators, Graph Query Layer methods, Graph Mutation Layer methods, and Multi-Pass Orchestrator operations.

## Rationale

- One tool for the common case (`create_prompt_basis`)
- One tool for the exploratory case (`explore_space`)
- One tool for the authoring case (`extend_schema`)
- Three tiers of interface matching three tiers of client sophistication
- LLM clients see 3 tools with clear, distinct purposes — no sequencing ambiguity
- MCP prompts handle workflow sequencing when guided exploration is needed
- MCP resources provide reference material without tool calls

## Consequences

- **Positive**: LLM clients can immediately use the primary tool without understanding the internal architecture
- **Positive**: Internal pipeline operators are independently testable without MCP overhead
- **Positive**: The tool surface is client-agnostic — works for LLMs, developers, pipelines
- **Negative**: Fine-grained control requires using `explore_space` which bundles many operations behind one tool name — its parameter schema will be more complex
- **Negative**: `extend_schema` handles three distinct operations (add dimension, add construct, add relation) behind one tool — operation type must be a parameter
- **Trade-off**: Simplicity of discovery vs. granularity of control. Prioritized discovery.
