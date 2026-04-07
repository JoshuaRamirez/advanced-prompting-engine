#!/usr/bin/env python3
"""Build the semantic bridge artifacts from GloVe word vectors.

This script runs on the DEVELOPER machine at build time — never at runtime.
It downloads GloVe 6B 50d vectors (~70MB) if not already cached, builds a
face centroid for each of the 12 Construct domains, computes cosine similarity
between the top ~8000 most common words and each centroid, and saves the
results as two artifacts that ship with the wheel:

  src/advanced_prompting_engine/data/semantic_bridge.npz
  src/advanced_prompting_engine/data/semantic_vocab.json

Usage:
    python3 scripts/build_semantic_bridge.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Ensure the project source is importable
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from advanced_prompting_engine.graph.schema import (
    ALL_FACES,
    DOMAIN_REPLACEMENTS,
    FACE_DEFINITIONS,
)
from advanced_prompting_engine.graph.canonical import BASE_QUESTIONS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GLOVE_URL = "https://nlp.stanford.edu/data/glove.6B.zip"
GLOVE_CACHE_DIR = Path.home() / ".cache" / "glove"
GLOVE_ZIP_PATH = GLOVE_CACHE_DIR / "glove.6B.zip"
GLOVE_TXT_PATH = GLOVE_CACHE_DIR / "glove.6B.50d.txt"
VECTOR_DIM = 50
TOP_K_WORDS = 8000  # GloVe is sorted by frequency; take top 8000

OUTPUT_DIR = PROJECT_ROOT / "src" / "advanced_prompting_engine" / "data"
NPZ_PATH = OUTPUT_DIR / "semantic_bridge.npz"
VOCAB_PATH = OUTPUT_DIR / "semantic_vocab.json"


# ---------------------------------------------------------------------------
# GloVe download and loading
# ---------------------------------------------------------------------------

def download_glove() -> None:
    """Download GloVe 6B zip if not already cached."""
    if GLOVE_TXT_PATH.exists():
        print(f"[OK] GloVe vectors already cached at {GLOVE_TXT_PATH}")
        return

    GLOVE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if not GLOVE_ZIP_PATH.exists():
        print(f"[DOWNLOAD] Fetching GloVe 6B from {GLOVE_URL} ...")
        print(f"           Destination: {GLOVE_ZIP_PATH}")
        print(f"           This is ~862MB — please wait.")
        urllib.request.urlretrieve(GLOVE_URL, str(GLOVE_ZIP_PATH))
        print(f"[OK] Download complete.")
    else:
        print(f"[OK] GloVe zip already cached at {GLOVE_ZIP_PATH}")

    print(f"[EXTRACT] Extracting glove.6B.50d.txt from zip ...")
    with zipfile.ZipFile(str(GLOVE_ZIP_PATH), "r") as zf:
        # Extract only the 50d file
        target_name = "glove.6B.50d.txt"
        zf.extract(target_name, str(GLOVE_CACHE_DIR))
    print(f"[OK] Extracted to {GLOVE_TXT_PATH}")


def load_glove(max_words: int = TOP_K_WORDS) -> tuple[dict[str, int], np.ndarray]:
    """Load the top max_words GloVe vectors.

    Returns:
        vocab: word -> index mapping
        vectors: shape (max_words, VECTOR_DIM)
    """
    print(f"[LOAD] Reading top {max_words} GloVe vectors ...")
    vocab: dict[str, int] = {}
    vectors: list[np.ndarray] = []

    with open(str(GLOVE_TXT_PATH), "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= max_words:
                break
            parts = line.rstrip().split(" ")
            word = parts[0]
            vec = np.array([float(x) for x in parts[1:]], dtype=np.float32)
            if vec.shape[0] != VECTOR_DIM:
                continue
            vocab[word] = len(vectors)
            vectors.append(vec)

    matrix = np.stack(vectors)  # shape (n_words, 50)
    print(f"[OK] Loaded {len(vocab)} words, matrix shape {matrix.shape}")
    return vocab, matrix


# ---------------------------------------------------------------------------
# Face centroid construction
# ---------------------------------------------------------------------------

def _tokenize_text(text: str) -> list[str]:
    """Simple whitespace tokenizer with punctuation removal, lowercased."""
    cleaned = text.lower()
    for ch in "?.,;:!'\"()[]{}—-–/":
        cleaned = cleaned.replace(ch, " ")
    return [w for w in cleaned.split() if len(w) > 1]


def _text_to_vector(words: list[str], vocab: dict[str, int], vectors: np.ndarray) -> np.ndarray:
    """Average the GloVe vectors for all words found in vocab."""
    indices = [vocab[w] for w in words if w in vocab]
    if not indices:
        return np.zeros(VECTOR_DIM, dtype=np.float32)
    return np.mean(vectors[indices], axis=0)


def build_face_centroids(vocab: dict[str, int], vectors: np.ndarray) -> np.ndarray:
    """Build a centroid vector for each of the 12 faces.

    Sources per face:
      - Core question words
      - Construction template words
      - Sub-dimension labels (x_axis_low, x_axis_high, y_axis_low, y_axis_high)
      - Domain replacement string words
      - All 144 construction questions (BASE_QUESTIONS parameterized with
        DOMAIN_REPLACEMENTS for this face)

    Returns: shape (12, VECTOR_DIM)
    """
    centroids = []

    for face in ALL_FACES:
        defn = FACE_DEFINITIONS[face]
        all_words: list[str] = []

        # Core question
        all_words.extend(_tokenize_text(defn["core_question"]))

        # Construction template
        all_words.extend(_tokenize_text(defn["construction_template"]))

        # Sub-dimension labels
        for key in ("x_axis_low", "x_axis_high", "y_axis_low", "y_axis_high"):
            all_words.extend(_tokenize_text(defn[key]))

        # Domain replacement string
        all_words.extend(_tokenize_text(DOMAIN_REPLACEMENTS[face]))

        # All 144 parameterized construction questions for this face
        domain_str = DOMAIN_REPLACEMENTS[face]
        for (_x, _y), template in BASE_QUESTIONS.items():
            question = template.replace("{domain}", domain_str)
            all_words.extend(_tokenize_text(question))

        centroid = _text_to_vector(all_words, vocab, vectors)

        # Normalize to unit length for cosine similarity
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm

        centroids.append(centroid)
        print(f"  {face:15s}: {len(all_words)} source words, "
              f"{sum(1 for w in all_words if w in vocab)} in GloVe vocab")

    return np.stack(centroids)  # shape (12, 50)


# ---------------------------------------------------------------------------
# Similarity matrix computation
# ---------------------------------------------------------------------------

def compute_similarity_matrix(
    vocab: dict[str, int],
    vectors: np.ndarray,
    centroids: np.ndarray,
) -> np.ndarray:
    """Compute cosine similarity between every vocab word and each face centroid.

    Returns: shape (vocab_size, 12)
    """
    print(f"[COMPUTE] Building similarity matrix ({len(vocab)} x {len(ALL_FACES)}) ...")

    # Normalize all word vectors to unit length
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    normed_vectors = vectors / norms  # shape (vocab_size, 50)

    # centroids are already unit-normalized
    # Cosine similarity = dot product of unit vectors
    similarity = normed_vectors @ centroids.T  # shape (vocab_size, 12)

    print(f"[OK] Similarity matrix shape: {similarity.shape}")
    return similarity


# ---------------------------------------------------------------------------
# Output and reporting
# ---------------------------------------------------------------------------

def save_artifacts(
    vocab: dict[str, int],
    similarity: np.ndarray,
) -> None:
    """Save the similarity matrix and vocabulary to disk."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        str(NPZ_PATH),
        matrix=similarity.astype(np.float32),
        faces=np.array(ALL_FACES),
    )
    print(f"[SAVE] {NPZ_PATH} ({NPZ_PATH.stat().st_size / 1024:.1f} KB)")

    with open(str(VOCAB_PATH), "w", encoding="utf-8") as f:
        json.dump(vocab, f)
    print(f"[SAVE] {VOCAB_PATH} ({VOCAB_PATH.stat().st_size / 1024:.1f} KB)")


def report_top_words(
    vocab: dict[str, int],
    similarity: np.ndarray,
    top_n: int = 20,
) -> None:
    """Print the top-N most similar words per face for sanity checking."""
    idx_to_word = {i: w for w, i in vocab.items()}

    print(f"\n{'='*70}")
    print(f"Top {top_n} words per face (sanity check)")
    print(f"{'='*70}")

    for col_idx, face in enumerate(ALL_FACES):
        scores = similarity[:, col_idx]
        top_indices = np.argsort(scores)[::-1][:top_n]
        top_words = [(idx_to_word[i], float(scores[i])) for i in top_indices]
        words_str = ", ".join(f"{w}({s:.3f})" for w, s in top_words)
        print(f"\n{face}:")
        print(f"  {words_str}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print("Semantic Bridge Builder")
    print("=" * 70)

    # Step 1: Download GloVe
    download_glove()

    # Step 2: Load GloVe vectors
    vocab, vectors = load_glove(TOP_K_WORDS)

    # Step 3: Build face centroids
    print(f"\n[BUILD] Computing face centroids ...")
    centroids = build_face_centroids(vocab, vectors)

    # Step 4: Compute similarity matrix
    similarity = compute_similarity_matrix(vocab, vectors, centroids)

    # Step 5: Save artifacts
    save_artifacts(vocab, similarity)

    # Step 6: Report
    report_top_words(vocab, similarity)

    print(f"\n{'='*70}")
    print(f"Vocabulary size: {len(vocab)}")
    print(f"Matrix shape:    {similarity.shape}")
    print(f"Artifacts:       {NPZ_PATH}")
    print(f"                 {VOCAB_PATH}")
    print(f"{'='*70}")
    print("[DONE]")


if __name__ == "__main__":
    main()
