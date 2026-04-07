# ADR-010: Construct as Canonical Content

**Date**: 2026-04-03
**Status**: Accepted
**Supersedes**: ADR-010 (Construct Epistemic Questions as Canonical Content, 2026-03-27)

## Context

The v2 Construct specification (`CONSTRUCT-v2.md`) introduces inference machinery (§14) that produces meaning at every grid position from three authored root decisions. This changes the canonical content strategy fundamentally: instead of 1000 independently authored questions (v1), the content is now 1728 questions generated from 144 parameterized templates applied across 12 domains.

The 144 templates are not arbitrary. Each template is derived from the geometric meaning at its grid position — read off from the inference machinery (axis meta-meaning, polarity convention, sub-dimensions) and phrased as a construction question. The templates contain a `{domain}` replacement string that is substituted with the domain-specific noun phrase for each face.

The question: should the shipped canonical content be this template-generated set?

## Decision

**Yes.** The Construct's 1728 constructs are shipped canonical content, generated from **144 question templates x 12 domains**. Each template is parameterized with `{domain}` and instantiated per face using the domain's replacement string.

### Template Derivation

Each template is authored by reading the geometric meaning at its grid position using the three inference layers:

1. Determine the constitutive character degree from the x-coordinate
2. Determine the dispositional orientation degree from the y-coordinate
3. Phrase the resulting meaning as a question useful for prompt construction

The template uses `{domain}` where domain-specific vocabulary belongs.

### Question Zones

The 144 templates are organized by zone, reflecting the structural role at each position type:

| Zone | Count | Character | Inference method |
|---|---|---|---|
| Corners | 4 | Fusion — two extremes collapsed into a single committed stance | Both axes at extreme; nothing varies |
| Edge midpoints | 8 | Balance at the boundary — axial equilibrium on the perimeter | One axis at extreme, other at balance |
| Other edge | 32 | One axis at full commitment, the other at a specified degree | One extreme held, other varying |
| Near-edge interior | 36 | Transition from pure edge stances to blended compositions | Both axes partially committed, one near boundary |
| Deep interior | 64 | Full composition — both axes blended at specified degrees | Neither axis near extreme |

### Domain Replacement Strings

Each domain maps to a noun phrase substituted for `{domain}` in templates:

| Domain | Replacement |
|---|---|
| Ontology | ontological existence |
| Epistemology | epistemological truth |
| Axiology | axiological evaluation |
| Teleology | teleological purpose |
| Phenomenology | phenomenological experience |
| Ethics | ethical obligation |
| Aesthetics | aesthetic recognition |
| Praxeology | praxeological action |
| Methodology | methodological practice |
| Semiotics | semiotic meaning |
| Hermeneutics | hermeneutic interpretation |
| Heuristics | heuristic strategy |

### Example

Position (0,0) template (corner — Alpha archetype):
```
"What is the most elemental, foundationally grounded form of {domain}?"
```

Instantiated for Ontology:
```
id: ontology.0_0
question: "What is the most elemental, foundationally grounded form of
           ontological existence?"
classification: corner
potency: highest
```

Instantiated for Ethics:
```
id: ethics.0_0
question: "What is the most elemental, foundationally grounded form of
           ethical obligation?"
classification: corner
potency: highest
```

Same template. Same structural role. Different philosophical domain.

## Rationale

- The inference machinery makes template authoring systematic: the meaning at each position is computable from three root decisions, so template content follows from geometry rather than independent invention.
- 144 templates are authored once. 1728 questions are generated mechanically. Adding a 13th domain would produce 144 more questions without new templates (though adding a domain requires a different polyhedron per ADR-002).
- Content scales with geometry. The relationship is multiplicative: templates x domains = constructs. Any change to the template set propagates uniformly across all domains.
- The engine ships operational on first activation — no authoring phase, no Knowledge Engineer required for baseline use.
- Questions serve triple duty: **content** (TF-IDF vectorizable for intent matching), **structure** (grid-positioned with classification and potency), and **guidance** (epistemic probes directing prompt construction).
- The seam between structure and content vanishes — the geometry determines the question, the question carries the geometry's meaning.

## Consequences

- **Positive**: Engine ships operational — `create_prompt_basis` works on first call with 1728 constructs
- **Positive**: Content scales with geometry — adding meaning requires only root-level changes (new sub-dimensions or template revisions), not per-construct authoring
- **Positive**: All 48 corners are mechanically derived and parameterized — no risk of corner questions contradicting their structural role
- **Positive**: Domain replacement strings ensure consistent vocabulary across all 144 positions within a face
- **Positive**: Question zones provide tractable authoring organization — 5 zones with distinct structural character rather than 144 undifferentiated positions
- **Negative**: The 144 base templates must be authored with care — they define the canonical epistemic framework permanently and must faithfully read the geometric meaning at each position
- **Negative**: The `{domain}` parameterization assumes all 12 domains can be questioned with the same structural template. Some domain-template combinations may produce awkward or imprecise questions. Per-domain template overrides may be needed as an escape valve.
- **Negative**: The canonical content encodes a specific epistemic framework. Users who disagree with the framework's assumptions must work within or extend it, not replace it.
- **Trade-off**: Universality vs. domain specificity. Template-generated content is intentionally domain-agnostic at the template level. Domain-specific utility requires either well-chosen replacement strings or user extensions layered on top.
