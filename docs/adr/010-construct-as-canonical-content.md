# ADR-010: Construct Epistemic Questions as Canonical Content

**Date**: 2026-03-27
**Status**: Accepted

## Context

The original design left the Schema Layer (Level 2) unpopulated. The engine was a fully specified instrument with no sample — the structure was complete but the 1000 construct positions were empty. Populating them required a Knowledge Engineer to author domain-specific content for each position.

The Construct specification includes 100 structurally-defined epistemic questions — one per grid position — each carrying positional semantics (corner, midpoint, edge, center). These questions are universal: they describe the nature of observation, possibility, and force at each structural position, regardless of domain.

The 10 philosophical branches provide domain parameterization. The cross-product of 100 positional questions × 10 branches produces 1000 uniquely defined constructs.

The question: should the shipped canonical graph be populated with these questions?

## Decision

**Yes.** The Construct's epistemic questions, parameterized across the 10 branches, are the shipped canonical content. The engine is operational on first activation.

### Content Structure

Each of the 1000 constructs contains:
- The Construct's structural question for its grid position, parameterized by its branch
- A description combining positional role with the branch's core question
- Tags derived from the question's key terms (for TF-IDF matching)
- Classification, potency, and spectrum membership (from grid position)

### Example

Position (3, 0) on the Epistemology plane:
```
id: epistemology.3_0
x: 3, y: 0
classification: edge
potency: 0.85
question: "What initiating polarity lies within the early
           divergence of epistemological lanes?"
tags: [initiating, polarity, divergence, epistemological, verification, lanes]
```

The same structural question at (3, 0) on the Methodology plane:
```
id: methodology.3_0
question: "What initiating polarity lies within the early
           divergence of methodological lanes?"
```

Same structural role. Different philosophical domain.

## Rationale

- The Construct's questions are structurally universal — they describe the epistemic nature of each position, not domain-specific content. They apply to any topic (validated by the Memory analysis example).
- The engine becomes immediately operational — no authoring phase, no Knowledge Engineer required for baseline use.
- The questions serve triple duty: they are **content** (TF-IDF vectorizable), **structure** (grid-positioned), and **guidance** (epistemic probes that direct prompt construction). This eliminates the interpretive gap without requiring runtime synthesis.
- TF-IDF vector colocation works naturally: the questions' semantic content is embedded in the same vector space as client intent. Proximity determines which structurally-meaningful positions activate.
- User extensions become the domain-specific layer — canonical provides the universal scaffold, users add domain vocabulary on top.
- The seam between structure and content vanishes — the structure IS the content.

## Consequences

- **Positive**: Engine ships operational — `create_prompt_basis` works on first call
- **Positive**: No interpretive gap — the predefined questions carry the guidance that the pipeline cannot synthesize
- **Positive**: 200 auto-generated spectrums have semantically rich endpoints (both endpoint questions are defined)
- **Positive**: User extensions compose naturally — domain-specific constructs layer on top of universal epistemic questions
- **Negative**: The 100 base questions must be authored once with care — they define the canonical epistemic framework permanently
- **Negative**: Parameterization across 10 branches may not be perfectly mechanical — some branches may need per-branch customization of the base questions
- **Negative**: The canonical content is philosophically opinionated — it encodes a specific epistemic framework. Users who disagree with the framework's assumptions must work within or extend it, not replace it.
- **Trade-off**: Universality vs. domain specificity. The canonical content is intentionally domain-agnostic. This makes it universal but also abstract. Domain-specific utility requires user extensions.
