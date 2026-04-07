# ADR-009: Grid-Structured Schema Layer

**Date**: 2026-04-03
**Status**: Accepted
**Supersedes**: ADR-009 (10x10 Grid-Structured Schema Layer, 2026-03-27)

## Context

The original Schema Layer used 10x10 grids (100 constructs per branch, 1000 total). The v2 Construct specification (`CONSTRUCT-v2.md`) expands the system to 12 faces with 12x12 grids, where 12 notches per axis correspond to 12 dimensions in the system. The grid size is not arbitrary — it matches the face count, ensuring each notch along an axis can represent one domain's worth of resolution.

Beyond increased size, v2 introduces three structural commitments that were absent in v1:

1. **Invariant axis meta-meaning** — the x-axis always means "constitutive character" (what kind of thing) and the y-axis always means "dispositional orientation" (how it engages). This holds across all 12 faces.
2. **Polarity convention** — low (0) = constrained, foundational, anchored. High (11) = expansive, synthetic, exploratory. This holds on every axis of every face.
3. **Inference machinery** — three authored layers (axis meta-meaning, polarity convention, sub-dimensions) combine to produce meaning at any coordinate mechanically.

The question: how should the Schema Layer adopt this richer grid structure?

## Decision

Replace 10x10 grids with **12x12 grids**. Each face contains exactly **144 constructs** arranged in a grid addressed by integer coordinates (0,0) through (11,11). Position determines classification, potency, spectrum membership, and semantic meaning through the inference machinery.

### Axis Meta-Meaning

The two axes carry invariant meaning across all 12 faces:

- **X-axis (constitutive character)**: What kind of thing this is within the domain. At x=0, the most elemental or foundational form. At x=11, the most comprehensive or expansive form.
- **Y-axis (dispositional orientation)**: How the thing moves, relates, or engages within the domain. At y=0, the most stable or grounded tendency. At y=11, the most fluid or exploratory tendency.

Each face instantiates these meta-axes with domain-specific sub-dimensions (e.g., Ontology: x = Particular -> Universal, y = Static -> Dynamic).

### Polarity Convention

For every face: x=0 and y=0 represent the constrained pole; x=11 and y=11 represent the expansive pole. This ensures the 4 corner archetypes hold invariantly:

| Corner | Position | Archetype |
|---|---|---|
| Alpha | (0,0) | Foundation — elemental nature fused with stable tendency |
| Beta | (11,0) | Extension — comprehensive nature fused with stable tendency |
| Gamma | (0,11) | Transformation — elemental nature fused with fluid tendency |
| Delta | (11,11) | Integration — comprehensive nature fused with fluid tendency |

### Point Classification

| Classification | Positions | Count per face | Potency |
|---|---|---|---|
| Corner | (0,0), (11,0), (0,11), (11,11) | 4 | Highest |
| Edge midpoint | Positions 5 and 6 on each edge | 8 | High |
| Other edge | Remaining perimeter positions | 32 | Moderate |
| Center | All interior positions (1-10, 1-10) | 100 | Lowest |

### Meaning Hierarchy

Meaning is produced at each structural level through a distinct mechanism:

```
Outer lines -> meaning by demarcation    (boundary established)
Inner lines -> meaning by graduation     (interior differentiated)
Crossings   -> meaning by composition    (two axes in ratio)
Corners     -> meaning by integration    (two axes fused)
Face        -> meaning by enclosure      (all ratios bounded)
```

### Inference Machinery

Three authored layers combine to determine meaning at any coordinate:

1. Axis meta-meaning (what x and y mean structurally)
2. Polarity convention (what low and high mean)
3. Sub-dimensions (what constitutive character and dispositional orientation mean in this specific domain)

These three layers produce meaning mechanically. No individual construct requires independent authoring — its meaning is computable from its position.

### Construct Identity

Node ID format: `face.x_y` (e.g., `epistemology.3_0`, `ethics.11_11`).

## Rationale

- Grid size matching face count (12x12 for 12 faces) is not cosmetic — each notch represents one domain's worth of resolution along each axis.
- Invariant axis meta-meaning enables cross-face geometric comparison: position (3,8) on any face means "moderately constrained constitutive character, moderately expansive dispositional orientation" before domain-specific meaning is applied.
- The polarity convention makes the 48 corners (4 per face x 12 faces) mechanically derivable from sub-dimensions. No corner is independently authored.
- The inference machinery reduces authoring requirements to three root decisions per face (which sub-dimension names to assign). All 144 positional meanings follow from those decisions.
- The meaning hierarchy (demarcation, graduation, composition, integration, enclosure) provides a formal account of how position produces meaning at each structural level.
- The 44/100 edge/center split per face provides a potency gradient that shapes tension and generative computation without additional configuration.

## Consequences

- **Positive**: Position determines meaning mechanically — 3 authored root decisions per face produce 144 positional meanings
- **Positive**: Cross-face comparison is geometric — same position on two faces shares the same structural archetype
- **Positive**: 48 corners (12 faces x 4 corners) are mechanically derived and fall into 4 invariant groups (Alpha, Beta, Gamma, Delta)
- **Positive**: The meaning hierarchy gives a formal vocabulary for what kind of meaning each structural element produces
- **Positive**: Spectrums arise from grid geometry — opposed edge points define structural oppositions without manual edge authoring
- **Negative**: Fixed at 144 per face — changing grid size breaks the 12-notch = 12-domain correspondence
- **Negative**: Node IDs are coordinate-based (`epistemology.3_0`) rather than semantically named — less self-documenting at the ID level
- **Negative**: The inference machinery's correctness depends on sub-dimension selection quality — poorly chosen sub-dimensions produce incoherent positional meanings
- **Trade-off**: Structural richness vs. authoring constraint. Every position demands content that matches its mechanically-derived meaning. This is intentional — the structure IS the authoring specification.
