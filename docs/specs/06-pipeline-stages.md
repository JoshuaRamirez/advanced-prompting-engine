# Spec 06 — Pipeline Stages

## Purpose

Defines each of the 8 pipeline stages as a formal contract: input type, output type, preconditions, postconditions, operations called, and error handling.

---

## Pipeline State Object

All stages operate on and contribute to a shared accumulating state:

```python
@dataclass
class PipelineState:
    # Input
    raw_input: str | dict                     # NL string or coordinate object

    # Stage 1 output
    partial_coordinate: dict | None = None    # branch → Optional[{x, y, weight, confidence}]

    # Stage 2 output
    coordinate: dict | None = None            # branch → {x, y, weight} — all 10 filled

    # Stage 3 output
    manifold_position: dict | None = None     # centroid + per_branch neighborhoods

    # Stage 4 output
    active_constructs: dict | None = None     # branch → list[{x, y, classification, potency, question, ...}]

    # Stage 5 output
    tensions: dict | None = None              # total_magnitude, direct[], spectrum[], cascading[]

    # Stage 6 output
    gems: list | None = None                  # list of gem dicts
    nexus_details: list | None = None         # list of nexus interaction details

    # Stage 7 output
    spokes: dict | None = None                # branch → spoke profile
    central_gem: dict | None = None           # coherence + classification

    # Stage 8 output
    construction_basis: dict | None = None    # the final output
```

---

## Stage 1 — Intent Parser

### Contract

| Aspect | Value |
|---|---|
| **Input** | `PipelineState.raw_input` — either a string or a coordinate dict |
| **Output** | `PipelineState.partial_coordinate` |
| **Precondition** | TF-IDF cache is populated |
| **Postcondition** | partial_coordinate has 0-10 branches filled; unfilled branches are None |

### Logic

```
IF raw_input is a coordinate dict:
    validate structure (each branch has x, y, weight)
    set partial_coordinate = raw_input (all 10 filled)
    RETURN

tokenize raw_input (lowercase, split)
for each branch:
    for each construct in branch (100 total):
        compute tag_score (overlap of input tokens with construct tags)
        compute tfidf_score (cosine similarity in shared TF-IDF space)
        combined = tag_score * 0.6 + tfidf_score * 0.4

    best = max scoring construct in this branch
    if best.combined > MATCH_THRESHOLD (0.15):
        set partial_coordinate[branch] = {x, y, weight, confidence}
        weight = token_emphasis (matched tokens for this branch / all matched tokens)
        confidence = best.combined
    else:
        set partial_coordinate[branch] = None
```

### Error Handling

- Empty string input: all branches are None → Stage 2 fills all via CSP
- Pre-formed coordinate with invalid branch names: raise `InvalidCoordinate`
- Pre-formed coordinate with out-of-range x/y: raise `InvalidCoordinate`

---

## Stage 2 — Coordinate Resolver

### Contract

| Aspect | Value |
|---|---|
| **Input** | `PipelineState.partial_coordinate` |
| **Output** | `PipelineState.coordinate` |
| **Precondition** | partial_coordinate exists (may have None entries) |
| **Postcondition** | coordinate has all 10 branches filled with valid (x, y, weight) |

### Logic

Calls `resolve_coordinate()` from Spec 05 (CSP, Section 5).

### Error Handling

- All branches None with no COMPATIBLE_WITH edges in graph: each branch gets fallback (5, 5) with weight 0.15
- EXCLUDES conflict between two specified positions: raise `ConflictingCoordinate` with details

---

## Stage 3 — Position Computer

### Contract

| Aspect | Value |
|---|---|
| **Input** | `PipelineState.coordinate` |
| **Output** | `PipelineState.manifold_position` |
| **Precondition** | Embedding cache is populated; coordinate is complete |
| **Postcondition** | manifold_position contains centroid vector and per-branch neighborhoods |

### Logic

```
for each branch:
    construct_id = f"{branch}.{coord[branch].x}_{coord[branch].y}"
    embedding = embedding_cache.get(construct_id)
    weighted_embeddings.append(coord[branch].weight * embedding)

centroid = sum(weighted_embeddings) / sum(weights)

per_branch = {}
for each branch:
    primary_id = f"{branch}.{coord[branch].x}_{coord[branch].y}"
    primary_embedding = embedding_cache.get(primary_id)
    nearby = []
    for construct in all_constructs_in_branch:
        dist = np.linalg.norm(primary_embedding - embedding_cache.get(construct.id))
        if dist > 0 and dist < activation_threshold(branch):
            nearby.append({id, dist, classification, potency})
    per_branch[branch] = {primary: ..., nearby: sorted by distance}
```

### Error Handling

- Construct not in embedding cache: raise `EmbeddingMissing` (indicates cache needs rebuild)

---

## Stage 4 — Construct Resolver

### Contract

| Aspect | Value |
|---|---|
| **Input** | `PipelineState.manifold_position` |
| **Output** | `PipelineState.active_constructs` |
| **Precondition** | manifold_position exists with per-branch neighborhoods |
| **Postcondition** | active_constructs has 1+ constructs per branch, each with full properties |

### Logic

```
for each branch:
    active = [primary_construct]  # always included
    for neighbor in manifold_position.per_branch[branch].nearby:
        if neighbor.distance < activation_threshold(branch):
            active.append(full_construct_properties(neighbor))
    active_constructs[branch] = active
```

Each active construct entry:
```python
{
    "branch": str,
    "x": int,
    "y": int,
    "id": str,          # "branch.x_y"
    "classification": str,
    "potency": float,
    "question": str,
    "tags": list[str],
}
```

### Error Handling

- No constructs in a branch (impossible for canonical graph): raise `EmptyBranch`

---

## Stage 5 — Tension Analyzer

### Contract

| Aspect | Value |
|---|---|
| **Input** | `PipelineState.active_constructs` |
| **Output** | `PipelineState.tensions` |
| **Precondition** | active_constructs populated |
| **Postcondition** | tensions has total_magnitude, direct[], spectrum[], cascading[], resolution_paths[] |

### Logic

Calls `compute_tensions()` from Spec 05 (Section 6).

Additionally for spectrum oppositions, retrieves the spectrum's `question` property (from Spec 03a Q37-Q55) if it exists:
```
for each spectrum opposition in tensions.spectrum:
    edge_data = G.edges[active_id, opposite_id]
    spectrum_question = edge_data.get("question", None)
    opposition.spectrum_question = spectrum_question  # may be None for spectrums without authored questions
```

Additionally collects resolution paths:
```
for each tension:
    check graph for RESOLVES edges targeting either endpoint
    if found: add to resolution_paths
```

### Error Handling

- No tensions found: total_magnitude = 0.0, all lists empty — valid state

---

## Stage 6 — Nexus/Gem Analyzer

### Contract

| Aspect | Value |
|---|---|
| **Input** | `PipelineState.active_constructs` |
| **Output** | `PipelineState.gems`, `PipelineState.nexus_details` |
| **Precondition** | active_constructs populated |
| **Postcondition** | gems contains one gem per branch-pair where both branches have active constructs; nexus_details has interaction metadata |

### Logic

```
active_branches = [b for b in active_constructs if active_constructs[b]]
gems = []
for source in active_branches:
    for target in active_branches:
        if source != target:
            gem = compute_gem(source, target, active_constructs, G)
            gems.append(gem)
```

This produces up to 90 gems (10 × 9) if all branches have active constructs. If fewer branches are active, fewer gems are computed.

### Error Handling

- Only 1 active branch: no gems produced (empty list) — valid state
- Gem computation returns 0 magnitude: include it (a weak interaction is still an interaction)

---

## Stage 7 — Spoke Analyzer

### Contract

| Aspect | Value |
|---|---|
| **Input** | `PipelineState.gems` |
| **Output** | `PipelineState.spokes`, `PipelineState.central_gem` |
| **Precondition** | gems list exists (may be empty) |
| **Postcondition** | spokes has one profile per branch (may have 0 gems); central_gem has coherence |

### Logic

```
for each branch:
    branch_gems = [g for g in gems if g.nexus starts with f"nexus.{branch}."]
    spoke = compute_spoke_shape(branch_gems)
    spokes[branch] = spoke

compute_contributions(spokes)

for each spoke:
    spoke.classification = classify_spoke(spoke)

central_gem = compute_central_gem(spokes)
```

### Error Handling

- No gems for a branch: spoke has strength=0, consistency=1.0, polarity=0, classification="weakly_integrated"
- No gems at all: central_gem coherence = 0.0, classification = "incoherent"

---

## Stage 8 — Construction Bridge

### Contract

| Aspect | Value |
|---|---|
| **Input** | All accumulated PipelineState fields |
| **Output** | `PipelineState.construction_basis` |
| **Precondition** | All previous stages completed |
| **Postcondition** | construction_basis is the complete output dict |

### Logic

```
output = {}
output["coordinate"] = state.coordinate
output["active_constructs"] = format_active_constructs(state.active_constructs)
output["spectrum_opposites"] = collect_spectrum_opposites(state.active_constructs, G)
output["structural_profile"] = compute_structural_profile(state.active_constructs)
output["tensions"] = state.tensions
output["generative_combinations"] = find_generatives(state.active_constructs, G)
output["gems"] = state.gems
output["spokes"] = state.spokes
output["central_gem"] = state.central_gem
output["construction_questions"] = {}

for each branch:
    template = branch_node.construction_template
    active = state.active_constructs[branch]
    opposite = get_spectrum_opposite(active[0], G)  # primary construct's opposite
    spoke = state.spokes[branch]
    tensions_here = [t for t in state.tensions if branch in t]

    spectrum_edge = get_spectrum_edge(active[0], opposite, G) if opposite else None
    spectrum_question = spectrum_edge.get("question") if spectrum_edge else None

    output["construction_questions"][branch] = {
        "template": template,
        "active_question": active[0].question,
        "active_question_revisited": active[0].get("question_revisited"),
        "opposite_question": opposite.question if opposite else None,
        "spectrum_question": spectrum_question,
        "classification": active[0].classification,
        "potency": active[0].potency,
        "spoke_profile": spoke.classification,
        "spoke_strength": spoke.strength,
        "tension_note": summarize_tensions(tensions_here),
        "generative_note": summarize_generatives(branch, generatives),
    }
```

### Error Handling

- Missing spoke for a branch: use default values (classification="unknown", strength=0)
- No spectrum opposite (center construct): opposite_question = None

---

## Pipeline Runner

```python
class PipelineRunner:
    def __init__(self, graph, embedding_cache, tfidf_cache):
        self.stages = [
            IntentParser(tfidf_cache),
            CoordinateResolver(graph),
            PositionComputer(embedding_cache),
            ConstructResolver(graph, embedding_cache),
            TensionAnalyzer(graph),
            NexusGemAnalyzer(graph),
            SpokeAnalyzer(),
            ConstructionBridge(graph),
        ]

    def run(self, raw_input: str | dict) -> dict:
        state = PipelineState(raw_input=raw_input)
        for stage in self.stages:
            stage.execute(state)
        return state.construction_basis
```

Each stage receives the full PipelineState and mutates it by adding its output. Stages are executed strictly in order. No stage reads output from a later stage.
