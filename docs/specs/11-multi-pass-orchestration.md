# Spec 11 — Multi-Pass Orchestration

## Purpose

Defines the three multi-pass operations that invoke the pipeline multiple times: `stress_test`, `triangulate`, and `deepen`. These live above the pipeline, not inside it.

---

## stress_test(coordinate)

### Purpose

Perturb each axis to nearby grid positions. Run the pipeline for each perturbation. Compare results against the baseline to find breakpoints (where things get worse) and improvements (where things get better).

### Input

| Parameter | Type | Description |
|---|---|---|
| `coordinate` | dict | A complete 10-axis coordinate |

### Algorithm

```python
def stress_test(coordinate: dict, pipeline: PipelineRunner) -> dict:
    # 1. Run baseline
    baseline = pipeline.run(coordinate)

    # 2. Generate perturbations
    perturbations = []
    for branch in coordinate:
        bx, by = coordinate[branch]["x"], coordinate[branch]["y"]
        # Try adjacent grid positions (±1 on each axis, within bounds)
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (1,1)]:
            nx, ny = bx + dx, by + dy
            if 0 <= nx <= 9 and 0 <= ny <= 9 and (nx, ny) != (bx, by):
                modified = deep_copy(coordinate)
                modified[branch] = {"x": nx, "y": ny, "weight": coordinate[branch]["weight"]}
                perturbations.append({
                    "branch": branch,
                    "from": (bx, by),
                    "to": (nx, ny),
                    "coordinate": modified,
                })

    # 3. Run pipeline for each perturbation
    results = []
    for p in perturbations:
        result = pipeline.run(p["coordinate"])
        tension_delta = result["tensions"]["total_magnitude"] - baseline["tensions"]["total_magnitude"]
        coherence_delta = result["central_gem"]["coherence"] - baseline["central_gem"]["coherence"]
        results.append({
            "branch": p["branch"],
            "from": p["from"],
            "to": p["to"],
            "tension_delta": tension_delta,
            "coherence_delta": coherence_delta,
            "new_tension": result["tensions"]["total_magnitude"],
            "new_coherence": result["central_gem"]["coherence"],
        })

    # 4. Classify
    breakpoints = [r for r in results if r["tension_delta"] > 0.1]
    improvements = [r for r in results if r["tension_delta"] < -0.1 or r["coherence_delta"] > 0.01]

    return {
        "baseline_tension": baseline["tensions"]["total_magnitude"],
        "baseline_coherence": baseline["central_gem"]["coherence"],
        "perturbations_tested": len(results),
        "breakpoints": sorted(breakpoints, key=lambda r: r["tension_delta"], reverse=True),
        "improvements": sorted(improvements, key=lambda r: r["tension_delta"]),
        "all_results": results,
    }
```

### Output

```json
{
  "baseline_tension": 0.0,
  "baseline_coherence": 0.0,
  "perturbations_tested": 0,
  "breakpoints": [],
  "improvements": [],
  "all_results": []
}
```

### Computational Cost

- 10 branches × ~6 adjacent positions = ~60 perturbations
- ~60 pipeline runs × ~150ms = ~9 seconds
- Bounded and predictable

---

## triangulate(coordinate_a, coordinate_b)

### Purpose

Run the pipeline for two different coordinates. Compare the results to understand how two intents relate dimensionally.

### Input

| Parameter | Type |
|---|---|
| `coordinate_a` | dict — complete 10-axis coordinate |
| `coordinate_b` | dict — complete 10-axis coordinate |

### Algorithm

```python
def triangulate(coord_a: dict, coord_b: dict, pipeline: PipelineRunner, G: nx.Graph) -> dict:
    result_a = pipeline.run(coord_a)
    result_b = pipeline.run(coord_b)

    # Per-branch construct intersection
    intersection = {}
    for branch in coord_a:
        a_ids = {f"{c['branch']}.{c['x']}_{c['y']}" for c in result_a["active_constructs"].get(branch, [])}
        b_ids = {f"{c['branch']}.{c['x']}_{c['y']}" for c in result_b["active_constructs"].get(branch, [])}
        intersection[branch] = list(a_ids & b_ids)

    # Shared tensions
    a_tension_pairs = {tuple(sorted(t["between"])) for t in result_a["tensions"].get("direct", [])}
    b_tension_pairs = {tuple(sorted(t["between"])) for t in result_b["tensions"].get("direct", [])}
    shared_tensions = list(a_tension_pairs & b_tension_pairs)

    # Spoke comparison
    spoke_comparison = {}
    for branch in coord_a:
        sa = result_a["spokes"].get(branch, {})
        sb = result_b["spokes"].get(branch, {})
        spoke_comparison[branch] = {
            "a_classification": sa.get("classification", "unknown"),
            "b_classification": sb.get("classification", "unknown"),
            "strength_delta": sa.get("strength", 0) - sb.get("strength", 0),
            "consistency_delta": sa.get("consistency", 0) - sb.get("consistency", 0),
        }

    # Coordinate distance
    distance = coordinate_distance(coord_a, coord_b, G)

    return {
        "distance": distance,
        "intersection": intersection,
        "shared_tensions": shared_tensions,
        "spoke_comparison": spoke_comparison,
        "a_coherence": result_a["central_gem"]["coherence"],
        "b_coherence": result_b["central_gem"]["coherence"],
    }
```

### Output

```json
{
  "distance": 0.0,
  "intersection": {},
  "shared_tensions": [],
  "spoke_comparison": {},
  "a_coherence": 0.0,
  "b_coherence": 0.0
}
```

### Computational Cost

- 2 pipeline runs × ~150ms = ~300ms

---

## deepen(construction_basis)

### Purpose

Recursive gem condensation. Takes a completed construction basis, selects gems for condensation into center points of uninvolved branches, and runs the pipeline again at a deeper level of philosophical integration.

### Input

| Parameter | Type |
|---|---|
| `construction_basis` | dict — output from a completed pipeline run |
| `condensation_targets` | list[dict] — which gems to condense where (optional; auto-selected if omitted) |

### Algorithm

```python
def deepen(basis: dict, pipeline: PipelineRunner, targets: list = None) -> dict:
    if targets is None:
        targets = auto_select_condensation_targets(basis)

    # Build modified coordinate from condensation
    new_coordinate = dict(basis["coordinate"])
    for target in targets:
        gem = target["gem"]
        dest_branch = target["destination_branch"]
        # Map gem magnitude to a center-point position
        # Higher magnitude → closer to grid center (4,4)/(5,5)
        # Lower magnitude → closer to grid periphery (but still center-class)
        cx, cy = magnitude_to_center_position(gem["magnitude"])
        new_coordinate[dest_branch] = {
            "x": cx,
            "y": cy,
            "weight": gem["magnitude"],  # gem magnitude becomes the weight
        }

    # Run pipeline with modified coordinate
    deeper_basis = pipeline.run(new_coordinate)
    deeper_basis["depth"] = basis.get("depth", 0) + 1
    deeper_basis["condensation_source"] = targets

    return deeper_basis

def auto_select_condensation_targets(basis: dict) -> list:
    """Select top gems and map them to uninvolved branches."""
    gems = sorted(basis.get("gems", []), key=lambda g: g["magnitude"], reverse=True)
    targets = []
    used_branches = set()

    for gem in gems[:3]:  # top 3 gems
        nexus_parts = gem["nexus"].split(".")  # "nexus.source.target"
        source = nexus_parts[1]
        target = nexus_parts[2]
        # Find an uninvolved branch (not source, not target, not already used)
        for branch in ALL_BRANCHES:
            if branch not in (source, target) and branch not in used_branches:
                targets.append({
                    "gem": gem,
                    "destination_branch": branch,
                })
                used_branches.add(branch)
                break

    return targets

def magnitude_to_center_position(magnitude: float) -> tuple[int, int]:
    """Map gem magnitude [0,1] to a center grid position.

    Higher magnitude → closer to (5,5) (true center)
    Lower magnitude → closer to (2,2) or (7,7) (near edges but still center-class)
    """
    # Scale magnitude to offset from center
    # magnitude 1.0 → (5, 5)
    # magnitude 0.5 → (3, 3) or (6, 6)
    # magnitude 0.0 → (1, 1) or (8, 8)
    offset = int(round((1 - magnitude) * 4))  # 0-4
    # Alternate between upper-left and lower-right quadrants
    if magnitude >= 0.5:
        return (5 - offset, 5 - offset)  # approaches center from upper-left
    else:
        return (4 + offset, 4 + offset)  # approaches center from lower-right
```

### Output

Same structure as `create_prompt_basis` output, plus:
- `depth`: integer indicating recursion depth (0 for first pass, 1 for first deepen, etc.)
- `condensation_source`: which gems were condensed where

### Termination

The client controls recursion depth. Each call to `deepen` produces a construction basis that can be deepened again. There is no automatic termination — the client decides when the construction basis is sufficient.

Recommended maximum depth: 3 (beyond this, the construction basis typically stabilizes — gem magnitudes converge).

### Computational Cost

- 1 pipeline run per deepen call × ~150ms
- Typical use: 1-3 deepen calls = 150-450ms additional
