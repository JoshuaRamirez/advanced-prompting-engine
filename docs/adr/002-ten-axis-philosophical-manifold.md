# ADR-002: 10-Axis Philosophical Manifold as Level 1 Axiom Layer

**Date**: 2026-03-27
**Status**: Accepted

## Context

The engine needs a dimensional basis for the prompt construction space — a set of axes that any prompt for any purpose can be measured against. The basis must be:
- Universal (applies to any domain, any task type)
- Complete (no dimension of prompt construction is unrepresented)
- Grounded (each axis has philosophical precedent, not invented ad hoc)

Initial design iterations used ad-hoc dimensions ("CognitiveDimension", "BehavioralAxis") that were underdetermined and lacked formal foundation.

## Decision

Use **10 classical branches of philosophy** as the immutable Level 1 axiom layer:

1. Ontology — what entities exist
2. Epistemology — how truth is established
3. Axiology — what is valued
4. Teleology — what purpose is served
5. Phenomenology — how experience is represented
6. Praxeology — how action is structured
7. Methodology — what methods of inquiry are used
8. Semiotics — how meaning is communicated
9. Hermeneutics — how interpretation is handled
10. Heuristics — what strategies address the unknown

## Rationale

- Each branch is a classical philosophical discipline with centuries of formal development
- Together they partition the full space of concerns about any human-directed communication
- Each branch has a definable "core question" that maps directly to a dimension of prompt construction
- The branches have a natural causal ordering (Ontology → Epistemology → ... → Heuristics) that provides structural constraints on the graph
- 10 axes produce a coordinate object of manageable size for any client

## Consequences

- **Positive**: Universal — any prompt domain (code, creative, scientific, legal) is representable
- **Positive**: Each axis is independently meaningful — no redundancy
- **Positive**: The ordering provides built-in structural constraints (PRECEDES edges between Level 1 nodes)
- **Negative**: The set is fixed — adding an 11th axis is a breaking change to the coordinate schema
- **Negative**: Three branches (Hermeneutics, Phenomenology, Heuristics) describe properties that are philosophically non-deterministic, creating a tension with the engine's deterministic computational model. This tension is accepted — the engine measures positions on these axes, it does not practice the disciplines themselves.
- **Trade-off**: 10 is a human-comfortable number but is not mathematically derived. If a future analysis identifies that two axes are redundant or that an axis is missing, the axiom layer must be versioned.
