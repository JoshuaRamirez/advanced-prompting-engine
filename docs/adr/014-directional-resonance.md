# ADR-014: Directional resonance for cube pairs

## Status

Accepted (v0.8.0)

## Context

Cube pairs (ADR-002) are symmetric — `(ontology, praxeology)`,
`(epistemology, methodology)`, etc. The harmonization metric
(`math/harmonization.py`) computes `resonance = alignment × √(cov_a × cov_b)`,
which requires both faces to be densely activated AND aligned to produce
a high score.

A field observation surfaced during refinement work (documented in
`docs/cc_genui_20260420_200730_face_importance_ranking.html`, Principle 4)
showed that this metric systematically under-reports prompts that
**legitimately** address one face more densely than the other:

- Execution prompts that inherit a pre-designed plan describe entities
  (ontology) explicitly but carry action-structure (praxeology) implicitly.
  The `ontology↔praxeology` pair scored ~0.11 resonance in every iteration
  despite both faces being genuinely addressed.

The symmetric metric cannot distinguish "both weakly present" from
"grounding strongly present, grounded implicitly inherited". A directional
relation between the paired faces is required.

## Decision

Introduce a per-pair directional grounding mapping and a new
`directional_resonance` metric alongside the existing symmetric one.

### Grounding directions

Defined in `src/advanced_prompting_engine/graph/schema.py` as
`CUBE_PAIR_DIRECTIONS` — a dict whose key is the grounding face and
whose value is the grounded face:

| Grounding → Grounded | Philosophical reading |
|---|---|
| ontology → praxeology | being grounds doing |
| epistemology → methodology | knowing grounds proceeding |
| ethics → axiology | obligation grounds worth (classical evaluative triad: teleology → ethics → axiology) |
| teleology → heuristics | purpose grounds strategy |
| phenomenology → aesthetics | experience grounds form |
| semiotics → hermeneutics | encoding grounds decoding |

### Directional resonance metric

For a pair with grounding face G and grounded face D:

```
directional_resonance = alignment(D → G) × coverage(G)
```

- `alignment(D → G)` — for each active construct on D, find the nearest
  active construct on G and average proximity. Measures whether the
  grounded face's positions are grounded in the grounding face's positions.
- `coverage(G)` — activated potency on G as a ratio of max potency. Credits
  the pattern "grounding present, grounded inherited" by carrying the
  grounding face's coverage independent of the grounded face's density.

When either face is empty, `directional_resonance = 0`. When grounding is
absent but grounded is activated, the score is zero — this surfaces the
"evaluative without grounding" pattern that the foundation-precedence
flag (v3 of the same report) also addresses at the face level.

### Symmetric resonance retained

`resonance` (the existing symmetric metric) is preserved unchanged. Both
metrics appear side-by-side in each pair's result, plus explicit
`grounding_face` and `grounded_face` fields so consumers can reason over
either.

## Consequences

### Positive

- Resolves the paired-face under-resonance failure mode for prompts that
  legitimately address one face densely and the other implicitly.
- Directional > symmetric on the "inherited plan" pattern (verified by
  the new `test_inherited_plan_pattern_directional_higher_than_symmetric`
  test).
- Carries no runtime dependency beyond numpy (ADR-005 preserved).
- Principle 4 from the face-importance-ranking report is now in the
  engine, not only in the skill's documentation.

### Negative

- Consumers that ignored the `grounding_face`/`grounded_face` fields or
  relied only on `resonance` get richer output but no behavioral change.
- The grounding directions are a philosophical commitment — ethics→axiology
  in particular follows Kantian lineage rather than a pragmatic worth-first
  reading. This is documented and intentional.

### Not addressed (deferred)

- The symmetric→directional framing does not replace the cube model. The
  6 pairs remain; the directionality is an overlay.
- Downstream effects on `math/gem.py` and the tension computation are
  unchanged — only harmonization exposes the directional metric. If gem
  magnitude should also be directional, that is a separate future ADR.

## Verification

- 6 new unit tests in `tests/test_math/test_harmonization.py`:
  - `TestCubePairDirections` (4 tests — schema integrity)
  - `TestDirectionalResonance` (6 tests — metric behavior including the
    field-observation case)
- Benchmark (`scripts/benchmark_8texts.py`) unchanged at 18/20 after v4
  (no regression from v3+v4 added together).
- Smoke test on the ethics-heavy field prompt shows
  `directional_resonance > resonance` for `ethics→axiology` when ethics
  is genuinely inhabited, consistent with the metric's design.
