#!/usr/bin/env python3
"""Build the geometric semantic bridge artifacts from GloVe word vectors.

This script runs on the DEVELOPER machine at build time — never at runtime.
It downloads GloVe 6B 50d vectors (~70MB), loads ALL 400K vectors, selects a
~16K runtime vocabulary (top 15K frequent + face/domain/axis/pole words), builds
12 face centroids from AUTHORED LAYERS ONLY (core questions, sub-dimension labels,
domain replacement strings, face names — NOT the 144 derived question templates),
builds 24 axis direction vectors (high_pole - low_pole), calibrates projections,
and pre-computes per-word artifacts:

  - Discriminative face similarity: cosine(word, centroid) - mean → (16K, 12)
  - Axis projections: dot(word, direction_unit) normalized by calibration → (16K, 24)
  - IDF weights from frequency rank → (16K,)

Artifacts saved:
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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GLOVE_URL = "https://nlp.stanford.edu/data/glove.6B.zip"
GLOVE_CACHE_DIR = Path.home() / ".cache" / "glove"
GLOVE_ZIP_PATH = GLOVE_CACHE_DIR / "glove.6B.zip"
GLOVE_TXT_PATH = GLOVE_CACHE_DIR / "glove.6B.50d.txt"
VECTOR_DIM = 50
TOP_K_FREQUENT = 15000  # Top 15K most frequent GloVe words
MAX_GLOVE_WORDS = 400000  # Load all 400K GloVe vectors for centroid/axis construction

OUTPUT_DIR = PROJECT_ROOT / "src" / "advanced_prompting_engine" / "data"
NPZ_PATH = OUTPUT_DIR / "semantic_bridge.npz"
VOCAB_PATH = OUTPUT_DIR / "semantic_vocab.json"


# ---------------------------------------------------------------------------
# Pole synonyms — curated to disambiguate each pole in GloVe space
# ---------------------------------------------------------------------------

POLE_SYNONYMS: dict[str, list[str]] = {
    # Ontology
    "particular": ["specific", "individual", "concrete", "singular", "instance", "token", "discrete"],
    "universal": ["general", "abstract", "comprehensive", "global", "total", "category", "class"],
    "static": ["fixed", "stable", "stationary", "unchanging", "permanent", "constant", "settled"],
    "dynamic": ["changing", "moving", "fluid", "evolving", "active", "adaptive", "shifting"],
    # Epistemology
    "empirical": ["observed", "experimental", "measured", "evidence", "data", "tested", "factual"],
    "rational": ["logical", "reasoned", "deductive", "theoretical", "argued", "formal", "analytical"],
    "certain": ["definite", "assured", "confident", "established", "proven", "absolute", "verified"],
    "provisional": ["tentative", "temporary", "conditional", "preliminary", "revisable", "uncertain"],
    # Axiology
    "absolute": ["unconditional", "fixed", "invariant", "universal", "objective", "inherent"],
    "relative": ["conditional", "contextual", "comparative", "dependent", "situated", "variable"],
    "quantitative": ["measurable", "numerical", "counted", "metric", "scored", "statistical"],
    "qualitative": ["descriptive", "interpretive", "subjective", "narrative", "textured", "nuanced"],
    # Teleology
    "immediate": ["proximate", "instant", "direct", "short", "tactical", "urgent", "present"],
    "ultimate": ["final", "long", "distant", "strategic", "enduring", "fundamental", "terminal"],
    "intentional": ["deliberate", "purposeful", "planned", "designed", "conscious", "directed", "willed"],
    "emergent": ["spontaneous", "arising", "unplanned", "organic", "evolving", "unexpected"],
    # Phenomenology — experience-specific. Avoid "independent" (overlaps Praxeology/Aesthetics),
    # "fundamental" (overlaps Teleology), "structural" (overlaps Methodology).
    "objective": ["external", "observable", "measurable", "public", "factual", "verifiable"],
    "subjective": ["internal", "personal", "felt", "experienced", "private", "perceived", "lived"],
    "surface": ["apparent", "visible", "shallow", "exterior", "obvious", "manifest", "overt"],
    "deep": ["hidden", "underlying", "profound", "interior", "latent", "buried", "unconscious"],
    # Ethics — morally specific vocabulary only. Avoid general action/outcome words
    # that also describe physics or drama (no "action", "impact", "effect", "performance").
    "deontological": ["duty", "obligation", "principle", "commandment", "rights", "imperative", "law"],
    "consequential": ["welfare", "happiness", "suffering", "harm", "benefit", "utilitarian", "good"],
    "agent": ["character", "virtue", "conscience", "integrity", "moral", "righteous", "noble"],
    "act": ["deed", "conduct", "wrongdoing", "transgression", "sin", "justice", "judgment"],
    # Aesthetics — art/beauty/form specific. Avoid generic intellectual vocabulary
    # that overlaps with Epistemology or Methodology (no "intellectual", "theoretical", "cognitive").
    "autonomous": ["intrinsic", "pure", "self-contained", "formalist", "disinterested", "absolute"],
    "contextual": ["cultural", "historical", "situated", "institutional", "social", "tradition"],
    "sensory": ["perceptual", "beautiful", "visual", "auditory", "tactile", "sublime", "elegant"],
    "conceptual": ["artistic", "creative", "imaginative", "symbolic", "expressive", "aesthetic"],
    # Praxeology — action-structure specific. "individual" means solo agent, not philosophical individuality.
    "individual": ["solo", "singular", "alone", "solitary", "unilateral", "lone"],
    "coordinated": ["collaborative", "collective", "organized", "synchronized", "joint", "team"],
    "reactive": ["responsive", "defensive", "adapting", "following", "triggered", "passive"],
    "proactive": ["initiating", "anticipating", "planning", "leading", "preemptive", "forward"],
    # Methodology
    "analytic": ["decomposing", "separating", "reductive", "dissecting", "breaking", "isolating"],
    "synthetic": ["combining", "integrating", "composing", "assembling", "unifying", "merging"],
    "deductive": ["deriving", "inferring", "concluding", "applying", "logical", "formal"],
    "inductive": ["generalizing", "observing", "pattern", "discovering", "empirical", "bottom"],
    # Semiotics
    "explicit": ["stated", "overt", "direct", "clear", "declared", "manifest", "visible"],
    "implicit": ["unstated", "implied", "indirect", "hidden", "assumed", "tacit", "latent"],
    "syntactic": ["structural", "formal", "grammatical", "rule", "pattern", "arrangement"],
    "semantic": ["meaningful", "interpreted", "significant", "content", "referential", "sense"],
    # Hermeneutics
    "literal": ["exact", "verbatim", "plain", "direct", "explicit", "straightforward"],
    "figurative": ["metaphorical", "symbolic", "allegorical", "imaginative", "poetic"],
    "author": ["creator", "writer", "original", "intended", "source", "meant"],
    "reader": ["audience", "interpreter", "reception", "response", "subjective"],
    # Heuristics
    "systematic": ["methodical", "ordered", "structured", "procedural", "algorithmic", "rigorous"],
    "intuitive": ["instinctive", "gut", "natural", "spontaneous", "informal", "heuristic"],
    "conservative": ["cautious", "safe", "careful", "traditional", "risk", "preserving", "stable"],
    "exploratory": ["adventurous", "experimental", "innovative", "searching", "creative", "bold"],
}


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
        target_name = "glove.6B.50d.txt"
        zf.extract(target_name, str(GLOVE_CACHE_DIR))
    print(f"[OK] Extracted to {GLOVE_TXT_PATH}")


def load_all_glove() -> tuple[dict[str, int], np.ndarray]:
    """Load ALL GloVe vectors (up to MAX_GLOVE_WORDS).

    Returns:
        vocab: word -> index mapping (all 400K words)
        vectors: shape (n_words, VECTOR_DIM)
    """
    print(f"[LOAD] Reading all GloVe vectors (up to {MAX_GLOVE_WORDS}) ...")
    vocab: dict[str, int] = {}
    vectors: list[np.ndarray] = []

    with open(str(GLOVE_TXT_PATH), "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= MAX_GLOVE_WORDS:
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
# Text tokenization
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


# ---------------------------------------------------------------------------
# Runtime vocabulary selection (~16K words)
# ---------------------------------------------------------------------------

def select_runtime_vocab(
    full_vocab: dict[str, int],
    full_vectors: np.ndarray,
) -> tuple[dict[str, int], np.ndarray]:
    """Select ~16K runtime vocabulary: top 15K frequent + face/domain/axis/pole words.

    Returns:
        runtime_vocab: word -> index in runtime matrix
        runtime_vectors: shape (runtime_size, VECTOR_DIM)
    """
    # Collect all domain-specific words that MUST be in runtime vocab
    must_include: set[str] = set()

    for face in ALL_FACES:
        defn = FACE_DEFINITIONS[face]
        # Face name
        must_include.add(face)
        # Domain replacement tokens
        must_include.update(_tokenize_text(DOMAIN_REPLACEMENTS[face]))
        # Core question tokens
        must_include.update(_tokenize_text(defn["core_question"]))
        # Sub-dimension labels
        for key in ("x_axis_low", "x_axis_high", "y_axis_low", "y_axis_high"):
            label = defn[key]
            # Split hyphenated labels (e.g., "Author-intent" -> "author", "intent")
            must_include.update(_tokenize_text(label))

    # Pole synonyms
    for pole_word, synonyms in POLE_SYNONYMS.items():
        must_include.add(pole_word)
        must_include.update(synonyms)

    # Filter to words actually in GloVe
    must_include = {w for w in must_include if w in full_vocab}

    # Top 15K frequent words (GloVe is sorted by frequency)
    # Take the first TOP_K_FREQUENT words from the full vocab ordering
    frequent_words = set()
    for word, idx in full_vocab.items():
        if idx < TOP_K_FREQUENT:
            frequent_words.add(word)

    # Union
    all_runtime_words = frequent_words | must_include

    # Build runtime vocab and vectors
    runtime_vocab: dict[str, int] = {}
    runtime_vecs: list[np.ndarray] = []
    # Preserve GloVe frequency order for IDF computation
    sorted_words = sorted(all_runtime_words, key=lambda w: full_vocab[w])

    for word in sorted_words:
        runtime_vocab[word] = len(runtime_vecs)
        runtime_vecs.append(full_vectors[full_vocab[word]])

    runtime_vectors = np.stack(runtime_vecs)
    extra = len(must_include - frequent_words)
    print(f"[VOCAB] {len(frequent_words)} frequent + {extra} domain-specific "
          f"= {len(runtime_vocab)} total runtime words")
    return runtime_vocab, runtime_vectors


# ---------------------------------------------------------------------------
# Face centroid construction (AUTHORED LAYERS ONLY)
# ---------------------------------------------------------------------------

def build_face_centroids(
    full_vocab: dict[str, int],
    full_vectors: np.ndarray,
) -> np.ndarray:
    """Build a centroid vector for each of the 12 faces from AUTHORED layers only.

    Sources per face (authored content only — NOT derived 144 question templates):
      - Core question words
      - Sub-dimension labels (x_axis_low, x_axis_high, y_axis_low, y_axis_high)
      - Domain replacement string words
      - Face name

    Returns: shape (12, VECTOR_DIM), unit-normalized.
    """
    centroids = []

    for face in ALL_FACES:
        defn = FACE_DEFINITIONS[face]
        all_words: list[str] = []

        # Face name (2x weight — primary identity)
        all_words.extend([face] * 2)

        # Core question (1x weight)
        all_words.extend(_tokenize_text(defn["core_question"]))

        # Sub-dimension labels (5x weight — these are the most face-specific content,
        # they define the axes and are what discriminates this face from all others)
        for key in ("x_axis_low", "x_axis_high", "y_axis_low", "y_axis_high"):
            label_words = _tokenize_text(defn[key])
            all_words.extend(label_words * 5)

        # Sub-dimension pole synonyms (3x weight — expands the axis vocabulary)
        for key in ("x_axis_low", "x_axis_high", "y_axis_low", "y_axis_high"):
            label = defn[key].lower()
            synonyms = POLE_SYNONYMS.get(label, [])
            for syn in synonyms:
                syn_words = _tokenize_text(syn)
                all_words.extend(syn_words * 3)

        # Domain replacement string (2x weight)
        all_words.extend(_tokenize_text(DOMAIN_REPLACEMENTS[face]) * 2)

        centroid = _text_to_vector(all_words, full_vocab, full_vectors)

        # Normalize to unit length for cosine similarity
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm

        in_vocab = sum(1 for w in all_words if w in full_vocab)
        centroids.append(centroid)
        print(f"  {face:15s}: {len(all_words)} authored words, "
              f"{in_vocab} in GloVe vocab")

    return np.stack(centroids)  # shape (12, 50)


# ---------------------------------------------------------------------------
# Axis direction vectors (24 total: 12 faces x 2 axes)
# ---------------------------------------------------------------------------

def _get_pole_label_words(label: str) -> list[str]:
    """Split a pole label into words, handling hyphens (e.g., 'Author-intent' -> ['author', 'intent'])."""
    return _tokenize_text(label)


def build_axis_directions(
    full_vocab: dict[str, int],
    full_vectors: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build 24 axis direction vectors (high_pole - low_pole).

    For each face, for each axis (x=0, y=1):
      - low_pole = average GloVe vector of (low_label + POLE_SYNONYMS)
      - high_pole = average GloVe vector of (high_label + POLE_SYNONYMS)
      - direction = high_pole - low_pole

    Also performs calibration: projects each pole onto its direction to get
    (expected_low, expected_high) per axis.

    Returns:
        directions: shape (24, VECTOR_DIM) — unit-normalized direction vectors
        cal_low: shape (24,) — expected projection of low pole
        cal_high: shape (24,) — expected projection of high pole
    """
    directions = []
    cal_low_arr = []
    cal_high_arr = []

    for face in ALL_FACES:
        defn = FACE_DEFINITIONS[face]
        for axis_idx, (low_key, high_key) in enumerate([
            ("x_axis_low", "x_axis_high"),
            ("y_axis_low", "y_axis_high"),
        ]):
            low_label = defn[low_key].lower()
            high_label = defn[high_key].lower()

            # Gather all words for each pole
            low_words = _get_pole_label_words(defn[low_key])
            high_words = _get_pole_label_words(defn[high_key])

            # Add pole synonyms for each word in the label
            for w in list(low_words):
                if w in POLE_SYNONYMS:
                    low_words.extend(POLE_SYNONYMS[w])
            for w in list(high_words):
                if w in POLE_SYNONYMS:
                    high_words.extend(POLE_SYNONYMS[w])

            low_vec = _text_to_vector(low_words, full_vocab, full_vectors)
            high_vec = _text_to_vector(high_words, full_vocab, full_vectors)

            direction = high_vec - low_vec
            dir_norm = np.linalg.norm(direction)
            if dir_norm > 0:
                direction_unit = direction / dir_norm
            else:
                direction_unit = np.zeros(VECTOR_DIM, dtype=np.float32)

            # Calibration: project each pole onto direction
            proj_low = float(np.dot(low_vec, direction_unit))
            proj_high = float(np.dot(high_vec, direction_unit))

            directions.append(direction_unit)
            cal_low_arr.append(proj_low)
            cal_high_arr.append(proj_high)

    return (
        np.stack(directions),  # shape (24, 50)
        np.array(cal_low_arr, dtype=np.float32),  # shape (24,)
        np.array(cal_high_arr, dtype=np.float32),  # shape (24,)
    )


# ---------------------------------------------------------------------------
# Per-word artifact computation
# ---------------------------------------------------------------------------

def compute_discriminative_face_similarity(
    runtime_vectors: np.ndarray,
    centroids: np.ndarray,
) -> np.ndarray:
    """Compute discriminative face similarity for each word.

    For each word:
      raw_sim[face] = cosine(word, centroid[face])
      disc_sim[face] = raw_sim[face] - mean(raw_sim across all faces)

    Returns: shape (vocab_size, 12)
    """
    print(f"[COMPUTE] Discriminative face similarity ({runtime_vectors.shape[0]} x 12) ...")

    # Normalize word vectors
    norms = np.linalg.norm(runtime_vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    normed = runtime_vectors / norms

    # centroids are already unit-normalized
    raw_sim = normed @ centroids.T  # (vocab_size, 12)
    mean_sim = np.mean(raw_sim, axis=1, keepdims=True)  # (vocab_size, 1)
    disc_sim = raw_sim - mean_sim  # (vocab_size, 12)

    print(f"[OK] Discriminative face similarity shape: {disc_sim.shape}")
    return disc_sim.astype(np.float32)


def compute_axis_projections(
    runtime_vectors: np.ndarray,
    directions: np.ndarray,
    cal_low: np.ndarray,
    cal_high: np.ndarray,
) -> np.ndarray:
    """Compute per-word axis projections, normalized by calibration to [0,1].

    For each word and each of 24 axes:
      raw_proj = dot(word_vec, direction_unit)
      normalized = (raw_proj - cal_low) / (cal_high - cal_low)
      clamped to [0, 1]

    Returns: shape (vocab_size, 24)
    """
    print(f"[COMPUTE] Axis projections ({runtime_vectors.shape[0]} x 24) ...")

    # Project all words onto all directions
    raw_proj = runtime_vectors @ directions.T  # (vocab_size, 24)

    # Normalize using calibration
    cal_range = cal_high - cal_low  # (24,)
    # Avoid division by zero
    cal_range = np.where(np.abs(cal_range) < 1e-8, 1.0, cal_range)
    normalized = (raw_proj - cal_low[np.newaxis, :]) / cal_range[np.newaxis, :]

    # Clamp to [0, 1]
    clamped = np.clip(normalized, 0.0, 1.0)

    print(f"[OK] Axis projections shape: {clamped.shape}")
    return clamped.astype(np.float32)


def compute_idf_weights(vocab_size: int) -> np.ndarray:
    """Compute IDF-like weights from frequency rank.

    GloVe words are ordered by frequency. More frequent words get LOWER weight
    (they are less informative). Uses log-inverse-rank formula:
      idf[i] = log(vocab_size / (rank + 1))
    Normalized to [0, 1].

    Returns: shape (vocab_size,)
    """
    print(f"[COMPUTE] IDF weights for {vocab_size} words ...")
    ranks = np.arange(vocab_size, dtype=np.float32) + 1.0
    idf = np.log(float(vocab_size) / ranks)
    # Normalize to [0, 1]
    idf_min = idf.min()
    idf_max = idf.max()
    if idf_max - idf_min > 1e-9:
        idf = (idf - idf_min) / (idf_max - idf_min)
    else:
        idf = np.ones(vocab_size, dtype=np.float32)
    print(f"[OK] IDF range: [{idf.min():.4f}, {idf.max():.4f}]")
    return idf.astype(np.float32)


# ---------------------------------------------------------------------------
# Output and reporting
# ---------------------------------------------------------------------------

def save_artifacts(
    runtime_vocab: dict[str, int],
    disc_face_sim: np.ndarray,
    axis_proj: np.ndarray,
    idf_weights: np.ndarray,
) -> None:
    """Save all artifacts to disk."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        str(NPZ_PATH),
        face_sim=disc_face_sim,
        axis_proj=axis_proj,
        idf=idf_weights,
        faces=np.array(ALL_FACES),
    )
    print(f"[SAVE] {NPZ_PATH} ({NPZ_PATH.stat().st_size / 1024:.1f} KB)")

    with open(str(VOCAB_PATH), "w", encoding="utf-8") as f:
        json.dump(runtime_vocab, f)
    print(f"[SAVE] {VOCAB_PATH} ({VOCAB_PATH.stat().st_size / 1024:.1f} KB)")


def report_top_words(
    runtime_vocab: dict[str, int],
    disc_face_sim: np.ndarray,
    top_n: int = 10,
) -> None:
    """Print the top-N most discriminative words per face."""
    idx_to_word = {i: w for w, i in runtime_vocab.items()}

    print(f"\n{'='*70}")
    print(f"Top {top_n} discriminative words per face")
    print(f"{'='*70}")

    for col_idx, face in enumerate(ALL_FACES):
        scores = disc_face_sim[:, col_idx]
        top_indices = np.argsort(scores)[::-1][:top_n]
        top_words = [(idx_to_word[i], float(scores[i])) for i in top_indices]
        words_str = ", ".join(f"{w}({s:.3f})" for w, s in top_words)
        print(f"\n{face}:")
        print(f"  {words_str}")


def report_pole_self_test(
    runtime_vocab: dict[str, int],
    axis_proj: np.ndarray,
) -> bool:
    """Project pole synonym words onto their own axis and verify correct placement.

    Low poles should project < 0.3, high poles should project > 0.7.
    Returns True if all pass.
    """
    print(f"\n{'='*70}")
    print(f"Pole self-test (low < 0.3, high > 0.7)")
    print(f"{'='*70}")

    all_pass = True
    axis_idx = 0

    for face in ALL_FACES:
        defn = FACE_DEFINITIONS[face]
        for low_key, high_key in [("x_axis_low", "x_axis_high"), ("y_axis_low", "y_axis_high")]:
            low_label = defn[low_key].lower()
            high_label = defn[high_key].lower()

            # Get words for each pole
            low_words = _get_pole_label_words(defn[low_key])
            high_words = _get_pole_label_words(defn[high_key])
            for w in list(low_words):
                if w in POLE_SYNONYMS:
                    low_words.extend(POLE_SYNONYMS[w])
            for w in list(high_words):
                if w in POLE_SYNONYMS:
                    high_words.extend(POLE_SYNONYMS[w])

            # Project low pole words
            low_indices = [runtime_vocab[w] for w in low_words if w in runtime_vocab]
            high_indices = [runtime_vocab[w] for w in high_words if w in runtime_vocab]

            if low_indices:
                low_proj = float(np.mean(axis_proj[low_indices, axis_idx]))
            else:
                low_proj = 0.5
            if high_indices:
                high_proj = float(np.mean(axis_proj[high_indices, axis_idx]))
            else:
                high_proj = 0.5

            low_ok = low_proj < 0.3
            high_ok = high_proj > 0.7
            status = "PASS" if (low_ok and high_ok) else "FAIL"
            if not (low_ok and high_ok):
                all_pass = False

            print(f"  {face:15s} {defn[low_key]:20s} -> {low_proj:.3f} {'OK' if low_ok else 'HIGH!'}"
                  f"  |  {defn[high_key]:20s} -> {high_proj:.3f} {'OK' if high_ok else 'LOW!'}"
                  f"  [{status}]")

            axis_idx += 1

    print(f"\n{'='*70}")
    print(f"Pole self-test: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
    print(f"{'='*70}")
    return all_pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print("Geometric Semantic Bridge Builder")
    print("=" * 70)

    # Step 1: Download GloVe
    download_glove()

    # Step 2: Load ALL GloVe vectors
    full_vocab, full_vectors = load_all_glove()

    # Step 3: Build face centroids from AUTHORED layers only
    print(f"\n[BUILD] Computing face centroids (authored layers only) ...")
    centroids = build_face_centroids(full_vocab, full_vectors)

    # Step 4: Build axis direction vectors
    print(f"\n[BUILD] Computing 24 axis direction vectors ...")
    directions, cal_low, cal_high = build_axis_directions(full_vocab, full_vectors)

    # Step 5: Select runtime vocabulary
    print(f"\n[BUILD] Selecting runtime vocabulary ...")
    runtime_vocab, runtime_vectors = select_runtime_vocab(full_vocab, full_vectors)

    # Step 6: Compute per-word artifacts
    print(f"\n[BUILD] Computing per-word artifacts ...")
    disc_face_sim = compute_discriminative_face_similarity(runtime_vectors, centroids)
    axis_proj = compute_axis_projections(runtime_vectors, directions, cal_low, cal_high)
    idf_weights = compute_idf_weights(len(runtime_vocab))

    # Step 7: Save artifacts
    print(f"\n[SAVE] Saving artifacts ...")
    save_artifacts(runtime_vocab, disc_face_sim, axis_proj, idf_weights)

    # Step 8: Reports
    report_top_words(runtime_vocab, disc_face_sim)
    pole_ok = report_pole_self_test(runtime_vocab, axis_proj)

    print(f"\n{'='*70}")
    print(f"Vocabulary size:      {len(runtime_vocab)}")
    print(f"Face similarity:      {disc_face_sim.shape}")
    print(f"Axis projections:     {axis_proj.shape}")
    print(f"IDF weights:          {idf_weights.shape}")
    print(f"Artifacts:            {NPZ_PATH}")
    print(f"                      {VOCAB_PATH}")
    print(f"Pole self-test:       {'PASS' if pole_ok else 'FAIL'}")
    print(f"{'='*70}")
    print("[DONE]")


if __name__ == "__main__":
    main()
