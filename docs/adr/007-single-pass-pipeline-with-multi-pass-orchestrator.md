# ADR-007: Single Forward-Pass Pipeline with Multi-Pass Orchestrator Above

**Date**: 2026-03-27
**Status**: Accepted

## Context

The engine's primary operation (`create_prompt_basis`) transforms a natural language intent into a construction basis through 7 stages. Two additional operations (`stress_test`, `triangulate`) require running the pipeline multiple times with different inputs.

Design options:
1. Pipeline with internal feedback loops (stages can re-invoke earlier stages)
2. Single forward-pass pipeline with multi-pass orchestration above it
3. Recursive pipeline (pipeline calls itself with modified inputs)

## Decision

The pipeline is a **single forward pass** — data flows from Stage 1 to Stage 7 with no backward loops. Multi-pass operations (`stress_test`, `triangulate`) live in a **Multi-Pass Orchestrator** that invokes the pipeline N times and compares results.

## Rationale

- Forward-only pipeline is simpler to reason about, test, and debug
- Each stage has a well-defined input type and output type — no cyclic type dependencies
- Pipeline stages can be unit-tested in isolation by constructing their input directly
- Multi-pass operations have fundamentally different computational cost profiles (100x pipeline runs for stress test) — they should be explicitly opt-in, not hidden inside the pipeline
- The orchestrator pattern cleanly separates "compute one result" from "compare multiple results"

## Consequences

- **Positive**: Pipeline stages are pure functions of their input + graph state — deterministic and testable
- **Positive**: Single pipeline run has predictable, bounded execution time (~50-100ms)
- **Positive**: Multi-pass operations are explicit about their computational cost
- **Negative**: No in-pipeline optimization — the Construction Bridge cannot automatically re-run earlier stages with better parameters
- **Negative**: Client must explicitly request stress testing or triangulation — the primary tool returns a single-pass result
- **Trade-off**: The pipeline produces a "first-pass best" result, not a globally optimal one. Global optimization requires the Multi-Pass Orchestrator. This is accepted because: (1) the first pass is good enough for most use cases, and (2) optimization cost should be explicit and client-controlled.
