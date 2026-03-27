# Spec 03 — Canonical Content

## Purpose

Defines the 1000 canonical constructs (100 base questions × 10 branches), 45 nexus interaction definitions (undirected pairs from which 90 directional nexi derive), and the central gem definition. This is the content that ships with the engine.

---

## Base Question Authoring Principles

Each of the 100 grid positions carries a **structural role** (from Spec 02) that determines the nature of the question at that position:

| Classification | Question nature |
|---|---|
| Corner | Foundational — addresses a bounding truth at the combined extreme of both sub-dimensions |
| Midpoint | Axial — addresses the balancing or centering force at one sub-dimension's extreme |
| Edge | Directional — addresses a force-integrated position along one extreme |
| Center | Resolving — addresses a synthesized, balanced position in the interior field |

Questions are written as **epistemic probes** — they ask what possibility exists at that position. They do not assert answers.

---

## Parameterization Rule

Each base question is written with a domain placeholder `{domain}`. When parameterized for a specific branch, `{domain}` is replaced with the branch's area of concern:

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

Example base question at (0,0): *"What foundational possibility anchors the origin of {domain}?"*

Becomes:
- Ontology: *"What foundational possibility anchors the origin of ontological existence?"*
- Epistemology: *"What foundational possibility anchors the origin of epistemological truth?"*

---

## Tag Derivation Rule

Tags are extracted mechanically from each parameterized question:

1. Lowercase the question
2. Remove stop words (what, is, the, of, a, an, at, in, from, how, does, do, that, this, which, for, to, and, or, by, with, its, are, be, into, as, when, where, can, has, have, through, between, within, upon, along, across)
3. Stem remaining words (Porter stemmer)
4. Add the branch name as a tag
5. Add the classification as a tag

---

## The 100 Base Questions

### Corner Points (4)

| Position | Question |
|---|---|
| (0,0) | What foundational possibility anchors the origin of {domain}? |
| (9,0) | What bounding possibility defines the horizon of {domain} along the primary axis? |
| (0,9) | What terminal possibility resolves the descent of {domain} along the secondary axis? |
| (9,9) | What convergent possibility harmonizes the full extent of {domain}? |

### Midpoints (4)

| Position | Question |
|---|---|
| (4,0) | What axial tension originates from the central polarity of {domain} at the primary extreme? |
| (9,4) | What transformational force emerges at the lateral midpoint of {domain}? |
| (4,9) | What reflective synthesis balances {domain} at the secondary extreme? |
| (0,4) | What counterbalancing projection shapes {domain} through its medial origin? |

### Top Edge — y=0 (positions 1-3, 5-8)

| Position | Question |
|---|---|
| (1,0) | What emergent polarity forms near the origin of {domain} along the primary axis? |
| (2,0) | What preliminary expression of {domain} is encoded before the primary midpoint? |
| (3,0) | What initiating polarity lies within the early divergence of {domain}? |
| (5,0) | What transitional resonance defines the zone beyond the primary center of {domain}? |
| (6,0) | What advancing structure begins to unfold past the center of {domain}? |
| (7,0) | What high-fidelity signature delineates specific knowing from general form in {domain}? |
| (8,0) | What pre-terminal alignment locks the primary edge's intent in {domain}? |

### Right Edge — x=9 (positions 1-3, 5-8)

| Position | Question |
|---|---|
| (9,1) | What lateral discharge begins to transfer potency downward along {domain}? |
| (9,2) | What boundary-modulated field accumulates adjacent to the edge of {domain}? |
| (9,3) | What preparatory harmonization forms before the secondary center of {domain}? |
| (9,5) | What energetic redirection signals inversion from external to internal force in {domain}? |
| (9,6) | What emergent tension creates a mirrored reflection in the lower quadrant of {domain}? |
| (9,7) | What force-integration model completes the downward projection in {domain}? |
| (9,8) | What containment regulates the terminal flow of {domain} along the lateral edge? |

### Bottom Edge — y=9 (positions 1-3, 5-8)

| Position | Question |
|---|---|
| (8,9) | What spectral conclusion initiates the return of {domain} from its terminal extent? |
| (7,9) | What saturation defines the late-stage horizon of {domain}? |
| (6,9) | What reversal of directional force becomes manifest in {domain}? |
| (5,9) | What terminal convergence mirrors the primary center of {domain}? |
| (3,9) | What leftward distillation resolves upper tensions in {domain}? |
| (2,9) | What potential resolves against its horizontal inverse in {domain}? |
| (1,9) | What fading polarity finalizes its contribution to {domain}? |

### Left Edge — x=0 (positions 1-3, 5-8)

| Position | Question |
|---|---|
| (0,8) | What structural echo of vertical centrality influences the boundary of {domain}? |
| (0,7) | What harmonization across lower spectrums arises in this ascending node of {domain}? |
| (0,6) | What signature potential rotates into active formation within {domain}? |
| (0,5) | What balanced state reflects both ascending and descending tension in {domain}? |
| (0,3) | What transitional field mimics inversion before the medial point of {domain}? |
| (0,2) | What initiating edge thrust configures the spectral flow path of {domain}? |
| (0,1) | What near-originating field contains an echo of the first point's truth in {domain}? |

### Center Points — Row y=1 (x: 1-8)

| Position | Question |
|---|---|
| (1,1) | What embryonic possibility awakens from boundary proximity in {domain}? |
| (2,1) | What directional gradient modulates substructural motion in {domain}? |
| (3,1) | What spectral tremor prefigures axial alignment in {domain}? |
| (4,1) | What harmonic overture begins energetic modulation of {domain}? |
| (5,1) | What flow redirection captures post-centrality effects in {domain}? |
| (6,1) | What resonance buffer bounds central field harmonics in {domain}? |
| (7,1) | What external harmonics leak inward at this position in {domain}? |
| (8,1) | What semi-boundary potential blurs the center-edge distinction in {domain}? |

### Center Points — Row y=2

| Position | Question |
|---|---|
| (1,2) | What vertical spectral transition begins force layering in {domain}? |
| (2,2) | What dual harmonics rise into structured balance within {domain}? |
| (3,2) | What sweep of cognition modulates upward force in {domain}? |
| (4,2) | What tuning operation bridges the northern internal zone of {domain}? |
| (5,2) | What return harmonic reshapes phase delay in {domain}? |
| (6,2) | What edge proximity biases the flow of {domain}? |
| (7,2) | What asymmetrical resonance is visible at this locus of {domain}? |
| (8,2) | What thinning of possibility occurs at this boundary-adjacent point of {domain}? |

### Center Points — Row y=3

| Position | Question |
|---|---|
| (1,3) | What layering of force expands downward in {domain}? |
| (2,3) | What midpoint translation occurs at this progressive entry of {domain}? |
| (3,3) | What convergence wave begins to overlap within {domain}? |
| (4,3) | What pressure gradient builds before the core of {domain}? |
| (5,3) | What inverse reflection shapes internal motion of {domain}? |
| (6,3) | What spectral compression sounds at this stepping-out point of {domain}? |
| (7,3) | What filtering behavior modulates vector intensity in {domain}? |
| (8,3) | What preparation for transition is made at this position in {domain}? |

### Center Points — Row y=4

| Position | Question |
|---|---|
| (1,4) | What return-to-core path signals harmonic approach in {domain}? |
| (2,4) | What stabilizing formation sits beneath the secondary vertical of {domain}? |
| (3,4) | What triadic edge balance frames ascending potential in {domain}? |
| (4,4) | What universal convergence of possibility initiates nexus formation in {domain}? |
| (5,4) | What reflective polarity stabilizes recursion at the core of {domain}? |
| (6,4) | What feedback occurs at the grid dilation boundary of {domain}? |
| (7,4) | What pressure absorption harmonizes forces at this position of {domain}? |
| (8,4) | What is filtered from {domain} at this rightward central resolution point? |

### Center Points — Row y=5

| Position | Question |
|---|---|
| (1,5) | What vertical inversion harmonizes within the southern trajectory of {domain}? |
| (2,5) | What mirrored convergence operates in phase-locked relationship within {domain}? |
| (3,5) | What descending gradient re-enters the axis of {domain}? |
| (4,5) | What mid-line rebound tension defines this active boundary of {domain}? |
| (5,5) | What recursive apex stabilizes the field at the true center of {domain}? |
| (6,5) | What winding dispersion approaches the external edge of {domain}? |
| (7,5) | What final arc of central-to-boundary shift characterizes {domain} here? |
| (8,5) | What concluding harmonic slips from internal projection in {domain}? |

### Center Points — Row y=6

| Position | Question |
|---|---|
| (1,6) | What deepening structural descent carries {domain} below its median? |
| (2,6) | What secondary harmonic layer stabilizes {domain} at this depth? |
| (3,6) | What rotational echo of the upper field persists at this position of {domain}? |
| (4,6) | What post-core release disperses concentrated energy in {domain}? |
| (5,6) | What mirror of the upper-center symmetry reflects at this position of {domain}? |
| (6,6) | What diagonal resonance crosses through this interior node of {domain}? |
| (7,6) | What dampened edge influence reaches this interior point of {domain}? |
| (8,6) | What boundary-proximate thinning recurs at this lower position of {domain}? |

### Center Points — Row y=7

| Position | Question |
|---|---|
| (1,7) | What lower-field harmonic rises from the depths of {domain}? |
| (2,7) | What resolution pattern begins to crystallize at this position of {domain}? |
| (3,7) | What late-stage convergence draws inward from the field of {domain}? |
| (4,7) | What pre-terminal synthesis collects the energies of {domain}? |
| (5,7) | What counterpart to the upper core operates at this depth of {domain}? |
| (6,7) | What dispersive tendency is counteracted by structural constraint in {domain}? |
| (7,7) | What near-boundary resonance echoes the opposite corner's influence in {domain}? |
| (8,7) | What penultimate resolution forms before the terminal edge of {domain}? |

### Center Points — Row y=8

| Position | Question |
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

## Question Count Verification

| Section | Count |
|---|---|
| Corners | 4 |
| Midpoints | 4 |
| Top edge (non-corner, non-midpoint) | 7 |
| Right edge | 7 |
| Bottom edge | 7 |
| Left edge | 7 |
| Center row y=1 | 8 |
| Center row y=2 | 8 |
| Center row y=3 | 8 |
| Center row y=4 | 8 |
| Center row y=5 | 8 |
| Center row y=6 | 8 |
| Center row y=7 | 8 |
| Center row y=8 | 8 |
| **Total** | **100** |

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

### Epistemology Pairs (8, excluding Ontology)

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

### Axiology Pairs (7, excluding Ontology, Epistemology)

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

### Pair Count Verification

9 + 8 + 7 + 6 + 5 + 4 + 3 + 2 + 1 = **45 undirected pairs** → **90 directional nexi**

---

## Central Gem Definition

**Content:** *"What singular coherence emerges when the extremes of existence, knowing, valuing, purposing, experiencing, acting, systematizing, communicating, interpreting, and strategizing are held simultaneously in mutual awareness?"*

This is the one question that belongs to no branch and all branches. It is the meta-philosophical convergence — the system-wide synthesis of awareness.

---

## Spectrum Semantic Annotations

Each of the 200 spectrums (20 per branch × 10 branches, adjusted per Spec 02's precise algorithm) has semantic content derived mechanically from its two endpoint questions. No manual annotation required — the spectrum's meaning is the contrast between its two endpoint questions.

Implementation: retrieve endpoint questions and present them as a pair. The spectrum is the structured difference between them.
