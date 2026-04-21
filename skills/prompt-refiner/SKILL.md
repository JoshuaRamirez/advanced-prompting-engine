---
name: Prompt Refiner
description: >
  This skill should be used when the user asks to "refine a prompt",
  "improve this prompt", "run this through APE", "make this prompt better",
  "iterate on this prompt", "philosophical refinement", "dimensional analysis
  of a prompt", "prompt engineering with APE", "measure this prompt",
  "what's missing from this prompt", or needs to iteratively improve a prompt
  using the Advanced Prompting Engine's 12-dimensional philosophical measurement.
version: 0.6.0
---

# Prompt Refiner

Iteratively refine a prompt using the Advanced Prompting Engine (APE) MCP server v0.7.2. Takes raw intent, measures it across 12 philosophical faces via a BGE-large-en-v1.5 semantic bridge (1024d, full-sentence encoding), interprets deficiencies using the `interpret_basis` tool, rewrites to address gaps, and repeats until the prompt achieves dimensional coverage appropriate for its purpose.

## The 12 Faces

Each face is a 12x12 grid with named axis polarities. Position on each axis carries meaning.

| Face | X Axis (0→11) | Y Axis (0→11) | Core Question |
|------|---------------|---------------|---------------|
| **Ontology** | Particular → Universal | Static → Dynamic | What entities and relationships fundamentally exist? |
| **Epistemology** | Empirical → Rational | Certain → Provisional | How do we know domain states and conditions are true? |
| **Axiology** | Absolute → Relative | Quantitative → Qualitative | By what criteria is worth determined? |
| **Teleology** | Immediate → Ultimate | Intentional → Emergent | What ultimate purposes does each interaction serve? |
| **Phenomenology** | Objective → Subjective | Surface → Deep | How are experiences represented and realized? |
| **Ethics** | Deontological → Consequential | Agent → Act | What obligations and moral warrants govern right action? |
| **Aesthetics** | Autonomous → Contextual | Sensory → Conceptual | What qualities of form and significance constitute recognition? |
| **Praxeology** | Individual → Coordinated | Reactive → Proactive | How are actions, behaviors, and intentions structured? |
| **Methodology** | Analytic → Synthetic | Deductive → Inductive | What processes govern construction and evolution? |
| **Semiotics** | Explicit → Implicit | Syntactic → Semantic | How are signals and data meaningfully communicated? |
| **Hermeneutics** | Literal → Figurative | Author-intent → Reader-response | What frameworks govern interpretation and understanding? |
| **Heuristics** | Systematic → Intuitive | Conservative → Exploratory | What practical strategies guide handling of complexities? |

## The Manifold

Each face is a 12x12 grid. Position (0,0) is the foundational corner — the place where the question has not yet been asked but the capacity to ask it is absolute. It is both foundation and absence. Position (11,11) is the widest unconstrained understanding. Center positions (5-8 range) indicate engaged, balanced commitment.

The axis names tell you what movement in each direction means. Ontology at (0,0) means Particular+Static — a fixed, specific entity claim. Ontology at (11,11) means Universal+Dynamic — the broadest, most fluid understanding of what exists. A prompt's position on each face is its philosophical stance on that dimension.

Constructs are classified as "corner" (at grid corners), "edge" (near edges), or "center" (in the middle). Spokes connect faces. The central gem measures overall coherence.

**Wholeness** does not mean uniform engagement across all 12 faces — register competition (see Known Limitations) makes that target incoherent. It means the construction questions the prompt generates are questions you have already answered within the register your task actually requires. Tensions are acknowledged with resolution paths, generative combinations are present, and the faces that matter for the purpose are inhabited rather than named. A prompt can be whole with 6 faces strongly engaged and 6 near the floor, if those 6 are the right 6.

## What the Server Returns

The server returns a **12-face coordinate matrix**. Each face is a triple:

```json
{"x": 4, "y": 7, "weight": 0.713}
```

- **x** (0-11): Position on the face's X axis. Meaning comes from the axis label — ontology x=4 means "moderately Particular" because the X axis is Particular(0)→Universal(11).
- **y** (0-11): Position on the face's Y axis. Ontology y=7 means "moderately Dynamic" because Y is Static(0)→Dynamic(11).
- **weight** (0.0-1.0): How strongly the prompt activates this dimension. The server classifies faces as "dominant" (high weight) or "neglected" (low weight) in the guidance section. The weight is a semantic activation measure — the BGE bridge produces it from your text, but the computation is opaque. You do not know how 0.713 was derived; you know it means "strongly engaged" because the server's guidance section calls it dominant, and faces below ~0.2 appear in the "neglected" list.

The server **does explain** what coordinates mean — via `position_summary` fields that translate (x,y) into natural language stances like "moderately Particular + moderately Dynamic." The server **does not explain** how it computed the weight from your text. The BGE semantic bridge is a black box — a 1024-dimensional transformer-based encoding with IDF² weighting on face-specific vocabulary.

### Output Modes

Three modes, mutually exclusive:

| Mode | Parameter | Size | Use When |
|------|-----------|------|----------|
| **Full** | (default) | ~600KB+ | You need the complete manifold: all active constructs, all tensions, all gems, all nexus connections. Too large for conversational context — save to file and query with jq/python. |
| **Compact** | `compact=true` | ~2KB | You need the coordinate matrix + structural profile + harmonization + spokes + central gem + construction questions. This is the working mode for refinement. |
| **Focused** | `focused=true` | ~500 bytes | You need only: dominant dimensions, neglected dimensions, strongest resonance, coherence, summary sentence. Fastest iteration. |

**For refinement, use `compact=true`** — it gives you the full coordinate matrix with construction questions, which is what you need to diagnose and rewrite. Use `focused=true` only for quick iteration checks. Use full (default) only when you need to inspect the deep structure (active constructs per face, individual tensions, gem nexuses).

### The Full Matrix Structure (compact mode)

```
coordinate:              12 faces, each {x, y, weight}
structural_profile:      edge_count, center_count, edge_ratio, mean_potency
tensions_summary:        total magnitude, positional count, spectrum count
harmonization_pairs:     6 face pairs with resonance + alignment + coverage
spokes:                  12 faces, each with classification + strength
central_gem:             coherence score + classification
construction_questions:  12 faces, each with template + position_summary + classification + potency
```

### Reading the Structural Profile

- **edge_count / center_count**: How many constructs sit at grid edges vs center. A prompt with all centers and zero edges is balanced but may lack strong commitments. A prompt with many edges takes extreme stances.
- **edge_ratio**: 0.0 = no extreme positions, 1.0 = all extreme positions.
- **mean_potency**: Average energy across constructs. 0.6 is the baseline center potency.

### Reading Harmonization Pairs

The server pairs faces into 6 resonance couples:

```
ontology      ↔ praxeology       (Being ↔ Doing)
epistemology  ↔ methodology      (Knowing ↔ Proceeding)
axiology      ↔ ethics           (Worth ↔ Obligation)
teleology     ↔ heuristics       (Purpose ↔ Strategy)
phenomenology ↔ aesthetics       (Experience ↔ Form)
semiotics     ↔ hermeneutics     (Encoding ↔ Interpretation)
```

Each pair has:
- **resonance** (0.0-1.0): How strongly the pair reinforces. Higher = the two faces amplify each other.
- **alignment** (0.0-1.0): How compatible their positions are. 0.98 = nearly identical stances. Low alignment with high resonance = productive tension.
- **coverage_a / coverage_b**: How much of the grid each face covers. Low coverage = narrow focus.

### Reading Spokes

Each face has a spoke connecting it to the whole manifold:
- **classification**: "weakly_integrated", "moderately_integrated", or "strongly_integrated"
- **strength** (0.0-1.0): How much this face participates in the overall coherence

All spokes at "weakly_integrated" means the prompt addresses each concern independently — the faces don't cross-pollinate. For a task prompt this is acceptable. For a design philosophy or living document, you'd want stronger integration.

### Reading the Central Gem

- **coherence** (0.0-1.0): Overall philosophical integration.
  - < 0.3: weakly coherent — faces are isolated
  - 0.3-0.6: moderately coherent — some integration
  - > 0.6: strongly coherent — faces form a unified philosophical fabric
- **classification**: "weakly_coherent", "moderately_coherent", "strongly_coherent"

### Reading Construction Questions

Each face generates a question. The server provides:
- **template**: The question itself — "What entities and relationships does this prompt assume exist?"
- **position_summary**: Where the prompt sits on that face — "moderately Particular + moderately Dynamic"
- **classification**: "corner", "edge", or "center"
- **potency**: Energy level of the construct (0.6 is the baseline center)

The construction questions are the primary diagnostic. If a question reveals a gap you care about, address it in the rewrite. If a question asks about something irrelevant to your prompt's purpose, the gap is intentional — leave it.

### The Full Output (non-compact)

The full output adds these structures beyond compact:

- **active_constructs**: Per-face list of all activated grid positions, each with its own classification, potency, and a unique construction question generated from that specific position. A face may have multiple active constructs (e.g., ontology might activate at (4,7) and (1,7) with different questions).
- **tensions**: Individual tension pairs between specific constructs across faces, with magnitude, cube_tier ("adjacent" or "opposite"), and positional distance.
- **gems**: Nexus connections between faces showing energy flow (source_energy, target_energy, magnitude, type "harmonious" or "conflicting").

This deep structure reveals which specific positions on which faces interact. For example, `ontology.4_7 → epistemology.4_6` might have a tension of 0.01 (negligible) while `ontology.4_7 → phenomenology.6_7` has a tension of 0.05 (meaningful). The full output lets you trace exactly where philosophical energy flows.

## Process

### Step 1: Write

Write your prompt. Your best attempt. Pour domain knowledge into prose. Inhabit the dimensions your purpose actually requires — not every dimension you can reach. A text has a primary register, and the instrument measures it; trying to activate all 12 faces at equal weight in a single text dilutes all of them (see "Register competition" in Known Limitations). Commit to the register the task needs.

### Step 2: Measure

Run it through `create_prompt_basis` with the `intent` parameter and `compact=true`:

```
create_prompt_basis(intent="<the prompt>", compact=true)
```

You'll get the 12-face coordinate matrix with construction questions, harmonization pairs, spokes, and coherence. This is the working dataset for refinement.

For quick checks during iteration, use `focused=true` instead — it returns only dominant dimensions, gaps, resonance, and a summary sentence (~500 bytes).

### Step 2.5: Classify task type

Before interpreting the measurement, establish what kind of task the prompt is for. Not all faces matter equally for every task — register engagement is necessary but not sufficient, and the *right* register depends on purpose.

Infer the task type from the prompt itself. If confidence is high, proceed and disclose the inferred type. If the prompt mixes types meaningfully, or no type fits, ask the user:

> "This prompt reads as (a) engineering / code, (b) analysis / reasoning, (c) policy / safety. Which best matches your intent? If hybrid, name the two most dominant."

Task types and their priorities are tabulated in the **Task-Type Priority Reference** section below. Priority values are H (high — close this gap), M (medium — default), L (low — leave alone). Hybrid task types combine two templates element-wise: H beats M beats L; ties resolve toward H.

### Step 2.6: Compute priority gaps

For each of the 12 faces, compare activation against the priority template for the task type:

```
priority   = template[task_type][face]      # H = 1.0, M = 0.5, L = 0.0
activation = basis.coordinate[face].weight   # normalized if possible
gap        = priority - activation_normalized
```

Output three lists, not one undifferentiated "neglected" list:

- **Critical gaps** — priority H, activation low → must address in the rewrite
- **Acceptable neglect** — priority L, activation low → confirm not addressing is correct for this task
- **Diffusion candidates** — priority L, activation high → candidates for compression (the prompt is spending effort where this task doesn't need it)

Working thresholds for "low" and "high" (activation weights are in [0, 1]):

- **Low:** below ~0.2 (face is near the floor — typical floor value is around 0.10; the server classifies these as "neglected")
- **Mid:** 0.2–0.55 (partially addressed; a H-priority face here is still a gap, but an improvement target rather than a crisis)
- **High:** above ~0.55 (face is engaged; the server typically classifies these as "dominant")

These are working thresholds, not hard bounds. Treat them as calibration hints for the qualitative classification. A H-priority face in mid-range is a soft critical gap — worth strengthening but not blocking. A L-priority face in mid-range is fine; only mark it as diffusion candidate if it's clearly high.

A prompt where every critical gap is closed and all acceptable neglect is confirmed is *priority-aligned*. That is a stronger target than high uniform activation.

### Step 2.6b: Check for routing-collision suspicion

Before recommending intervention, check whether a low activation is plausibly a measurement artifact rather than an inhabitation gap. The BGE bridge has known vocabulary routing collisions — shared vocabulary tends to attribute to the more abstract of two competing faces. The most documented case: ethics-bearing vocabulary (*owe*, *warrant*, *trust*, *duty*, *culpable*, *forbidden*) often routes to axiology when both could claim it.

For each critical gap, do a vocabulary scan. If the user's prompt contains dense vocabulary that *should* activate the gapped face and the adjacent face is dominant, flag the gap as **likely routing collision**, not **inhabitation gap**. Recommend:

1. Do not escalate inhabitation — adding more moral vocabulary when ethics is stuck at 0.10 and axiology at 0.60 will not move the needle. The four-iteration trap is real.
2. Consider indirect activation via a pattern that carries the face through a different route (e.g., a constitutional-style rule list activates ethics via Semiotics+Ethics co-pattern, not by direct vocabulary weight).
3. File the collision as feedback for the engine's disambiguation layer — the known-collision table below is the current frontier.

**Known routing collisions** (update as new cases surface):

| Shared vocabulary | Routes to | Should route to | Symptom |
|---|---|---|---|
| *owe, warrant, trust, duty, forbidden, culpable* | axiology | ethics | Ethics stuck at floor despite dense moral vocabulary |
| *form, shape, recognizable* | aesthetics | context-dependent (aesthetics when qualitative, semiotics when structural) | Aesthetics over-activates on structural descriptions |
| *interpret, read as, means* | hermeneutics & semiotics (tied) | hermeneutics when receiving, semiotics when sending | Semiotics and hermeneutics move in lockstep |
| *purpose, end, goal* | teleology + axiology (split) | teleology (grounding) | Teleology under-activates when worth-framing dominates |

**Paired-face under-resonance** is a related routing issue. Official cube pairs (ontology↔praxeology, epistemology↔methodology, etc.) are symmetric. If a prompt explicitly grounds one face in another (e.g., describes entities and then derives actions from them) but pairs still read as weak-resonance, the symmetric metric cannot express the directional grounding. This is a known limit, not a rewrite gap.

### Step 2.7: Suggest interventions from the pattern library

For each critical gap **not flagged as routing collision**, look up prompt-engineering patterns whose primary activation targets that face. Recommend the lightest-touch pattern not already present. Present options in cost order.

Patterns and their face activations are tabulated in the **Pattern Intervention Reference** section below. Typical recommendations:

> **Critical gap: Methodology (priority H, activation 0.12).** Task is engineering work. Recommended interventions in order of cost:
> 1. Add an explicit "Reasoning: … Result: …" output template (cheapest, activates Semiotics+Methodology)
> 2. Chain of Thought scaffold ("think step by step" or explicit step numbering)
> 3. Worked-example demonstration (if the procedure is non-obvious)
> 4. Full Plan-and-Execute structure (if the task has multiple phases)

### Step 3: Interpret

Use the `interpret_basis` tool on the **focused** result to get the server's plain-language interpretation:

```
interpret_basis(basis="<the JSON result from create_prompt_basis with focused=true>")
```

**Important**: `interpret_basis` requires a `guidance` section in its input. Only the `focused=true` output reliably includes this. If you used `compact=true`, run a second `focused=true` call and pass that result to `interpret_basis`.

The server's interpretation returns:
- Dominant dimensions with their positions and questions
- Neglected dimensions with specific gap descriptions
- Strongest resonance pair
- Summary sentence

**This is the server's reading, not yours.** Present it to the user as the server's interpretation. Your own analysis of positions, harmonization pairs, and spokes is supplementary — label it as such. After presenting the server's interpretation, layer your priority-aware reading on top of it: "the server reports X as neglected; for this task type, X is **critical / acceptable / diffusion-risk**." The server treats all faces uniformly; you do not.

Also read the construction questions directly. Each one asks what your prompt assumes, demands, or neglects about that face:

- If a face is at **(0,0)**: the question asks what foundational commitment you haven't made. The axis names tell you what (0,0) means for that face — e.g., Ontology at (0,0) = Particular+Static, Epistemology at (0,0) = Empirical+Certain.
- If at **center**: the question asks what that balanced position produces and what stronger commitments would obscure.
- If at **edge**: the question asks what that extreme commitment costs.

### Step 4: Rewrite

Address the gaps the construction questions and server interpretation exposed. The critical rule:

**Don't name the dimension — inhabit it.**

- WRONG: "This prompt establishes truth by verifying against authoritative sources" (narrating ABOUT epistemology)
- RIGHT: "How do we know a configured path is correct: by checking it resolves, by verifying contents, or by tracing the config key through code?" (BEING epistemological)

The difference is the mode of engagement. Labeling a dimension doesn't activate it. Asking its question does.

The two new faces require specific attention:
- **Ethics**: Don't say "this is ethical." Instead, pose the obligation: "What duty does this system owe to the user who trusts its output?"
- **Aesthetics**: Don't say "this should be elegant." Instead, attend to form: "What quality of structure would make this system's behavior recognizable as coherent rather than accidental?"

### Step 5: Measure Again with priority overlay

Run the rewritten prompt through `create_prompt_basis`. Compare:
- Did faces move off corners?
- Did weights change? (Compare the coordinate matrices side by side)
- Did new harmonization pairs strengthen?
- Did the construction questions change? (Changed questions mean the manifold sees a different prompt.)
- Did coherence improve?
- **Did each critical gap from Step 2.6 close?** (This is the priority-aware check, not "did everything improve")
- **Were any diffusion candidates compressed?** (The acceptable-neglect faces should not be over-activated just because other faces dropped)
- **Did any flagged routing-collision resolve via indirect activation?** (If you used a co-pattern rather than direct vocabulary, the gapped face may still be stuck even if the intervention worked — measure what the *pattern* activated, not what the *vocabulary* was supposed to)

Present the comparison as a table so the user can see movement:

```
Face             v1 Weight  v2 Weight  Position Change
─────────────────────────────────────────────────────
ontology         0.71       0.68       stable
epistemology     0.61       0.75       Certain → Provisional shift
methodology      0.10       0.10       stuck (see "Known Limitations" below)
```

### Step 6: Repeat

Continue until one of these conditions:
- The construction questions stop revealing gaps you care about
- The same faces keep activating with stable positions (plateau)
- The register has stabilized to match the task's actual purpose (the right faces are engaged at the expense of the wrong ones, and attempting to recover the low-weight faces would cost register focus)
- Coherence and breadth are in the tradeoff position you chose (see "Coherence declines with breadth" in Known Limitations) — further additions would diffuse, further removals would narrow
- **All critical gaps from Step 2.6 are closed and acceptable-neglect faces are confirmed at low activation** (priority-alignment achieved)
- **A suspected routing collision has been either resolved via indirect activation or accepted as unreachable from text** (do not iterate on vocabulary that the bridge cannot attribute correctly)
- The server's interpretation stops changing materially between iterations

## Task-Type Priority Reference

Priority scale: **H** = high (close this gap), **M** = medium (default if unlisted), **L** = low (leave neglected; over-activation is diffusion).

| Task type | High-priority faces | Low-priority faces |
|---|---|---|
| Engineering / code / tests | Semiotics, Methodology, Ontology, Praxeology | Aesthetics, Heuristics |
| Structured extraction / schema | Semiotics, Ontology, Epistemology | Phenomenology, Hermeneutics, Aesthetics |
| Analysis / research / reasoning | Epistemology, Methodology, Hermeneutics, Ontology | Praxeology, Aesthetics |
| Agentic workflow | Praxeology, Teleology, Methodology, Heuristics | Aesthetics, Phenomenology |
| Execution prompt (inheriting plan) | Semiotics, Ontology, Ethics | Praxeology, Teleology, Heuristics |
| Creative writing | Aesthetics, Phenomenology, Hermeneutics, Heuristics | Methodology, Semiotics |
| Policy / safety / moral reasoning | Ethics, Axiology, Teleology, Semiotics | Heuristics, Aesthetics |
| Educational explanation | Hermeneutics, Phenomenology, Methodology, Semiotics | Praxeology, Heuristics |
| Translation / paraphrase | Semiotics, Hermeneutics, Aesthetics | Praxeology, Teleology, Heuristics |
| Summarization | Semiotics, Methodology, Hermeneutics | Praxeology, Heuristics |
| Conversation / chat / persona | Phenomenology, Hermeneutics, Aesthetics, Ethics | Methodology, Semiotics |

Notes:
- "Execution prompt (inheriting plan)" is a specific task type: the prompt executes a pre-designed plan it did not itself generate. Praxeology is *inherited* rather than expressed, so it is not high-priority to measure. Ethics matters because execution prompts need failure-mode prevention.
- Hybrid tasks (e.g., "engineering + policy") combine templates element-wise.
- Priority is a default, not a prescription. The user can override for specific purposes.

## Pattern Intervention Reference

When a face gap is flagged as critical (not routing-collision), these are the patterns to recommend. Ordered roughly by cost within each face.

| Gap face | Patterns | Typical phrasing |
|---|---|---|
| **Methodology** | Reasoning trace structure · Chain of Thought · Worked-example · Plan-and-Execute | "Reason through the steps before…" / "Think step by step." |
| **Semiotics** | Output schema · Reasoning trace structure · Few-shot examples · Output length spec | "Return JSON matching: { … }" / "Format: <reasoning>…</reasoning><answer>…</answer>" |
| **Ontology** | Few-shot examples · Worked-example · Entity definition list · Type hierarchy | "The allowed entities are: …" / "Example: given X, produce Y." |
| **Praxeology** | ReAct · Plan-and-Execute · Tool-call sequence template | "For each step: (1) decide action, (2) run it, (3) observe result, (4) continue." |
| **Epistemology** | Grounding / citation requirement · Self-consistency · Self-critique / reflexion | "Cite the source for each claim." / "Before answering, verify…" |
| **Teleology** | Plan-and-Execute · Goal statement · Outcome specification | "The goal is X. Every step serves X." |
| **Ethics** | Constitutional / rule list · Failure-mode enumeration · Negative constraints | "Never do: …" / "Avoid these mistakes: …" |
| **Axiology** | Worth criteria · Priority ordering · Value framing | "Quality criteria: (1) correct, (2) concise, (3) readable, in that order." |
| **Aesthetics** | Form specification · Tone direction · Output length spec | "The output should read as: deliberate, not accidental." |
| **Hermeneutics** | Role prompt · Audience framing · Step-back prompting | "Explain as if to a domain expert new to this codebase." |
| **Heuristics** | Tree of Thought · "Consider alternatives before committing" · Search prompts | "Explore 2-3 approaches before choosing." |
| **Phenomenology** | Role / persona · Surface/depth framing · Subjective stance | "Three surfaces exist and are not the same surface: …" |

**Lightest-touch heuristic:** if the gap face is structural (Semiotics, Methodology, Ontology, Praxeology), prefer format/template interventions over long prose additions. If the gap face is bias (Ethics, Axiology, Aesthetics, Hermeneutics, Heuristics), prefer concrete list/framing interventions over abstract commitments.

**Most patterns activate multiple faces.** Few-shot carries Ontology alongside Semiotics; Constitutional carries Semiotics alongside Ethics. Use secondary activations to close a second gap with one intervention.

## Known Limitations of Text Refinement

**Vocabulary routing collisions are real.** The BGE bridge systematically routes shared vocabulary to the more abstract of two competing faces. The documented case: duty-bearing vocabulary (*owe*, *warrant*, *trust*, *duty*, *culpable*, *forbidden*) routes to axiology rather than ethics. A four-iteration field test escalated ethics vocabulary from *owe* (v2) to *culpable, forbidden, virtue, lie, sabotage, moral duty* (v4) without moving ethics off 0.10, while axiology rose 0.58 → 0.60 absorbing every addition. **Inhabitation is not the universal fix.** When a face stays at floor despite dense face-specific vocabulary and an adjacent face is already dominant, suspect routing collision (Step 2.6b) and switch to indirect activation via a multi-face pattern (e.g., constitutional rule list activates ethics via its Semiotics+Ethics co-pattern, not via direct vocabulary weight). Do not iterate on inhabitation of vocabulary the bridge cannot attribute correctly. The known collision table is in Step 2.6b; file new observations as feedback.

**Register competition is real.** A text has a primary register, and the BGE bridge measures it. You cannot stack all 12 faces at equal weight in a single text — attempting to do so dilutes all of them. The refinement goal is not maximum uniform activation; it is an activation profile that matches the prompt's actual purpose. If your task is a technical spec, ontology/methodology/semiotics dominating is correct. If it is a piece of moral argument, ethics/axiology dominating is correct. A flat distribution across 12 faces is almost always a sign the text has no register at all.

**Inhabit, don't name — and treat 0.10 as a signal, not a ceiling.** When a face reads at 0.10, the first hypothesis is that the text described the dimension from outside rather than spoke from inside it. A prompt that says "aesthetic quality matters here" while performing no aesthetic discrimination will sit near the floor on aesthetics; a prompt that makes judgments *about form* — which arrangement reads as deliberate, which as accidental — will activate it even without the word "aesthetic." APE 0.7.0 (BGE-large-en-v1.5, 1024d, full-sentence encoding, `FACE_VERNACULAR` at 4× weight for ethics/axiology/methodology) broke the earlier "phenomenology dominates everything" ceiling — so the old claim that certain vocabularies are unreachable is no longer correct. When a face stays low despite deliberate effort, re-read the prose and ask whether it talks *about* the stance or speaks *from* it.

**Coherence declines with breadth.** Adding more activated faces tends to lower the central gem's coherence score, not raise it. Coherence measures philosophical focus — how tightly the activated faces hang together — so a narrow 7-face register with a single clear position will typically score higher coherence than an 8- or 9-face mixed register. This is counterintuitive: activating more dimensions feels like strengthening the prompt, but it often just diffuses the focus the instrument rewards. Decide whether breadth or coherence matters more for your task before optimizing; you generally trade one for the other.

**The intent string is compressed.** When using `focused=true` or `compact=true`, the engine processes a compressed representation of your text. Nuanced sections (ethical framing, teleological purpose, aesthetic criteria) may not register if they're a small portion of a large prompt. The prompt's actual philosophical content can be richer than what the measurement captures.

**Weights are relative, not absolute.** A weight of 0.73 does not mean "73% semiotic" — it means stronger than the 0.10 floor within this single measurement. Cross-prompt comparison is meaningful only when prompts are similar in length and domain. IDF² weighting on face-specific vocabulary means rare, face-distinctive words dominate the signal — filler prose with generic terms will produce diffuse, low-coherence measurements regardless of topic.

## Advanced: The Coordinate Form

After text refinement plateaus, a prompt has a dual form:
- **The text** is what a human reads and an LLM executes
- **The coordinate vector** is its philosophical fingerprint

To work in coordinate space:

```
create_prompt_basis(coordinate={
  "ontology":      {"x": 5, "y": 7, "weight": 0.70},
  "epistemology":  {"x": 4, "y": 4, "weight": 0.75},
  "axiology":      {"x": 3, "y": 8, "weight": 0.60},
  "teleology":     {"x": 7, "y": 5, "weight": 0.65},
  "phenomenology": {"x": 6, "y": 8, "weight": 0.66},
  "ethics":        {"x": 7, "y": 6, "weight": 0.55},
  "aesthetics":    {"x": 6, "y": 9, "weight": 0.60},
  "praxeology":    {"x": 5, "y": 6, "weight": 0.51},
  "methodology":   {"x": 6, "y": 5, "weight": 0.70},
  "semiotics":     {"x": 4, "y": 7, "weight": 0.51},
  "hermeneutics":  {"x": 4, "y": 6, "weight": 0.55},
  "heuristics":    {"x": 5, "y": 6, "weight": 0.53}
})
```

The coordinate form lets you specify exact positions and weights, bypassing the BGE bridge entirely. Use this to:
- Set the target topology you want the text to achieve
- Activate faces that the BGE bridge can't detect in your text (less common post-0.7.0, but still possible for deeply metaphorical or technical-domain texts)
- Stress test how position changes affect tension and coherence

**Important**: Coordinate mode with `focused=true` returns guidance with all 12 faces engaged (no "neglected" dimensions), because you're specifying positions directly rather than having them inferred from text. Coherence will typically be lower than text mode because coordinate positions lack the semantic connections that text creates.

### Stress Testing

Use `explore_space` with the `stress_test` operation to find breakpoints and improvements:

```
explore_space(operation="stress_test", coordinate={...})
```

Returns two lists:
- **breakpoints**: Perturbations that increase tension (fragile positions — moving there would destabilize)
- **improvements**: Perturbations that decrease tension or increase coherence (opportunities — moving there would strengthen)

Each entry shows: face, from position, to position, tension_delta, coherence_delta. Look for improvements with negative tension_delta AND positive coherence_delta — those are the highest-leverage moves.

### Building Relations

Use `extend_schema` to define explicit relationships between face positions:

```
extend_schema(
  operation="add_relation",
  source_id="ontology.5_7",
  target_id="epistemology.4_4",
  relation_type="REQUIRES",
  strength=0.8
)
```

Relation types:
- **REQUIRES** — dependency chains (ontology requires epistemology)
- **TENSIONS_WITH** — productive conflict (axiology tensions with praxeology = completeness vs speed)
- **GENERATES** — creative potential (phenomenology generates hermeneutics = experience generates interpretive need)
- **RESOLVES** — resolution paths (methodology resolves axiology = method resolves value tension)
- **COMPATIBLE_WITH** — alignment (epistemology compatible with semiotics = truth-verification aligns with meaning-encoding)

Relations affect the tension and coherence calculations. After adding relations, re-run the coordinate basis or stress test to see their effect.

### The Refinement Workflow at Advanced Stage

1. Text iterations plateau (3-5 rounds)
2. Run `compact=true` to get the final text-derived coordinate matrix
3. Use that matrix as the starting point for `coordinate` mode
4. Adjust positions for faces the BGE bridge couldn't activate
5. Run `stress_test` to find high-leverage moves
6. Add relations via `extend_schema` to define the prompt's intended philosophical topology
7. Use the stress test improvements to guide final text edits
8. The coordinate form becomes the prompt's spec; the text becomes its implementation

## Transparency

When presenting measurements to the user:
- **Show the coordinate matrix** — the (x, y, weight) triples for all 12 faces
- **Show the server's interpretation** — from the guidance section, not your own narrative
- **Label your own analysis separately** — "The server says X. My reading of the harmonization pairs suggests Y."
- **Acknowledge what the numbers don't tell you** — the weight computation is opaque, the BGE bridge can still miss metaphorical framing that doesn't align with face-specific vocabulary, and the prompt's actual philosophical content may exceed what the measurement captures

## Tools Required

- `create_prompt_basis` — measure intent (with BGE-large-en-v1.5 semantic bridge, 1024d) or coordinates. Use `compact=true` for the working matrix, `focused=true` for quick iteration checks.
- `interpret_basis` — server's plain-language interpretation. Requires `focused=true` output (needs the `guidance` section).
- `extend_schema` — add constructs and relations (advanced mode)
- `explore_space` — inspect faces, constructs, spokes, stress test, triangulate (advanced mode)
