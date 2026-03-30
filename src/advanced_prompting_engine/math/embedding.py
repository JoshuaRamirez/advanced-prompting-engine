"""Spectral embedding via graph Laplacian eigendecomposition — numpy only.

Authoritative source: Spec 05 §3.
"""

from __future__ import annotations

import networkx as nx
import numpy as np


def compute_spectral_embedding(G: nx.Graph, k: int = 20) -> dict[str, np.ndarray]:
    """Compute spectral embedding for all nodes.

    Uses the graph Laplacian eigendecomposition.
    Returns dict mapping node_id → k-dimensional vector.
    """
    n = len(G.nodes())
    if n < 2:
        return {node: np.zeros(0) for node in G.nodes()}

    k = min(k, n - 1)

    # Symmetrize for spectral methods — directed edges become undirected
    A = nx.to_numpy_array(G.to_undirected())
    D = np.diag(A.sum(axis=1))
    L = D - A

    eigenvalues, eigenvectors = np.linalg.eigh(L)

    # Skip trivial eigenvector (index 0, eigenvalue ≈ 0)
    embedding_matrix = eigenvectors[:, 1 : k + 1]

    nodes = list(G.nodes())
    return {nodes[i]: embedding_matrix[i] for i in range(n)}
