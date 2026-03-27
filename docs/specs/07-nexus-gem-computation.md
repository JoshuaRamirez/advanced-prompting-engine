# Spec 07 — Nexus/Gem Computation

## Purpose

Defines the nexus operation lifecycle, the gem integration function, directionality semantics, and which nexi are computed per pipeline run.

---

## Nexus Operation Lifecycle

```
1. IDENTIFY   — which nexus nodes to compute (based on active branches)
2. RECEIVE    — gather edge constructs from both connected branches
3. INTEGRATE  — compute the harmonic juxtaposition of both sets of edge energies
4. PRODUCE    — output a gem (magnitude + harmony type)
5. ASSOCIATE  — attach the gem to the nexus node for spoke aggregation
```

---

## Which Nexi Are Computed

Not all 90 nexi are computed on every pipeline run. Only nexi between branches that have active constructs:

```python
def identify_active_nexi(active_constructs: dict, G: nx.Graph) -> list[str]:
    active_branches = [b for b in active_constructs if active_constructs[b]]
    nexi = []
    for source in active_branches:
        for target in active_branches:
            if source != target:
                nexus_id = f"nexus.{source}.{target}"
                if nexus_id in G.nodes:
                    nexi.append(nexus_id)
    return nexi
```

If all 10 branches have active constructs: 90 nexi computed.
If only 5 branches active: 5 × 4 = 20 nexi computed.

---

## Directionality

`nexus.A.B` and `nexus.B.A` are distinct entities. They produce different gems because:

- `nexus.A.B` integrates A's edge energies INTO B's context (what does A contribute to B?)
- `nexus.B.A` integrates B's edge energies INTO A's context (what does B contribute to A?)

In the gem computation (Spec 05, Section 10), the `source_branch` determines which branch's active constructs receive the 2x potency boost. This asymmetry makes directional nexi produce different magnitude values.

---

## Receive Phase

For a nexus between source branch A and target branch B:

**From source branch A:**
- All 36 edge-classified constructs (corners, midpoints, edges)
- Each with its potency (1.0, 0.95, 0.85)
- Active constructs get 2x potency boost

**From target branch B:**
- All 36 edge-classified constructs
- Same potency + active boost logic

These two sets of edge energies are the nexus's inputs.

---

## Integrate Phase

The integration function (from Spec 05, Section 10) computes:

1. **Source energy ratio**: sum of potencies of A's edge constructs (active = 2x) / maximum possible
2. **Target energy ratio**: same for B
3. **Gem magnitude**: harmonic mean of the two ratios

The harmonic mean ensures both branches must contribute for a high gem. One-sided energy produces a low magnitude.

---

## Produce Phase

The gem output:

```python
{
    "nexus": "nexus.A.B",
    "magnitude": float,       # harmonic mean of energy ratios, range [0, 1]
    "type": "harmonious" | "conflicting",
    "source_energy": float,   # source branch energy ratio
    "target_energy": float,   # target branch energy ratio
}
```

Harmony type determination:
- Count TENSIONS_WITH edges between active constructs across the two branches
- Count COMPATIBLE_WITH edges between active constructs across the two branches
- If compatible >= tension: "harmonious"
- Otherwise: "conflicting"

---

## Computational Cost

- Per nexus: 2 × 36 potency lookups + 1 harmonic mean + edge scan for harmony = O(E) where E is edges between the two branches' active constructs
- Total for 90 nexi: O(90 × E) — bounded and fast
- Expected time: ~5ms for all 90 nexi
