# Spec 03 — Canonical Content

## Purpose

Defines the canonical content that ships with the engine: point questions (construct node content), spectrum questions (SPECTRUM_OPPOSITION edge content), nexus interaction definitions, and the central gem definition.

**Authoritative source:** `03a-source-questions.md` contains the 100 original epistemic questions. This spec maps them to engine structures.

---

## Content Architecture

The source material contains three kinds of content, not one:

| Source range | Count | Content type | Maps to |
|---|---|---|---|
| Q1-Q36 | 36 | Point questions for edge positions | Construct node `question` property |
| Q37-Q55 | 19 | Spectrum questions for opposition pairs | SPECTRUM_OPPOSITION edge `question` property |
| Q56-Q100 | 45 | Point questions for center positions | Construct node `question` property |

Total unique point questions from source: ~79 (36 edge + ~43 center).
Total center positions per grid: 64.
Gap: ~19-21 center questions must be authored to complete rows y=6, y=7, y=8.

---

## Base Question Authoring Principles

Each grid position carries a **structural role** (from Spec 02) that determines the nature of the question:

| Classification | Question nature |
|---|---|
| Corner | Foundational — addresses a bounding truth at the combined extreme of both sub-dimensions |
| Midpoint | Axial — addresses the balancing or centering force at one sub-dimension's extreme |
| Edge | Directional — addresses a force-integrated position along one extreme |
| Center | Resolving — addresses a synthesized, balanced position in the interior field |

Questions are **epistemic probes** — they ask what possibility exists at that position. They do not assert answers.

---

## Parameterization Rule

Point questions are written with a domain placeholder `{domain}`. When parameterized for a specific branch, `{domain}` is replaced with the branch's area of concern:

| Branch | {domain} replacement |
|---|---|
| Ontology | ontological existence |
| Epistemology | epistemological truth |
| Axiology | axiological value |
| Teleology | teleological purpose |
| Phenomenology | phenomenological experience |
| Praxeology | praxeological action |
| Methodology | methodological practice |
| Semiotics | semiotic meaning |
| Hermeneutics | hermeneutic interpretation |
| Heuristics | heuristic strategy |

Spectrum questions use the same `{domain}` replacement but describe the relationship between two positions rather than a single position.

---

## Tag Derivation Rule

Tags are extracted mechanically from each parameterized question:

1. Lowercase the question
2. Remove stop words (what, is, the, of, a, an, at, in, from, how, does, do, that, this, which, for, to, and, or, by, with, its, are, be, into, as, when, where, can, has, have, through, between, within, upon, along, across)
3. Stem remaining words (Porter stemmer)
4. Add the branch name as a tag
5. Add the classification as a tag

---

## Point Questions — Edge Positions (36)

Sourced from Q1-Q36 of `03a-source-questions.md`. Each is parameterized with `{domain}`.

### Corner Points (4)

| Position | Source | Base question |
|---|---|---|
| (0,0) | Q1 | What originating possibility initiates the total epistemic field of {domain}? |
| (9,0) | Q2 | What force-defined boundary sets the limitation of harmonic potential across the horizontal axis of {domain}? |
| (0,9) | Q3 | What end-state possibility reflects the accumulation of spectral influence along the vertical edge of {domain}? |
| (9,9) | Q4 | What convergence of opposed energetic directions yields a coherent inflection in {domain}? |

### Midpoints (4)

| Position | Source | Base question |
|---|---|---|
| (4,0) | Q5 | What axial tension originates from the horizontal dimension's central polarity in {domain}? |
| (9,4) | Q6 | What transformation does vertical edge influence undergo at the locus of maximal lateral divergence in {domain}? |
| (4,9) | Q7 | What reflected projection completes the harmonic sequence begun from the top center of {domain}? |
| (0,4) | Q8 | What counterbalancing projection is enacted through edge-derived force reflection in {domain}? |

### Top Edge — y=0 (7)

| Position | Source | Base question |
|---|---|---|
| (1,0) | Q9 | What emergent polarity forms between anchoring origin and expanding vector in {domain}? |
| (2,0) | Q10 | What preliminary expression of spectrum is encoded before the midpoint of {domain} is reached? |
| (3,0) | Q11 | What early-stage energetic differentiator signals the initial divergence of {domain}? |
| (5,0) | Q12 | What resonant field defines transitional knowledge zones in {domain}? |
| (6,0) | Q13 | What hyperstructural inversion begins to unfold from lateral energy in {domain}? |
| (7,0) | Q14 | What high-fidelity spectral signature delineates specific knowing from generalized form in {domain}? |
| (8,0) | Q15 | What final pre-corner alignment locks the edge's intent in {domain}? |

### Right Edge — x=9 (7)

| Position | Source | Base question |
|---|---|---|
| (9,1) | Q16 | What lateral discharge begins to transfer energetic potency downward in {domain}? |
| (9,2) | Q17 | What boundary-modulated field accumulates adjacent to edge-centric energy in {domain}? |
| (9,3) | Q18 | What preparation is made for harmonization across horizontal and vertical interplay in {domain}? |
| (9,5) | Q19 | What energetic recoil or redirection signals inversion from external to internal force in {domain}? |
| (9,6) | Q20 | What emergent tension creates a mirrored reflection of the upper quadrant in {domain}? |
| (9,7) | Q21 | What force-integration model completes the downward projection in {domain}? |
| (9,8) | Q22 | What point of containment regulates the end flow of vertical energy in {domain}? |

### Bottom Edge — y=9 (7)

| Position | Source | Base question |
|---|---|---|
| (8,9) | Q23 | What spectral conclusion begins the return journey of horizontal contraction in {domain}? |
| (7,9) | Q24 | What saturation defines the late-stage energy horizon of {domain}? |
| (6,9) | Q25 | What reversal of directional knowledge becomes manifest in {domain}? |
| (5,9) | Q26 | What terminal convergence mirrors the primary center of {domain}? |
| (3,9) | Q27 | What leftward movement of energy distills upper tensions in {domain}? |
| (2,9) | Q28 | What potential resolves against its horizontal inverse in {domain}? |
| (1,9) | Q29 | What fading polarity finalizes its contribution to {domain}? |

### Left Edge — x=0 (7)

| Position | Source | Base question |
|---|---|---|
| (0,8) | Q30 | What structural echo of vertical centrality influences the boundary of {domain}? |
| (0,7) | Q31 | What harmonization across lower-edge spectrums arises in this ascending node of {domain}? |
| (0,6) | Q32 | What signature potential rotates into active formation within {domain}? |
| (0,5) | Q33 | What balanced state reflects both ascending and descending tension in {domain}? |
| (0,3) | Q34 | What transitional field mimics inversion before the medial point of {domain}? |
| (0,2) | Q35 | What initiating edge thrust configures the spectral flow path of {domain}? |
| (0,1) | Q36 | What near-originating field contains an echo of the first point's truth in {domain}? |

---

## Spectrum Questions (19)

Sourced from Q37-Q55 of `03a-source-questions.md`. Stored as the `question` property on SPECTRUM_OPPOSITION edges.

Each spectrum question describes the opposition between two edge points. Parameterized with `{domain}`.

| Source | Point A | Point B | Base question |
|---|---|---|---|
| Q37 | (0,0) | (9,9) | What diagonal spectrum defines the longest uninterrupted field of force-paired knowledge in {domain}? |
| Q38 | (0,1) | (9,8) | What tension manifests between offset vertical polarities in {domain}? |
| Q39 | (0,2) | (9,7) | What dynamic between secondaries encodes nuanced relationships in {domain}? |
| Q40 | (0,3) | (9,6) | What diagonal field carries mirrored harmonic intent in {domain}? |
| Q41 | (0,4) | (9,5) | What intersectional convergence frames a resonance of central axis inversion in {domain}? |
| Q42 | (0,5) | (9,4) | What mirrored spectrum balances opposing phase channels in {domain}? |
| Q43 | (0,6) | (9,3) | What axial rotation produces lateral constraint in {domain}? |
| Q44 | (0,7) | (9,2) | What reversal mirror is expressed in opposing phase lag in {domain}? |
| Q45 | (0,8) | (9,1) | What diagonal returns to near-origin configuration in {domain}? |
| Q46 | (0,9) | (9,0) | What final spectrum defines the inversion between start and end in {domain}? |
| Q47 | (1,0) | (8,9) | What interior-facing spectrum cross-links secondaries across opposing edge regions in {domain}? |
| Q48 | (2,0) | (7,9) | What intermediate diagonal translates structural tension into spectral arc in {domain}? |
| Q49 | (3,0) | (6,9) | What mid-range spectrum amplifies edge-center integration in {domain}? |
| Q50 | (4,0) | (5,9) | What direct axial alignment overlays mirrored projections in {domain}? |
| Q51 | (5,0) | (4,9) | What inwardly reversing diagonal manifests dynamic inversion in {domain}? |
| Q52 | (6,0) | (3,9) | What force corridor overlays reversal with asymmetry in {domain}? |
| Q53 | (7,0) | (2,9) | What counter-spectral swing defines displaced reciprocity in {domain}? |
| Q54 | (8,0) | (1,9) | What nearly-terminal spectrum refines terminal edges of {domain}? |
| Q55 | (9,0) | (0,9) | What full-spectrum inversion completes edge-to-edge totality in {domain}? |

**Note:** The source provides 19 spectrum questions. The grid geometry produces 18 unique edge↔edge reflection pairs (from Spec 02). The 19th (Q55) is the reverse of Q46 — both describe the (0,9)↔(9,0) / (9,0)↔(0,9) spectrum from opposite perspectives. Both are retained as the spectrum's content (one per directional reading).

---

## Point Questions — Center Positions (64)

### Center positions covered by source (Q56-Q99): ~43 positions

Rows y=1 through y=5 are fully covered (8 positions per row × 5 rows = 40), plus the 4 core nexus candidates at (4,4), (4,5), (5,4), (5,5), minus the revisitations at Q87 and Q95-Q96.

Sourced from Q56-Q99 of `03a-source-questions.md`.

### Core center (4)

| Position | Source | Base question |
|---|---|---|
| (4,4) | Q56 | What universal convergence of possibility initiates nexus formation in {domain}? |
| (4,5) | Q57 | What active boundary supports the center's epistemic field of {domain}? |
| (5,4) | Q58 | What mirror of core potential modulates counter-flow in {domain}? |
| (5,5) | Q59 | What harmonization at the true grid center governs all structural interactions in {domain}? |

### Row y=1 (8)

| Position | Source | Base question |
|---|---|---|
| (1,1) | Q60 | What embryonic possibility awakens from boundary proximity in {domain}? |
| (2,1) | Q61 | What directional gradient modulates substructural motion in {domain}? |
| (3,1) | Q62 | What spectral tremor prefigures axial alignment in {domain}? |
| (4,1) | Q63 | What harmonic overture begins energetic modulation of {domain}? |
| (5,1) | Q64 | What flow redirection captures post-centrality effects in {domain}? |
| (6,1) | Q65 | What resonance buffer bounds central field harmonics in {domain}? |
| (7,1) | Q66 | What external harmonics leak inward at this position in {domain}? |
| (8,1) | Q67 | What semi-boundary potential blurs the center-edge distinction in {domain}? |

### Row y=2 (8)

| Position | Source | Base question |
|---|---|---|
| (1,2) | Q68 | What vertical spectral transition begins force layering in {domain}? |
| (2,2) | Q69 | What dual harmonics rise into structured balance within {domain}? |
| (3,2) | Q70 | What sweep of cognition modulates upward force in {domain}? |
| (4,2) | Q71 | What tuning operation bridges the northern internal zone of {domain}? |
| (5,2) | Q72 | What return harmonic reshapes phase delay in {domain}? |
| (6,2) | Q73 | What edge proximity biases the flow of {domain}? |
| (7,2) | Q74 | What asymmetrical resonance is visible at this locus of {domain}? |
| (8,2) | Q75 | What thinning of possibility occurs at this boundary-adjacent point of {domain}? |

### Row y=3 (8)

| Position | Source | Base question |
|---|---|---|
| (1,3) | Q76 | What layering of force expands downward in {domain}? |
| (2,3) | Q77 | What midpoint translation occurs at this progressive entry of {domain}? |
| (3,3) | Q78 | What convergence wave begins to overlap within {domain}? |
| (4,3) | Q79 | What pressure gradient builds before the core of {domain}? |
| (5,3) | Q80 | What inverse reflection shapes internal motion of {domain}? |
| (6,3) | Q81 | What spectral compression sounds at this stepping-out point of {domain}? |
| (7,3) | Q82 | What filtering behavior modulates vector intensity in {domain}? |
| (8,3) | Q83 | What preparation for transition is made at this position in {domain}? |

### Row y=4 (8)

| Position | Source | Base question |
|---|---|---|
| (1,4) | Q84 | What return-to-core path signals harmonic approach in {domain}? |
| (2,4) | Q85 | What stabilizing formation sits beneath the secondary vertical of {domain}? |
| (3,4) | Q86 | What triadic edge balance frames ascending potential in {domain}? |
| (4,4) | Q87 | What confirms the role of universal synthesizer in {domain}? |
| (5,4) | Q88 | What reflective polarity stabilizes recursion at the core of {domain}? |
| (6,4) | Q89 | What feedback occurs at the grid dilation boundary of {domain}? |
| (7,4) | Q90 | What pressure absorption harmonizes forces at this position of {domain}? |
| (8,4) | Q91 | What is filtered from {domain} at this rightward central resolution point? |

### Row y=5 (8)

| Position | Source | Base question |
|---|---|---|
| (1,5) | Q92 | What vertical inversion harmonizes within the southern trajectory of {domain}? |
| (2,5) | Q93 | What mirrored convergence operates in phase-locked relationship within {domain}? |
| (3,5) | Q94 | What descending gradient re-enters the axis of {domain}? |
| (4,5) | Q95 | What mid-line rebound tension defines this active boundary of {domain}? |
| (5,5) | Q96 | What recursive apex stabilizes the field at the true center of {domain}? |
| (6,5) | Q97 | What winding dispersion approaches the external edge of {domain}? |
| (7,5) | Q98 | What final arc of central-to-boundary shift characterizes {domain} here? |
| (8,5) | Q99 | What concluding harmonic slips from internal projection in {domain}? |

### Rows y=6, y=7, y=8 — Authored to Complete (24) [PROVISIONAL]

These 24 questions complete the 64 center positions. Authored to maintain the structural and tonal patterns of the source material. **These are not from Spec 03a (the authoritative source).** They are implementation-authored to fill the gap left by the source material ending at row y=5. They should be reviewed against the Construct's epistemic framework and may be revised.

### Row y=6 (8)

| Position | Base question |
|---|---|
| (1,6) | What deepening structural descent carries {domain} below its median? |
| (2,6) | What secondary harmonic layer stabilizes {domain} at this depth? |
| (3,6) | What rotational echo of the upper field persists at this position of {domain}? |
| (4,6) | What post-core release disperses concentrated energy in {domain}? |
| (5,6) | What mirror of the upper-center symmetry reflects at this position of {domain}? |
| (6,6) | What diagonal resonance crosses through this interior node of {domain}? |
| (7,6) | What dampened edge influence reaches this interior point of {domain}? |
| (8,6) | What boundary-proximate thinning recurs at this lower position of {domain}? |

### Row y=7 (8)

| Position | Base question |
|---|---|
| (1,7) | What lower-field harmonic rises from the depths of {domain}? |
| (2,7) | What resolution pattern begins to crystallize at this position of {domain}? |
| (3,7) | What late-stage convergence draws inward from the field of {domain}? |
| (4,7) | What pre-terminal synthesis collects the energies of {domain}? |
| (5,7) | What counterpart to the upper core operates at this depth of {domain}? |
| (6,7) | What dispersive tendency is counteracted by structural constraint in {domain}? |
| (7,7) | What near-boundary resonance echoes the opposite corner's influence in {domain}? |
| (8,7) | What penultimate resolution forms before the terminal edge of {domain}? |

### Row y=8 (8)

| Position | Base question |
|---|---|
| (1,8) | What final interior force prepares {domain} for its southern boundary? |
| (2,8) | What residual harmonic persists at this depth within {domain}? |
| (3,8) | What last trace of central convergence is detectable at this position of {domain}? |
| (4,8) | What pre-edge compression focuses the remaining energy of {domain}? |
| (5,8) | What mirrored pre-edge state reflects the upper boundary approach of {domain}? |
| (6,8) | What terminal interior oscillation characterizes this position of {domain}? |
| (7,8) | What boundary anticipation shapes the final interior expression of {domain}? |
| (8,8) | What near-corner resonance prefigures the terminal convergence of {domain}? |

---

## Revisitation Handling

Two source questions revisit positions already covered:
- **Q87** revisits (4,4) (first covered by Q56). Both questions are retained as construct properties: Q56 as `question`, Q87 as `question_revisited`. The revisitation deepens the position's meaning.
- **Q100** revisits (9,9) (first covered by Q4). Same treatment: Q4 as `question`, Q100 as `question_revisited`.

---

## Point Question Count Verification

| Category | Count |
|---|---|
| Corner points | 4 |
| Midpoint points | 4 |
| Top edge (non-corner, non-midpoint) | 7 |
| Right edge | 7 |
| Bottom edge | 7 |
| Left edge | 7 |
| Center rows y=1 through y=5 (sourced) | 40 |
| Center core (4,4), (4,5), (5,4), (5,5) | 4 (included in row counts) |
| Center rows y=6, y=7, y=8 (authored) | 24 |
| **Total unique point questions** | **100** |

With 19 spectrum questions: **119 total canonical content items** per plane, parameterized across 10 branches = **1190 parameterized items** (1000 point questions on construct nodes + 190 spectrum questions on spectrum edges).

---

## Nexus Definitions (45 Undirected Pairs)

Each pair produces 2 directional nexi (A→B and B→A). The content below describes the undirected interaction; directional nexi inherit this content with source/target specificity.

### Ontology Pairs (9)

| Pair | Content |
|---|---|
| Ontology ↔ Epistemology | How does the nature of what exists determine what can be known, and how does knowing reshape what is recognized as existing? |
| Ontology ↔ Axiology | How does the nature of existence ground what can be valued, and how do values determine which entities are recognized? |
| Ontology ↔ Teleology | How do existing entities bear purpose, and how does purpose call entities into recognized existence? |
| Ontology ↔ Phenomenology | How does existence present itself to experience, and how does experience constitute what is recognized as real? |
| Ontology ↔ Praxeology | How does the structure of what exists enable or constrain action, and how does action alter what exists? |
| Ontology ↔ Methodology | How does the nature of existence determine which methods of inquiry are valid, and how do methods reveal or construct entities? |
| Ontology ↔ Semiotics | How do existing entities generate signs, and how do signs constitute the recognition of entities? |
| Ontology ↔ Hermeneutics | How does the nature of what exists shape how it is interpreted, and how does interpretation reconstitute what is understood to exist? |
| Ontology ↔ Heuristics | How does the structure of existence determine which problem-solving strategies are viable, and how do strategies reshape perceived reality? |

### Epistemology Pairs (8)

| Pair | Content |
|---|---|
| Epistemology ↔ Axiology | How does justified knowledge determine what is worth valuing, and how do values shape what counts as knowledge? |
| Epistemology ↔ Teleology | How does knowledge direct purpose, and how does purpose determine what is worth knowing? |
| Epistemology ↔ Phenomenology | How does knowledge relate to lived experience, and how does experience generate or undermine claims to knowledge? |
| Epistemology ↔ Praxeology | How does knowing inform acting, and how does acting produce or revise knowledge? |
| Epistemology ↔ Methodology | How do justified beliefs determine valid methods, and how do methods produce justified beliefs? |
| Epistemology ↔ Semiotics | How does knowledge encode into signs, and how do signs carry or distort epistemic content? |
| Epistemology ↔ Hermeneutics | How does established knowledge frame interpretation, and how does interpretation challenge or extend knowledge? |
| Epistemology ↔ Heuristics | How does knowledge inform strategy, and how do strategies reveal knowledge that formal methods miss? |

### Axiology Pairs (7)

| Pair | Content |
|---|---|
| Axiology ↔ Teleology | How do values define purpose, and how does purpose reveal which values are operative? |
| Axiology ↔ Phenomenology | How do values shape experience, and how does experience challenge or validate value claims? |
| Axiology ↔ Praxeology | How do values motivate action, and how do the outcomes of action revise what is valued? |
| Axiology ↔ Methodology | How do values determine which methods are acceptable, and how do methods produce value judgments? |
| Axiology ↔ Semiotics | How are values communicated through signs, and how do semiotic structures privilege certain values? |
| Axiology ↔ Hermeneutics | How do values frame interpretation, and how does interpretation reveal hidden value commitments? |
| Axiology ↔ Heuristics | How do values constrain strategy, and how do strategic outcomes reshape value hierarchies? |

### Teleology Pairs (6)

| Pair | Content |
|---|---|
| Teleology ↔ Phenomenology | How does purpose structure experience, and how does experience reveal or subvert intended purpose? |
| Teleology ↔ Praxeology | How does purpose direct action, and how does action fulfill, redirect, or abandon purpose? |
| Teleology ↔ Methodology | How does purpose select method, and how do methodological constraints reshape achievable purpose? |
| Teleology ↔ Semiotics | How is purpose encoded in communication, and how do semiotic structures enable or obscure purpose? |
| Teleology ↔ Hermeneutics | How does purpose frame interpretation, and how does interpretation reveal purposes not consciously intended? |
| Teleology ↔ Heuristics | How does purpose constrain strategy, and how do pragmatic strategies reshape what purposes are pursued? |

### Phenomenology Pairs (5)

| Pair | Content |
|---|---|
| Phenomenology ↔ Praxeology | How does experience motivate action, and how does action transform the quality of experience? |
| Phenomenology ↔ Methodology | How does experience inform method, and how do methods structure what can be experienced? |
| Phenomenology ↔ Semiotics | How does experience generate meaning, and how do signs shape what is experienceable? |
| Phenomenology ↔ Hermeneutics | How does lived experience frame interpretation, and how does interpretation deepen or distort experience? |
| Phenomenology ↔ Heuristics | How does experience inform practical strategy, and how do strategies alter the texture of experience? |

### Praxeology Pairs (4)

| Pair | Content |
|---|---|
| Praxeology ↔ Methodology | How does action require method, and how do methods constrain or enable forms of action? |
| Praxeology ↔ Semiotics | How is action communicated, and how do communicative structures shape what actions are conceivable? |
| Praxeology ↔ Hermeneutics | How is action interpreted, and how does interpretation of past action shape future action? |
| Praxeology ↔ Heuristics | How do strategies structure action, and how does action under uncertainty refine available strategies? |

### Methodology Pairs (3)

| Pair | Content |
|---|---|
| Methodology ↔ Semiotics | How do methods produce signs, and how do semiotic conventions determine which methods are communicable? |
| Methodology ↔ Hermeneutics | How do methods frame interpretation, and how does interpretive practice challenge methodological assumptions? |
| Methodology ↔ Heuristics | How do formal methods relate to informal strategies, and how do heuristic discoveries become formalized methods? |

### Semiotics Pairs (2)

| Pair | Content |
|---|---|
| Semiotics ↔ Hermeneutics | How do signs invite interpretation, and how does interpretive practice generate new semiotic conventions? |
| Semiotics ↔ Heuristics | How do signs encode strategies, and how do strategic adaptations produce new signs? |

### Hermeneutics Pair (1)

| Pair | Content |
|---|---|
| Hermeneutics ↔ Heuristics | How does interpretation inform practical strategy, and how do strategies for managing the unknown reshape interpretive frames? |

### Pair Count: 9 + 8 + 7 + 6 + 5 + 4 + 3 + 2 + 1 = **45 undirected pairs** → **90 directional nexi**

---

## Central Gem Definition

**Content:** *"What singular coherence emerges when the extremes of existence, knowing, valuing, purposing, experiencing, acting, systematizing, communicating, interpreting, and strategizing are held simultaneously in mutual awareness?"*

---

## Spectrum Semantic Annotations

Spectrums with authored questions (Q37-Q55) have their `question` property set to that authored question on the SPECTRUM_OPPOSITION edge.

Spectrums without authored questions have `question = null` on the edge. Their semantic content is derived at query time by the pipeline — the Construction Bridge presents the two endpoint point-questions as a contrasting pair. The spectrum meaning is the structured difference between its two endpoint questions. No synthetic question is generated; the endpoint pair IS the content.
