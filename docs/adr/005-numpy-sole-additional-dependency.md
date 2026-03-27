# ADR-005: numpy as Sole Additional Dependency (No scipy, No scikit-learn)

**Date**: 2026-03-27
**Status**: Accepted

## Context

The engine's mathematical operations require linear algebra capabilities not present in Python stdlib:
- Spectral embedding (eigendecomposition of graph Laplacian)
- Vector distance computation (norms, dot products)
- TF-IDF vectorization (term frequency, cosine similarity)

The natural Python libraries for these operations are:
- **numpy**: array operations, linear algebra
- **scipy**: sparse matrices, advanced decompositions
- **scikit-learn**: TF-IDF vectorizer, cosine similarity utilities

Each additional dependency increases install size, activation time, and potential for version conflicts.

## Decision

Use **numpy only**. Implement all operations without scipy or scikit-learn.

Specific implementations:
| Operation | Typical dependency | numpy-only approach |
|---|---|---|
| Laplacian matrix | `nx.laplacian_matrix` → scipy sparse | `A = nx.to_numpy_array(G)` → `L = np.diag(A.sum(1)) - A` |
| Eigendecomposition | scipy.linalg.eigh | `np.linalg.eigh(L)` |
| TF-IDF | sklearn.TfidfVectorizer | ~50 lines of Python + numpy |
| Cosine similarity | sklearn.metrics.pairwise | `np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))` |

## Rationale

- numpy is near-universal in Python — virtually every scientific Python installation has it
- scipy adds ~150MB to install size with no operation that numpy cannot handle at our expected scale (~500 nodes)
- scikit-learn adds ~100MB and is massive overkill for TF-IDF which is ~50 lines of code
- Fewer dependencies = faster `uvx` activation, fewer version conflicts, smaller attack surface
- At expected graph scale (500-5000 nodes), numpy's dense matrix operations are efficient. Sparse matrices (scipy) would only matter at 50,000+ nodes.

## Consequences

- **Positive**: Total installable dependencies: networkx + numpy + mcp — minimal footprint
- **Positive**: No scikit-learn version conflicts (a common source of dependency hell)
- **Positive**: TF-IDF implementation is fully visible and auditable (not hidden behind sklearn)
- **Negative**: Must maintain ~50 lines of TF-IDF code instead of calling sklearn
- **Negative**: If graph scale exceeds ~5000 nodes, dense matrix eigendecomposition (numpy) becomes slow. Would need to reconsider scipy sparse at that point.
- **Trade-off**: Custom code vs. dependency weight. At this scale, custom code wins.
