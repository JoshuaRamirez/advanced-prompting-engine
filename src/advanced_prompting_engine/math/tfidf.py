"""TF-IDF vectorization and cosine similarity — numpy only, no sklearn.

Authoritative source: Spec 05 §1-2.
"""

from __future__ import annotations

import numpy as np


def build_tfidf_matrix(documents: list[str]) -> tuple[np.ndarray, list[str]]:
    """Build normalized TF-IDF matrix for all documents.

    Returns (matrix of shape (n_docs, vocab_size), vocabulary list).
    """
    tokenized = [doc.lower().split() for doc in documents]

    vocab = sorted(set(word for doc in tokenized for word in doc))
    word_to_idx = {w: i for i, w in enumerate(vocab)}

    n_docs = len(documents)
    vocab_size = len(vocab)

    if n_docs == 0 or vocab_size == 0:
        return np.zeros((n_docs, 0)), vocab

    # Term frequency
    tf = np.zeros((n_docs, vocab_size))
    for i, doc in enumerate(tokenized):
        for word in doc:
            tf[i, word_to_idx[word]] += 1
        if len(doc) > 0:
            tf[i] /= len(doc)

    # Inverse document frequency (smoothed)
    df = np.sum(tf > 0, axis=0)
    idf = np.log((n_docs + 1) / (df + 1)) + 1

    # TF-IDF
    tfidf = tf * idf

    # Normalize rows to unit length
    norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
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


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors. Returns 0.0 for zero vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
