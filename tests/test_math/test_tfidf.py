"""Tests for TF-IDF vectorization and cosine similarity."""

import numpy as np
from advanced_prompting_engine.math.tfidf import build_tfidf_matrix, cosine_similarity, vectorize_query


def test_empty_documents():
    matrix, vocab = build_tfidf_matrix([])
    assert matrix.shape == (0, 0)
    assert vocab == []


def test_basic_tfidf():
    docs = ["the cat sat", "the dog sat", "the bird flew"]
    matrix, vocab = build_tfidf_matrix(docs)
    assert matrix.shape[0] == 3
    assert matrix.shape[1] == len(vocab)
    assert "cat" in vocab
    assert "dog" in vocab


def test_rows_normalized():
    docs = ["alpha beta gamma", "delta epsilon"]
    matrix, vocab = build_tfidf_matrix(docs)
    for i in range(matrix.shape[0]):
        norm = np.linalg.norm(matrix[i])
        assert abs(norm - 1.0) < 1e-6 or norm == 0.0


def test_query_vectorization():
    docs = ["hello world", "foo bar"]
    matrix, vocab = build_tfidf_matrix(docs)
    vec = vectorize_query("hello", vocab)
    assert vec.shape == (len(vocab),)
    norm = np.linalg.norm(vec)
    assert norm > 0


def test_empty_query():
    docs = ["hello world"]
    matrix, vocab = build_tfidf_matrix(docs)
    vec = vectorize_query("", vocab)
    assert np.all(vec == 0)


def test_query_no_overlap():
    docs = ["alpha beta"]
    matrix, vocab = build_tfidf_matrix(docs)
    vec = vectorize_query("zzz xxx", vocab)
    assert np.all(vec == 0)


def test_cosine_zero_vectors():
    assert cosine_similarity(np.zeros(5), np.zeros(5)) == 0.0


def test_cosine_identical():
    v = np.array([1.0, 2.0, 3.0])
    assert abs(cosine_similarity(v, v) - 1.0) < 1e-6


def test_cosine_orthogonal():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    assert abs(cosine_similarity(a, b)) < 1e-6
