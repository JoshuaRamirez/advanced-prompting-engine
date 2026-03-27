# Spec 05 — Mathematical Operations

## Purpose

Defines every mathematical operation with exact input types, output types, formulas, edge cases, and numpy implementation notes. Each operation is a pure function of its inputs — no side effects, no graph mutations.

---

## 1. TF-IDF Vectorization

**Used by:** Intent Parser (Stage 1), TF-IDF Cache

### Input

| Parameter | Type | Description |
|---|---|---|
| `documents` | list[str] | The 1000 construct question texts |
| `query` | str | The client's natural language intent |

### Computation

```python
import numpy as np

def build_tfidf_matrix(documents: list[str]) -> tuple[np.ndarray, list[str]]:
    """Build TF-IDF matrix for all documents.

    Returns: (matrix of shape (n_docs, vocab_size), vocabulary list)
    """
    # Tokenize
    tokenized = [doc.lower().split() for doc in documents]

    # Build vocabulary
    vocab = sorted(set(word for doc in tokenized for word in doc))
    word_to_idx = {w: i for i, w in enumerate(vocab)}

    n_docs = len(documents)
    vocab_size = len(vocab)

    # Term frequency
    tf = np.zeros((n_docs, vocab_size))
    for i, doc in enumerate(tokenized):
        for word in doc:
            tf[i, word_to_idx[word]] += 1
        if len(doc) > 0:
            tf[i] /= len(doc)

    # Inverse document frequency
    df = np.sum(tf > 0, axis=0)  # document frequency per term
    idf = np.log((n_docs + 1) / (df + 1)) + 1  # smoothed IDF

    # TF-IDF
    tfidf = tf * idf

    # Normalize rows to unit length
    norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)  # avoid division by zero
    tfidf = tfidf / norms

    return tfidf, vocab

def vectorize_query(query: str, vocab: list[str]) -> np.ndarray:
    """Project a query into the same TF-IDF space."""
    word_to_idx = {w: i for i, w in enumerate(vocab)}
    tokens = query.lower().split()
    vec = np.zeros(len(vocab))
    for word in tokens:
        if word in word_to_idx:
            vec[word_to_idx[word]] += 1
    if len(tokens) > 0:
        vec /= len(tokens)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec /= norm
    return vec
```

### Output

| Return | Type | Description |
|---|---|---|
| `tfidf_matrix` | np.ndarray (1000, vocab_size) | Normalized TF-IDF vectors for all constructs |
| `vocab` | list[str] | Vocabulary mapping index → word |
| `query_vector` | np.ndarray (vocab_size,) | Normalized TF-IDF vector for the query |

### Edge Cases

- Empty query: returns zero vector → all cosine similarities are 0 → no matches
- Query with no vocabulary overlap: same as empty
- Duplicate words in query: TF handles frequency naturally
- Very long query: TF normalization prevents bias

---

## 2. Cosine Similarity

**Used by:** Intent Parser (Stage 1)

### Input

| Parameter | Type |
|---|---|
| `a` | np.ndarray (vocab_size,) |
| `b` | np.ndarray (vocab_size,) |

### Computation

```python
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    dot = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))
```

### Output

| Return | Type | Range |
|---|---|---|
| similarity | float | [0, 1] for non-negative TF-IDF vectors |

### Edge Cases

- Zero vector input: returns 0.0 (no similarity)
- Identical vectors: returns 1.0

---

## 3. Spectral Embedding

**Used by:** Position Computer (Stage 3), Embedding Cache

### Input

| Parameter | Type | Description |
|---|---|---|
| `G` | nx.Graph | The full graph (1101+ nodes) |
| `k` | int | Embedding dimensionality. Default: `min(20, n_nodes - 1)` |

### Computation

```python
def compute_spectral_embedding(G: nx.Graph, k: int = 20) -> dict[str, np.ndarray]:
    """Compute spectral embedding for all nodes.

    Uses the graph Laplacian eigendecomposition.
    """
    A = nx.to_numpy_array(G)
    n = A.shape[0]
    k = min(k, n - 1)

    D = np.diag(A.sum(axis=1))
    L = D - A

    eigenvalues, eigenvectors = np.linalg.eigh(L)

    # Skip the trivial eigenvector (index 0, eigenvalue ≈ 0)
    # Use eigenvectors 1 through k
    embedding_matrix = eigenvectors[:, 1:k + 1]

    nodes = list(G.nodes())
    return {nodes[i]: embedding_matrix[i] for i in range(n)}
```

### Output

| Return | Type | Description |
|---|---|---|
| embeddings | dict[str, np.ndarray] | Node ID → k-dimensional vector |

### Edge Cases

- Disconnected graph: eigenvalue 0 has multiplicity > 1. The embedding still works but disconnected components will be separated in embedding space. This is acceptable — disconnected constructs SHOULD be far apart.
- Graph with 1 node: k = 0, returns empty vectors. Should not occur (minimum graph is 1101 nodes).
- Symmetric Laplacian: `np.linalg.eigh` handles symmetric matrices correctly and returns real eigenvalues.

### Performance

- `np.linalg.eigh` on 1101×1101 matrix: ~50ms
- Memory: 1101 × 20 × 8 bytes = ~176KB for embeddings

---

## 4. Graph Distance Metric

**Used by:** Position Computer (Stage 3), Coordinate Resolver (Stage 2)

### Input

| Parameter | Type | Description |
|---|---|---|
| `G` | nx.Graph | The graph |
| `source` | str | Source node ID |
| `target` | str | Target node ID |

### Computation

```python
EDGE_WEIGHTS = {
    "COMPATIBLE_WITH": 0.2,
    "TENSIONS_WITH": 0.8,
    "SPECTRUM_OPPOSITION": 0.6,
    "REQUIRES": 0.1,
    "EXCLUDES": float('inf'),
    "GENERATES": 0.3,
    "RESOLVES": 0.2,
    "HAS_CONSTRUCT": 0.0,  # structural, not traversal-meaningful
    "PRECEDES": 0.0,
    "NEXUS_SOURCE": 0.4,
    "NEXUS_TARGET": 0.4,
    "CENTRAL_GEM_LINK": 0.5,
}

def graph_distance(G: nx.Graph, source: str, target: str) -> float:
    """Compute weighted shortest path distance."""
    def weight_fn(u, v, data):
        return EDGE_WEIGHTS.get(data.get("relation", ""), 1.0)

    try:
        return nx.shortest_path_length(G, source, target, weight=weight_fn)
    except nx.NetworkXNoPath:
        return float('inf')
```

### Coordinate Distance

```python
def coordinate_distance(coord_a: dict, coord_b: dict, G: nx.Graph) -> float:
    """Weighted sum of per-axis graph distances."""
    total = 0.0
    weight_sum = 0.0
    for branch in coord_a:
        a_id = f"{branch}.{coord_a[branch]['x']}_{coord_a[branch]['y']}"
        b_id = f"{branch}.{coord_b[branch]['x']}_{coord_b[branch]['y']}"
        w = (coord_a[branch]['weight'] + coord_b[branch]['weight']) / 2
        d = graph_distance(G, a_id, b_id)
        if d < float('inf'):
            total += w * d
            weight_sum += w
    if weight_sum == 0:
        return float('inf')
    return total / weight_sum
```

### Output

| Return | Type | Range |
|---|---|---|
| distance | float | [0, ∞) |

### Edge Cases

- No path exists: returns `inf`
- Same node: returns 0.0
- EXCLUDES edges: weight = inf → path through EXCLUDES is never shortest

---

## 5. Constraint Propagation (CSP)

**Used by:** Coordinate Resolver (Stage 2)

### Input

| Parameter | Type | Description |
|---|---|---|
| `partial_coord` | dict | Branch → Optional[{x, y, weight}] — some axes may be None |
| `G` | nx.Graph | The graph |

### Computation

```python
def resolve_coordinate(partial_coord: dict, G: nx.Graph) -> dict:
    """Fill null axes via constraint satisfaction."""
    specified = {b: v for b, v in partial_coord.items() if v is not None}
    specified_ids = [f"{b}.{v['x']}_{v['y']}" for b, v in specified.items()]
    unspecified = [b for b, v in partial_coord.items() if v is None]

    result = dict(specified)

    for branch in unspecified:
        candidates = []
        for x in range(10):
            for y in range(10):
                cid = f"{branch}.{x}_{y}"
                # Check EXCLUDES
                excluded = any(
                    G.has_edge(cid, sid) and G.edges[cid, sid].get('relation') == 'EXCLUDES'
                    for sid in specified_ids
                )
                if excluded:
                    continue

                # Score by COMPATIBLE_WITH + REQUIRES + potency
                compat_count = sum(
                    1 for sid in specified_ids
                    if G.has_edge(cid, sid) and G.edges[cid, sid].get('relation') == 'COMPATIBLE_WITH'
                )
                requires_count = sum(
                    1 for sid in specified_ids
                    if G.has_edge(sid, cid) and G.edges[sid, cid].get('relation') == 'REQUIRES'
                )
                p = potency(x, y)  # from Spec 02
                score = compat_count * 1.0 + requires_count * 2.0 + p * 0.5

                candidates.append((x, y, score))

        if not candidates:
            # No valid candidates — use center position as fallback
            candidates = [(5, 5, 0.0)]

        # Sort by score descending, tiebreak by potency
        candidates.sort(key=lambda c: (c[2], potency(c[0], c[1])), reverse=True)
        best_x, best_y, best_score = candidates[0]

        # Auto-fill weight
        max_score = max(c[2] for c in candidates) if candidates else 1.0
        pull_ratio = best_score / max(max_score, 1e-10)
        weight = 0.15 + (0.4 - 0.15) * pull_ratio

        result[branch] = {"x": best_x, "y": best_y, "weight": weight}
        specified_ids.append(f"{branch}.{best_x}_{best_y}")

    return result
```

### Output

| Return | Type | Description |
|---|---|---|
| coordinate | dict | Branch → {x, y, weight} — complete, all 10 axes filled |

### Edge Cases

- All axes specified: returns input unchanged (no CSP needed)
- No COMPATIBLE_WITH or REQUIRES edges to guide: potency alone determines selection → edge points preferred
- All candidates excluded: fallback to center position (5, 5) with minimum weight (0.15)

---

## 6. Potency-Weighted Tension

**Used by:** Tension Analyzer (Stage 5)

### Input

| Parameter | Type | Description |
|---|---|---|
| `active_constructs` | dict[str, list[dict]] | Branch → list of active constructs with potency |
| `G` | nx.Graph | The graph |

### Computation

```python
def compute_tensions(active_constructs: dict, G: nx.Graph) -> dict:
    """Compute all tensions: direct, spectrum, and cascading."""
    all_active = []
    for branch, constructs in active_constructs.items():
        for c in constructs:
            all_active.append(c)

    direct = []
    spectrum = []
    cascading = []

    # Direct tensions
    for i, a in enumerate(all_active):
        for b in all_active[i + 1:]:
            a_id = f"{a['branch']}.{a['x']}_{a['y']}"
            b_id = f"{b['branch']}.{b['x']}_{b['y']}"
            if G.has_edge(a_id, b_id):
                edge = G.edges[a_id, b_id]
                if edge.get('relation') == 'TENSIONS_WITH':
                    mag = edge.get('strength', 0.5) * a['potency'] * b['potency']
                    direct.append({
                        "between": [a_id, b_id],
                        "magnitude": mag,
                        "type": "declared",
                        "potency_product": a['potency'] * b['potency'],
                    })

    # Spectrum oppositions
    for c in all_active:
        c_id = f"{c['branch']}.{c['x']}_{c['y']}"
        if c['classification'] in ('corner', 'midpoint', 'edge'):
            for _, neighbor, data in G.edges(c_id, data=True):
                if data.get('relation') == 'SPECTRUM_OPPOSITION':
                    opp_potency = G.nodes[neighbor].get('potency', 0.5)
                    mag = 0.6 * c['potency'] * opp_potency
                    spectrum.append({
                        "active": c_id,
                        "opposite": neighbor,
                        "magnitude": mag,
                        "type": "spectrum_geometric",
                    })

    # Cascading tensions
    decay = compute_decay_factor(G)
    for c in all_active:
        c_id = f"{c['branch']}.{c['x']}_{c['y']}"
        cascade_tensions = propagate_tension(c_id, all_active, G, decay, max_hops=5)
        cascading.extend(cascade_tensions)

    total = (
        sum(t['magnitude'] for t in direct) +
        sum(t['magnitude'] for t in spectrum) +
        sum(t['magnitude'] for t in cascading)
    )

    return {
        "total_magnitude": total,
        "direct": direct,
        "spectrum": spectrum,
        "cascading": cascading,
    }

def compute_decay_factor(G: nx.Graph) -> float:
    """Derive decay from mean REQUIRES edge strength."""
    requires_strengths = [
        d.get('strength', 0.5)
        for _, _, d in G.edges(data=True)
        if d.get('relation') == 'REQUIRES'
    ]
    if not requires_strengths:
        return 0.7
    return float(np.mean(requires_strengths))

def propagate_tension(
    source_id: str, all_active: list, G: nx.Graph, decay: float, max_hops: int
) -> list:
    """Follow REQUIRES chains from source, check for tensions at each hop."""
    results = []
    active_ids = {f"{c['branch']}.{c['x']}_{c['y']}" for c in all_active}
    visited = {source_id}
    frontier = [(source_id, 0)]

    while frontier:
        current, hops = frontier.pop(0)
        if hops >= max_hops:
            continue
        for _, neighbor, data in G.edges(current, data=True):
            if data.get('relation') != 'REQUIRES' or neighbor in visited:
                continue
            visited.add(neighbor)
            # Check if this required node tensions with any active node
            for _, tension_target, td in G.edges(neighbor, data=True):
                if td.get('relation') == 'TENSIONS_WITH' and tension_target in active_ids:
                    mag = td.get('strength', 0.5) * (decay ** (hops + 1))
                    if mag >= 0.05:  # negligible threshold
                        results.append({
                            "between": [source_id, tension_target],
                            "magnitude": mag,
                            "type": "inferred_cascade",
                            "chain": [source_id, current, neighbor, tension_target],
                        })
            frontier.append((neighbor, hops + 1))

    return results
```

### Output

| Return | Type |
|---|---|
| tensions | dict with `total_magnitude`, `direct`, `spectrum`, `cascading` |

### Edge Cases

- No active edge constructs: spectrum list is empty
- No TENSIONS_WITH edges in graph: all tension lists empty, total = 0.0
- Decay factor with no REQUIRES edges: defaults to 0.7
- Cascade loop (A requires B, B requires A): `visited` set prevents infinite loops

---

## 7. Community Detection

**Used by:** Generative Analyzer (within Construct Resolver, Stage 4)

### Input

| Parameter | Type | Description |
|---|---|---|
| `subgraph` | nx.Graph | Subgraph induced by active constructs |

### Computation

```python
def detect_communities(subgraph: nx.Graph) -> list[set[str]]:
    """Run Louvain community detection on active construct subgraph."""
    if len(subgraph.nodes()) < 2:
        return [set(subgraph.nodes())]
    try:
        return list(nx.community.louvain_communities(subgraph, seed=42))
    except Exception:
        return [set(subgraph.nodes())]
```

### Output

| Return | Type | Description |
|---|---|---|
| communities | list[set[str]] | Each set is a community of node IDs |

### Edge Cases

- Single node: one community containing that node
- No edges in subgraph: each node is its own community
- `seed=42` for deterministic results

---

## 8. Centrality Analysis

**Used by:** Generative Analyzer, Coordinate Resolver (tiebreaker)

### Input

| Parameter | Type |
|---|---|
| `G` | nx.Graph |

### Computation

```python
def compute_centralities(G: nx.Graph) -> dict[str, dict[str, float]]:
    """Compute betweenness centrality and PageRank for all nodes."""
    betweenness = nx.betweenness_centrality(G)
    pagerank = nx.pagerank(G, alpha=0.85, max_iter=100)
    return {
        node: {
            "betweenness": betweenness.get(node, 0.0),
            "pagerank": pagerank.get(node, 0.0),
        }
        for node in G.nodes()
    }
```

### Output

| Return | Type |
|---|---|
| centralities | dict[str, {"betweenness": float, "pagerank": float}] |

### Edge Cases

- Disconnected graph: PageRank may not converge cleanly. `max_iter=100` with default tolerance handles this.
- Node with no edges: both centralities = 0.0

---

## 9. Transitive Closure

**Used by:** Tension Analyzer (REQUIRES chains), Coordinate Resolver

### Input

| Parameter | Type | Description |
|---|---|---|
| `G` | nx.Graph | The graph |
| `relation` | str | Edge type to compute closure over |

### Computation

```python
def transitive_closure_for_relation(G: nx.Graph, relation: str) -> nx.DiGraph:
    """Compute transitive closure for a specific relation type."""
    subgraph = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        if data.get('relation') == relation:
            subgraph.add_edge(u, v)
    return nx.transitive_closure(subgraph)
```

### Output

| Return | Type | Description |
|---|---|---|
| closure | nx.DiGraph | Graph where (A, C) exists if A→B→...→C via the relation |

### Edge Cases

- No edges of the given relation: returns empty graph
- Self-loops: possible in transitive closure if cycles exist in REQUIRES chains

---

## 10. Gem Magnitude

**Used by:** Nexus/Gem Analyzer (Stage 6)

### Input

| Parameter | Type | Description |
|---|---|---|
| `source_branch` | str | The source branch |
| `target_branch` | str | The target branch |
| `active_constructs` | dict | Branch → list of active constructs |
| `G` | nx.Graph | The graph |

### Computation

The gem magnitude integrates edge-point energies from both branches, weighted by which constructs are active:

```python
def compute_gem(source_branch: str, target_branch: str,
                active_constructs: dict, G: nx.Graph) -> dict:
    """Compute gem for one directional nexus."""

    source_edge_constructs = [
        c for c in get_all_constructs(G, source_branch)
        if c['classification'] in ('corner', 'midpoint', 'edge')
    ]
    target_edge_constructs = [
        c for c in get_all_constructs(G, target_branch)
        if c['classification'] in ('corner', 'midpoint', 'edge')
    ]

    source_active = {
        f"{c['branch']}.{c['x']}_{c['y']}"
        for c in active_constructs.get(source_branch, [])
    }
    target_active = {
        f"{c['branch']}.{c['x']}_{c['y']}"
        for c in active_constructs.get(target_branch, [])
    }

    # Sum potencies of active edge constructs from both branches
    source_energy = sum(
        c['potency'] * (2.0 if c['id'] in source_active else 1.0)
        for c in source_edge_constructs
    )
    target_energy = sum(
        c['potency'] * (2.0 if c['id'] in target_active else 1.0)
        for c in target_edge_constructs
    )

    # Normalize by maximum possible energy (all edge constructs at 2x)
    max_source = sum(c['potency'] * 2.0 for c in source_edge_constructs)
    max_target = sum(c['potency'] * 2.0 for c in target_edge_constructs)

    source_ratio = source_energy / max(max_source, 1e-10)
    target_ratio = target_energy / max(max_target, 1e-10)

    # Gem magnitude is the harmonic mean of both ratios
    if source_ratio + target_ratio == 0:
        magnitude = 0.0
    else:
        magnitude = 2 * source_ratio * target_ratio / (source_ratio + target_ratio)

    # Determine harmony vs conflict
    # Check if there are more tensions or compatibilities between the two branches' active constructs
    tension_count = 0
    compat_count = 0
    for sc in active_constructs.get(source_branch, []):
        s_id = f"{sc['branch']}.{sc['x']}_{sc['y']}"
        for tc in active_constructs.get(target_branch, []):
            t_id = f"{tc['branch']}.{tc['x']}_{tc['y']}"
            if G.has_edge(s_id, t_id):
                rel = G.edges[s_id, t_id].get('relation')
                if rel == 'TENSIONS_WITH':
                    tension_count += 1
                elif rel == 'COMPATIBLE_WITH':
                    compat_count += 1

    harmony_type = "harmonious" if compat_count >= tension_count else "conflicting"

    return {
        "nexus": f"nexus.{source_branch}.{target_branch}",
        "magnitude": magnitude,
        "type": harmony_type,
        "source_energy": source_ratio,
        "target_energy": target_ratio,
    }
```

### Output

| Return | Type |
|---|---|
| gem | dict with `nexus`, `magnitude`, `type`, `source_energy`, `target_energy` |

### Design Notes

- Active edge constructs contribute 2x their potency (they are "lit up" by the coordinate)
- Inactive edge constructs still contribute 1x (they exist structurally)
- Harmonic mean ensures both branches must contribute for high magnitude — one-sided energy produces a low gem
- Harmony type is determined by the ratio of declared tensions to compatibilities between active constructs across the two branches

### Edge Cases

- No active constructs in one branch: that branch contributes only baseline energy → low gem
- No declared edges between branches: harmony defaults to "harmonious" (no evidence of conflict)

---

## 11. Spoke Shape

**Used by:** Spoke Analyzer (Stage 7)

### Input

| Parameter | Type | Description |
|---|---|---|
| `gems` | list[dict] | The 9 gems for one spoke |

### Computation

```python
def compute_spoke_shape(gems: list[dict]) -> dict:
    """Compute the 4 spoke properties from gem magnitudes."""
    # Handle empty gem list (inactive branch — no nexi computed)
    if len(gems) == 0:
        return {
            "strength": 0.0,
            "consistency": 1.0,
            "polarity": 0.0,
            "gems": [],
        }

    magnitudes = np.array([g['magnitude'] for g in gems])

    strength = float(np.mean(magnitudes))

    std = float(np.std(magnitudes))
    consistency = 1.0 - (std / max(strength, 1e-10))
    consistency = max(0.0, min(1.0, consistency))  # clamp to [0, 1]

    tension_count = sum(1 for g in gems if g['type'] == 'conflicting')
    polarity = tension_count / max(len(gems), 1)

    return {
        "strength": strength,
        "consistency": consistency,
        "polarity": polarity,
        "gems": gems,
    }
```

**Contribution** is computed after all spokes are calculated:

```python
def compute_contributions(spokes: dict[str, dict]) -> dict[str, dict]:
    """Add contribution property to each spoke."""
    total_strength = sum(s['strength'] for s in spokes.values())
    for branch, spoke in spokes.items():
        spoke['contribution'] = spoke['strength'] / max(total_strength, 1e-10)
    return spokes
```

**Classification:**

```python
# Calibrated for a 10-branch system. See Spec 08 for rationale.
SPOKE_THRESHOLDS = {
    "high_strength": 0.5,
    "high_consistency": 0.65,
    "high_contribution": 0.15,  # > 1/10 = disproportionate
    "low_strength": 0.25,
}

def classify_spoke(spoke: dict) -> str:
    s = spoke['strength']
    c = spoke['consistency']
    p = spoke['contribution']

    if s < SPOKE_THRESHOLDS['low_strength']:
        return "weakly_integrated"
    if s >= SPOKE_THRESHOLDS['high_strength'] and c >= SPOKE_THRESHOLDS['high_consistency']:
        return "coherent"
    if s >= SPOKE_THRESHOLDS['high_strength'] and p >= SPOKE_THRESHOLDS['high_contribution']:
        return "dominant"
    if s >= SPOKE_THRESHOLDS['high_strength'] and c < SPOKE_THRESHOLDS['high_consistency']:
        return "fragmented"
    return "moderate"
```

### Output

| Return | Type |
|---|---|
| spoke | dict with `strength`, `consistency`, `polarity`, `contribution`, `classification`, `gems` |

### Edge Cases

- All gems have magnitude 0: strength = 0, consistency = 1.0 (no variance), classification = "weakly_integrated"
- Single non-zero gem: consistency will be low (high relative std), classification = "fragmented"

---

## 12. Central Gem Coherence

**Used by:** Spoke Analyzer (Stage 7)

### Input

| Parameter | Type |
|---|---|
| `spokes` | dict[str, dict] — all 10 spoke profiles |

### Computation

```python
def compute_central_gem(spokes: dict[str, dict]) -> dict:
    """Aggregate all spoke contributions into central gem coherence."""
    contributions = [s['contribution'] for s in spokes.values()]
    consistencies = [s['consistency'] for s in spokes.values()]

    # Coherence = weighted mean of contributions weighted by consistency
    # High-consistency spokes count more toward coherence
    weighted_sum = sum(c * w for c, w in zip(contributions, consistencies))
    weight_total = sum(consistencies)

    coherence = weighted_sum / max(weight_total, 1e-10)

    return {
        "coherence": coherence,
        "classification": classify_coherence(coherence),
    }

def classify_coherence(coherence: float) -> str:
    # Thresholds are deliberately low — the coherence formula produces small
    # values. With 10 spokes each contributing ~0.1, weighted by consistency,
    # maximum coherence is ~0.1. See Spec 08 for calibration rationale.
    if coherence >= 0.08:
        return "highly_coherent"
    if coherence >= 0.05:
        return "moderately_coherent"
    if coherence >= 0.02:
        return "weakly_coherent"
    return "incoherent"
```

### Output

| Return | Type |
|---|---|
| central_gem | dict with `coherence` (float) and `classification` (str) |

### Edge Cases

- All spokes weakly integrated: coherence near 0 → "incoherent"
- One dominant spoke with high consistency: coherence may be moderate despite imbalance
- All spokes equally strong and consistent: coherence is high → "highly_coherent"

---

## 13. Pareto Optimization

**Used by:** Multi-Pass Orchestrator (stress_test)

### Input

| Parameter | Type | Description |
|---|---|---|
| `results` | list[dict] | Pipeline results for each perturbation |

### Computation

```python
def pareto_front(results: list[dict]) -> list[dict]:
    """Find Pareto-optimal results (minimize tension, maximize generative)."""
    front = []
    for r in results:
        dominated = False
        for other in results:
            if (other['tension'] <= r['tension'] and
                other['generative'] >= r['generative'] and
                (other['tension'] < r['tension'] or other['generative'] > r['generative'])):
                dominated = True
                break
        if not dominated:
            front.append(r)
    return front
```

### Output

| Return | Type |
|---|---|
| front | list[dict] — non-dominated results |

### Edge Cases

- All results identical: all are on the front
- Single result: it is the front
- O(n²) complexity — acceptable for ~100 perturbations
