# Spec 09 — Caching Lifecycle

## Purpose

Defines the two lifecycle-managed caches (spectral embedding and TF-IDF), their computation triggers, invalidation conditions, and query interfaces.

---

## Shared Lifecycle Protocol

Both caches follow the same lifecycle:

```
1. INITIALIZE  — compute on first startup
2. VALIDATE    — check graph hash before each pipeline run
3. INVALIDATE  — clear if graph has changed
4. RECOMPUTE   — rebuild from current graph state
5. SERVE       — return cached values during pipeline execution
```

---

## Graph Hash

Both caches use the same hash to detect graph mutations:

```python
import hashlib

def compute_graph_hash(G: nx.Graph) -> str:
    """Deterministic hash of graph structure."""
    node_part = str(sorted(G.nodes()))
    edge_part = str(sorted((u, v, d.get('relation', '')) for u, v, d in G.edges(data=True)))
    combined = f"{len(G.nodes())}:{len(G.edges())}:{node_part}:{edge_part}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]
```

The hash changes if:
- A node is added or removed
- An edge is added or removed
- An edge's relation type changes

The hash does NOT change if:
- Edge strengths change (properties other than relation)
- Node descriptions or tags change

This is intentional: structural changes invalidate, property changes do not (because embeddings depend on topology, not labels).

**Exception:** The TF-IDF cache depends on node labels (questions, tags). A separate hash for TF-IDF accounts for label changes:

```python
def compute_tfidf_hash(G: nx.Graph) -> str:
    """Hash that includes node content."""
    content = sorted(
        f"{n}:{G.nodes[n].get('question', '')}:{G.nodes[n].get('tags', '')}"
        for n in G.nodes() if G.nodes[n].get('type') == 'construct'
    )
    return hashlib.sha256(str(content).encode()).hexdigest()[:16]
```

---

## Embedding Cache

### Computation

From Spec 05, Section 3: Laplacian eigendecomposition of the full graph.

```python
class EmbeddingCache:
    def __init__(self):
        self._embeddings: dict[str, np.ndarray] = {}
        self._graph_hash: str = ""

    def initialize(self, G: nx.Graph):
        self._embeddings = compute_spectral_embedding(G)
        self._graph_hash = compute_graph_hash(G)

    def validate(self, G: nx.Graph) -> bool:
        return compute_graph_hash(G) == self._graph_hash

    def invalidate(self):
        self._embeddings = {}
        self._graph_hash = ""

    def ensure_valid(self, G: nx.Graph):
        if not self.validate(G):
            self.initialize(G)

    def get(self, node_id: str) -> np.ndarray:
        if node_id not in self._embeddings:
            raise EmbeddingMissing(node_id)
        return self._embeddings[node_id]

    def all_embeddings(self) -> dict[str, np.ndarray]:
        return self._embeddings
```

### Startup

```
1. Load graph from SQLite
2. Compute embedding cache (calls initialize)
3. ~50ms for 1101 nodes
```

### Invalidation Trigger

Any call to `GraphMutationLayer.add_construct()` or `GraphMutationLayer.add_relation()` calls `embedding_cache.invalidate()`.

The next pipeline run calls `ensure_valid()` which recomputes.

---

## TF-IDF Cache

### Computation

From Spec 05, Sections 1-2: TF-IDF vectorization of all 1000 construct questions.

```python
class TfidfCache:
    def __init__(self):
        self._matrix: np.ndarray | None = None  # (n_docs, vocab_size)
        self._vocab: list[str] = []
        self._doc_ids: list[str] = []             # parallel to matrix rows
        self._content_hash: str = ""

    def initialize(self, G: nx.Graph):
        constructs = [
            (n, G.nodes[n])
            for n in G.nodes()
            if G.nodes[n].get('type') == 'construct'
        ]
        documents = [
            f"{data.get('question', '')} {' '.join(data.get('tags', []))}"
            for _, data in constructs
        ]
        self._doc_ids = [node_id for node_id, _ in constructs]
        self._matrix, self._vocab = build_tfidf_matrix(documents)
        self._content_hash = compute_tfidf_hash(G)

    def validate(self, G: nx.Graph) -> bool:
        return compute_tfidf_hash(G) == self._content_hash

    def invalidate(self):
        self._matrix = None
        self._vocab = []
        self._doc_ids = []
        self._content_hash = ""

    def ensure_valid(self, G: nx.Graph):
        if not self.validate(G):
            self.initialize(G)

    def query(self, intent: str) -> list[tuple[str, float]]:
        """Return (construct_id, similarity) pairs sorted by similarity."""
        query_vec = vectorize_query(intent, self._vocab)
        similarities = self._matrix @ query_vec  # dot product (matrix is pre-normalized)
        results = list(zip(self._doc_ids, similarities.tolist()))
        results.sort(key=lambda x: x[1], reverse=True)
        return results
```

### Startup

```
1. Load graph from SQLite
2. Compute TF-IDF cache (calls initialize)
3. ~30ms for 1000 construct questions
```

### Invalidation Trigger

Same as embedding cache: any graph mutation invalidates. TF-IDF additionally invalidates on content changes (question or tag edits), detected via the separate content hash.

---

## Startup Sequence

```
1. Open/create SQLite database
2. Load or initialize canonical data
3. Load user data
4. Build NetworkX graph from all data
5. Initialize embedding cache    ← ~50ms
6. Initialize TF-IDF cache      ← ~30ms
7. Compute centrality cache      ← ~20ms (betweenness + PageRank, cached similarly)
8. Server ready for MCP connections
```

Total cold startup: ~100ms. Subsequent startups with unchanged graph: hash validation is instant, no recomputation needed (caches could be persisted to disk as an optimization, but in-memory recomputation at 100ms is acceptable).

---

## Centrality Cache

An additional cache for pre-computed centrality measures, following the same lifecycle:

```python
class CentralityCache:
    def __init__(self):
        self._centralities: dict[str, dict[str, float]] = {}
        self._graph_hash: str = ""

    def initialize(self, G: nx.Graph):
        self._centralities = compute_centralities(G)
        self._graph_hash = compute_graph_hash(G)

    # ... same validate/invalidate/ensure_valid pattern
```

Used by: Coordinate Resolver (tiebreaker), Generative Analyzer (structural leverage).
