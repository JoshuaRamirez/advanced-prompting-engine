"""TF-IDF vector cache — lifecycle-managed.

Authoritative source: CONSTRUCT-v2.md §14.
Vectors built from construct question text + tags.
Query projects intent into the same space; cosine similarity determines matches.

Supports both global queries (all 1728 constructs) and per-face queries
(144 constructs within one face). Per-face matching eliminates cross-face
homogeneity that causes all faces to match the same position.
"""

from __future__ import annotations

import networkx as nx
import numpy as np

from advanced_prompting_engine.cache.hashing import compute_tfidf_hash
from advanced_prompting_engine.math.tfidf import build_tfidf_matrix, vectorize_query


class TfidfCache:
    """Lifecycle-managed cache for TF-IDF vectors of construct questions."""

    def __init__(self):
        # Global matrix (all constructs)
        self._matrix: np.ndarray | None = None
        self._vocab: list[str] = []
        self._doc_ids: list[str] = []
        # Per-face matrices (144 constructs each)
        self._face_matrices: dict[str, np.ndarray] = {}
        self._face_vocabs: dict[str, list[str]] = {}
        self._face_doc_ids: dict[str, list[str]] = {}
        self._content_hash: str = ""

    def initialize(self, G: nx.Graph):
        constructs = [
            (n, G.nodes[n])
            for n in G.nodes()
            if G.nodes[n].get("type") == "construct"
        ]

        # Global matrix
        documents = [
            f"{data.get('question', '')} {' '.join(data.get('tags', []))}"
            for _, data in constructs
        ]
        self._doc_ids = [node_id for node_id, _ in constructs]
        self._matrix, self._vocab = build_tfidf_matrix(documents)

        # Per-face matrices
        self._face_matrices = {}
        self._face_vocabs = {}
        self._face_doc_ids = {}

        face_groups: dict[str, list[tuple[str, dict]]] = {}
        for node_id, data in constructs:
            face = data.get("face", "")
            if face not in face_groups:
                face_groups[face] = []
            face_groups[face].append((node_id, data))

        for face, face_constructs in face_groups.items():
            face_docs = [
                f"{data.get('question', '')} {' '.join(data.get('tags', []))}"
                for _, data in face_constructs
            ]
            face_ids = [nid for nid, _ in face_constructs]
            matrix, vocab = build_tfidf_matrix(face_docs)
            self._face_matrices[face] = matrix
            self._face_vocabs[face] = vocab
            self._face_doc_ids[face] = face_ids

        self._content_hash = compute_tfidf_hash(G)

    def validate(self, G: nx.Graph) -> bool:
        return compute_tfidf_hash(G) == self._content_hash

    def invalidate(self):
        self._matrix = None
        self._vocab = []
        self._doc_ids = []
        self._face_matrices = {}
        self._face_vocabs = {}
        self._face_doc_ids = {}
        self._content_hash = ""

    def ensure_valid(self, G: nx.Graph):
        if not self._content_hash or not self.validate(G):
            self.initialize(G)

    def query(self, intent: str) -> list[tuple[str, float]]:
        """Return (construct_id, similarity) pairs sorted by similarity descending.

        Global query across all 1728 constructs.
        """
        if self._matrix is None or len(self._doc_ids) == 0:
            return []
        query_vec = vectorize_query(intent, self._vocab)
        similarities = self._matrix @ query_vec
        results = list(zip(self._doc_ids, similarities.tolist()))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def query_face(self, intent: str, face: str) -> list[tuple[str, float]]:
        """Return (construct_id, similarity) pairs within ONE face only.

        Uses a face-specific TF-IDF matrix where IDF is computed from only
        that face's 144 constructs. This eliminates cross-face homogeneity —
        words that are common across all faces (structural template words)
        get low IDF within each face, while face-differentiating words
        get high IDF.
        """
        if face not in self._face_matrices:
            return []
        matrix = self._face_matrices[face]
        vocab = self._face_vocabs[face]
        doc_ids = self._face_doc_ids[face]
        if matrix is None or len(doc_ids) == 0:
            return []
        query_vec = vectorize_query(intent, vocab)
        similarities = matrix @ query_vec
        results = list(zip(doc_ids, similarities.tolist()))
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def similarity(self, text_a: str, text_b: str) -> float:
        """Compute similarity between two arbitrary texts in the global cache's space."""
        if not self._vocab:
            return 0.0
        vec_a = vectorize_query(text_a, self._vocab)
        vec_b = vectorize_query(text_b, self._vocab)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))

    @property
    def is_initialized(self) -> bool:
        return bool(self._content_hash)
