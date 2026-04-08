#!/usr/bin/env python3
"""Build the geometric semantic bridge artifacts from GloVe word vectors.

This script runs on the DEVELOPER machine at build time — never at runtime.
It downloads GloVe 6B 100d vectors (~130MB), loads ALL 400K vectors, selects a
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
    CUBE_PAIRS,
    DOMAIN_REPLACEMENTS,
    FACE_DEFINITIONS,
    FACE_PHASES,
)
from advanced_prompting_engine.graph.canonical import BASE_QUESTIONS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
GLOVE_URL = "https://nlp.stanford.edu/data/glove.6B.zip"
GLOVE_CACHE_DIR = Path.home() / ".cache" / "glove"
GLOVE_ZIP_PATH = GLOVE_CACHE_DIR / "glove.6B.zip"
GLOVE_TXT_PATH = GLOVE_CACHE_DIR / "glove.6B.100d.txt"
VECTOR_DIM = 100
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
    # Axiology — evaluation-specific. Avoid "objective"/"subjective" (overlaps Phenomenology),
    # "contextual"/"situated" (overlaps Aesthetics), "universal" (overlaps Ontology).
    "absolute": ["unconditional", "invariant", "inherent", "intrinsic", "categorical", "non-negotiable"],
    "relative": ["conditional", "comparative", "dependent", "variable", "proportional", "graduated"],
    "quantitative": ["measurable", "numerical", "counted", "metric", "scored", "statistical"],
    "qualitative": ["descriptive", "interpretive", "narrative", "textured", "nuanced", "holistic"],
    # Teleology — purpose-specific. Avoid common/broad words ("direct", "short", "present",
    # "final", "long", "fundamental", "designed", "conscious") that attract all text.
    "immediate": ["proximate", "near", "tactical", "urgent", "pressing", "momentary"],
    "ultimate": ["destiny", "culmination", "telos", "paramount", "supreme", "terminal"],
    "intentional": ["deliberate", "purposeful", "willed", "motivated", "purposive", "teleological"],
    "emergent": ["spontaneous", "arising", "unplanned", "organic", "serendipitous", "unexpected"],
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
# Algorithm 1: Counter-fitting (Mrksic et al. 2016 SGD, antonym-only + VSP)
# ---------------------------------------------------------------------------

def _build_antonym_pairs(
    full_vocab: dict[str, int],
) -> dict[int, set[int]]:
    """Build antonym constraint sets from POLE_SYNONYMS.

    For each of 24 axes, all words in the low-pole synonym cluster are
    antonyms of all words in the high-pole synonym cluster. This yields
    approximately 24 x 7 x 7 = ~1176 antonym pairs.

    Returns:
        A: word_idx -> set of antonym word indices (bidirectional)
    """
    A: dict[int, set[int]] = {}

    for face in ALL_FACES:
        defn = FACE_DEFINITIONS[face]
        for low_key, high_key in [
            ("x_axis_low", "x_axis_high"),
            ("y_axis_low", "y_axis_high"),
        ]:
            low_label = defn[low_key].lower()
            high_label = defn[high_key].lower()
            low_words = [low_label] + POLE_SYNONYMS.get(low_label, [])
            high_words = [high_label] + POLE_SYNONYMS.get(high_label, [])

            low_indices = [full_vocab[w] for w in low_words if w in full_vocab]
            high_indices = [full_vocab[w] for w in high_words if w in full_vocab]

            # Cross-product: every low word is antonym of every high word
            for idx in low_indices:
                if idx not in A:
                    A[idx] = set()
                A[idx].update(high_indices)
            for idx in high_indices:
                if idx not in A:
                    A[idx] = set()
                A[idx].update(low_indices)

    return A


def _build_vsp_neighbors(
    full_vectors: np.ndarray,
    constrained_indices: list[int],
    k: int = 10,
    rho: float = 0.2,
) -> dict[int, list[tuple[int, float]]]:
    """Build Vector Space Preservation (VSP) neighbor sets.

    For each constrained word, find its top-K neighbors within rho cosine
    distance in the ORIGINAL vector space. These neighbors will be pulled
    back if they drift during SGD.

    Returns:
        VSP: word_idx -> list of (neighbor_idx, original_euclidean_distance)
    """
    print(f"[COUNTERFIT] Building VSP neighbors (K={k}, rho={rho}) ...")

    # Normalize all vectors for cosine computation
    norms = np.linalg.norm(full_vectors, axis=1, keepdims=True)
    norms = np.where(norms < 1e-9, 1.0, norms)
    normed = full_vectors / norms

    VSP: dict[int, list[tuple[int, float]]] = {}
    n_total = full_vectors.shape[0]

    # For each constrained word, compute cosine sim to ALL words and find
    # top-K within rho distance. Process in batches for memory efficiency.
    batch_size = 64
    constrained_arr = np.array(constrained_indices)

    for batch_start in range(0, len(constrained_arr), batch_size):
        batch_end = min(batch_start + batch_size, len(constrained_arr))
        batch_indices = constrained_arr[batch_start:batch_end]

        # Cosine similarities: (batch, n_total)
        batch_normed = normed[batch_indices]
        sims = batch_normed @ normed.T

        for local_i, global_idx in enumerate(batch_indices):
            row_sims = sims[local_i]
            # Cosine distance = 1 - cosine_similarity
            # Find words with cosine distance < rho (i.e., sim > 1 - rho)
            threshold = 1.0 - rho
            mask = row_sims > threshold
            mask[global_idx] = False  # exclude self

            candidate_indices = np.where(mask)[0]
            candidate_sims = row_sims[candidate_indices]

            # Sort by similarity descending, take top K
            if len(candidate_indices) > k:
                top_k_local = np.argsort(candidate_sims)[::-1][:k]
                candidate_indices = candidate_indices[top_k_local]

            # Store with original euclidean distances
            neighbors = []
            vi = full_vectors[global_idx]
            for nidx in candidate_indices:
                orig_dist = float(np.linalg.norm(vi - full_vectors[nidx]))
                neighbors.append((int(nidx), orig_dist))

            VSP[int(global_idx)] = neighbors

    total_vsp_pairs = sum(len(v) for v in VSP.values())
    print(f"[COUNTERFIT] {len(VSP)} constrained words, "
          f"{total_vsp_pairs} total VSP neighbor pairs")
    return VSP


def counterfit_vectors(
    full_vocab: dict[str, int],
    full_vectors: np.ndarray,
) -> None:
    """Counter-fit GloVe vectors using antonym-only constraints + VSP.

    Implements the Mrksic et al. 2016 SGD procedure:
      - k1 = 0.1 (antonym repulsion weight)
      - k2 = 0   (NO synonym attraction -- antonym-only mode)
      - k3 = 0.1 (VSP preservation weight)
      - delta = 1.0 (antonym distance margin)
      - rho = 0.2 (VSP neighborhood cosine radius)
      - 20 SGD iterations

    Only modifies words that appear in antonym pairs (the 24 axis pole
    synonym clusters). Other words are indirectly affected by VSP.
    Modifies full_vectors in-place.
    """
    k1 = 0.1   # antonym repulsion
    # k2 = 0   # synonym attraction (disabled)
    k3 = 0.1   # VSP preservation
    delta = 1.0  # antonym distance margin
    rho = 0.2    # VSP neighborhood radius
    T = 20       # SGD iterations

    print(f"\n[COUNTERFIT] Mrksic SGD: k1={k1}, k3={k3}, delta={delta}, "
          f"rho={rho}, T={T}")

    # Build antonym constraints
    A = _build_antonym_pairs(full_vocab)
    constrained = sorted(A.keys())
    n_antonym_pairs = sum(len(v) for v in A.values()) // 2
    print(f"[COUNTERFIT] {len(constrained)} constrained words, "
          f"{n_antonym_pairs} antonym pairs")

    # Save original vectors for VSP distance reference
    original_vectors = full_vectors.copy()

    # Build VSP neighbors from original space
    VSP = _build_vsp_neighbors(original_vectors, constrained, k=10, rho=rho)

    # Measure coherence using cosine similarity (robust to normalization changes)
    def _measure_antonym_cosine() -> float:
        """Average cosine similarity between antonym pairs (lower = better separated)."""
        cosines = []
        for idx in constrained:
            vi = full_vectors[idx]
            vi_norm = np.linalg.norm(vi)
            if vi_norm < 1e-9:
                continue
            vi_unit = vi / vi_norm
            for j in A.get(idx, set()):
                if j > idx:
                    vj = full_vectors[j]
                    vj_norm = np.linalg.norm(vj)
                    if vj_norm < 1e-9:
                        continue
                    cosines.append(float(np.dot(vi_unit, vj / vj_norm)))
        return float(np.mean(cosines)) if cosines else 0.0

    cos_before = _measure_antonym_cosine()
    print(f"[COUNTERFIT] BEFORE: avg antonym cosine = {cos_before:.4f} "
          f"(lower = better separated)")

    # SGD iterations
    for t in range(T):
        for idx in constrained:
            vi = full_vectors[idx]
            gradient = np.zeros(VECTOR_DIM, dtype=np.float32)
            count = 0

            # Antonym repulsion (k1): push apart if closer than delta
            for j in A.get(idx, set()):
                diff = vi - full_vectors[j]
                dist = float(np.linalg.norm(diff))
                if dist < delta and dist > 1e-9:
                    gradient += k1 * (diff / dist)  # push away
                    count += 1

            # VSP preservation (k3): pull back if neighbors have drifted
            for (nidx, orig_dist) in VSP.get(idx, []):
                current_diff = vi - full_vectors[nidx]
                current_dist = float(np.linalg.norm(current_diff))
                if current_dist > orig_dist and current_dist > 1e-9:
                    gradient += k3 * (full_vectors[nidx] - vi)  # pull back
                    count += 1

            # Apply averaged gradient
            if count > 0:
                full_vectors[idx] = vi + gradient / count

            # Renormalize to unit length
            norm = float(np.linalg.norm(full_vectors[idx]))
            if norm > 1e-9:
                full_vectors[idx] /= norm

        if (t + 1) % 5 == 0 or t == 0:
            cos_t = _measure_antonym_cosine()
            print(f"  iteration {t+1}/{T}: avg antonym cosine = {cos_t:.4f}")

    cos_after = _measure_antonym_cosine()
    print(f"[COUNTERFIT] AFTER: avg antonym cosine = {cos_after:.4f}")
    print(f"[COUNTERFIT] Delta: {cos_after - cos_before:+.4f} "
          f"({'improved' if cos_after < cos_before else 'worsened'})")


# ---------------------------------------------------------------------------
# Algorithm 2: Contextual Disambiguation Table
# ---------------------------------------------------------------------------

DISAMBIGUATION_ENTRIES: dict[str, list[dict]] = {
    "state": [
        {"context_words": {"quantum", "particle", "energy", "wave", "matter", "electron", "physics", "atom", "field", "rest", "motion"},
         "target_face": "ontology", "seed_words": ["quantum", "particle", "energy", "wave", "configuration", "system"]},
        {"context_words": {"government", "nation", "political", "law", "power", "sovereignty", "country", "federal"},
         "target_face": "praxeology", "seed_words": ["government", "nation", "political", "sovereignty", "institution"]},
    ],
    "compelled": [
        {"context_words": {"force", "motion", "acceleration", "gravity", "momentum", "pressure", "velocity", "physics", "body", "rest"},
         "target_face": "praxeology", "seed_words": ["force", "motion", "compulsion", "necessity", "driven"]},
    ],
    "right": [
        {"context_words": {"left", "turn", "side", "direction", "hand", "angle", "north", "south"},
         "override_type": "suppress"},
    ],
    "deep": [
        {"context_words": {"water", "ocean", "sea", "hole", "cave", "dig", "feet", "meters", "underground"},
         "override_type": "suppress"},
    ],
    "forces": [
        {"context_words": {"gravity", "electromagnetic", "nuclear", "field", "particle", "newton", "acceleration", "mass", "motion", "body"},
         "target_face": "ontology", "seed_words": ["gravity", "electromagnetic", "field", "fundamental", "interaction"]},
        {"context_words": {"military", "army", "police", "special", "armed", "troops", "personnel"},
         "target_face": "praxeology", "seed_words": ["military", "coordinated", "organized", "deployment"]},
    ],
    "heaven": [
        {"context_words": {"earth", "sky", "creation", "cosmos", "universe", "genesis", "firmament", "celestial", "beginning"},
         "target_face": "ontology", "seed_words": ["cosmos", "creation", "existence", "celestial", "realm"]},
    ],
    "tragedy": [
        {"context_words": {"drama", "aristotle", "plot", "catharsis", "theater", "comedy", "poetics", "stage", "genre", "imitation"},
         "target_face": "aesthetics", "seed_words": ["drama", "catharsis", "theatrical", "artistic", "genre"]},
    ],
    "action": [
        {"context_words": {"drama", "scene", "play", "performance", "theater", "film", "actor", "stage", "screenplay", "imitation"},
         "target_face": "aesthetics", "seed_words": ["dramatic", "performance", "theatrical", "scene", "staging"]},
    ],
    # Physics/science -> methodology
    "motion": [
        {"context_words": {"force", "body", "rest", "velocity", "acceleration", "uniform", "line", "state", "change", "impressed"},
         "target_face": "methodology", "seed_words": ["systematic", "deductive", "formal", "mathematical", "law"]},
    ],
    # Aristotle/drama -> aesthetics
    "magnitude": [
        {"context_words": {"tragedy", "action", "serious", "complete", "language", "ornament", "imitation", "artistic"},
         "target_face": "aesthetics", "seed_words": ["artistic", "dramatic", "theatrical", "magnitude", "sublime"]},
    ],
    "serious": [
        {"context_words": {"tragedy", "action", "complete", "magnitude", "language", "imitation", "artistic"},
         "target_face": "aesthetics", "seed_words": ["dramatic", "weighty", "solemn", "dignified", "gravitas"]},
    ],
    # MLK/rhetoric -> semiotics
    "meaning": [
        {"context_words": {"creed", "true", "nation", "dream", "equal", "content", "character", "judged"},
         "target_face": "semiotics", "seed_words": ["meaning", "signify", "symbol", "creed", "declaration"]},
    ],
    "creed": [
        {"context_words": {"meaning", "true", "nation", "dream", "equal", "created"},
         "target_face": "semiotics", "seed_words": ["creed", "declaration", "proclamation", "signify", "charter"]},
    ],
}


def compute_disambiguation_table(
    full_vocab: dict[str, int],
    full_vectors: np.ndarray,
    centroids: np.ndarray,
    directions: np.ndarray,
    cal_low: np.ndarray,
    cal_high: np.ndarray,
    runtime_vocab: dict[str, int],
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Compute override face_sim and axis_proj for polysemous words.

    For each disambiguation entry with seed_words:
      1. Average GloVe vectors of seed words -> sense vector
      2. Compute face_sim through standard pipeline (cosine - mean)
      3. Compute axis_proj through standard pipeline (dot, calibrate, clamp)

    For suppress entries: override with zeros (no face signal).

    Returns:
        disambig_face_sim: shape (N_senses, 12) — override face similarity per sense
        disambig_axis_proj: shape (N_senses, 24) — override axis projection per sense
        disambig_meta: {trigger_word: [{context_words, sense_idx, override_type, target_face, threshold}]}
    """
    print(f"\n[DISAMBIG] Computing disambiguation table ...")

    sense_face_sims = []
    sense_axis_projs = []
    disambig_meta: dict[str, list[dict]] = {}
    sense_idx = 0

    for trigger_word, entries in DISAMBIGUATION_ENTRIES.items():
        disambig_meta[trigger_word] = []

        for entry in entries:
            override_type = entry.get("override_type", "redirect")
            context_words = sorted(entry["context_words"])  # sort for determinism
            threshold = 2

            if override_type == "suppress":
                # Suppress: zeros for face_sim, 0.5 for axis_proj (neutral)
                sense_face_sims.append(np.zeros(12, dtype=np.float32))
                sense_axis_projs.append(np.full(24, 0.5, dtype=np.float32))
            else:
                # Redirect: compute from seed words
                seed_words = entry["seed_words"]
                seed_indices = [full_vocab[w] for w in seed_words if w in full_vocab]

                if seed_indices:
                    sense_vec = np.mean(full_vectors[seed_indices], axis=0)
                else:
                    sense_vec = np.zeros(VECTOR_DIM, dtype=np.float32)

                # Face sim: cosine(sense_vec, centroid) - mean
                norm = np.linalg.norm(sense_vec)
                if norm > 1e-9:
                    sense_unit = sense_vec / norm
                else:
                    sense_unit = np.zeros(VECTOR_DIM, dtype=np.float32)

                raw_sim = sense_unit @ centroids.T  # (12,)
                disc_sim = raw_sim - np.mean(raw_sim)

                # Axis proj: dot(sense_vec, direction) calibrated
                raw_proj = sense_vec @ directions.T  # (24,)
                cal_range = cal_high - cal_low
                cal_range = np.where(np.abs(cal_range) < 1e-8, 1.0, cal_range)
                normalized = (raw_proj - cal_low) / cal_range
                clamped = np.clip(normalized, 0.0, 1.0)

                sense_face_sims.append(disc_sim.astype(np.float32))
                sense_axis_projs.append(clamped.astype(np.float32))

            meta_entry = {
                "context_words": context_words,
                "sense_idx": sense_idx,
                "override_type": override_type,
                "threshold": threshold,
            }
            if "target_face" in entry:
                meta_entry["target_face"] = entry["target_face"]

            disambig_meta[trigger_word].append(meta_entry)
            sense_idx += 1

    disambig_face_sim = np.stack(sense_face_sims) if sense_face_sims else np.zeros((0, 12), dtype=np.float32)
    disambig_axis_proj = np.stack(sense_axis_projs) if sense_axis_projs else np.zeros((0, 24), dtype=np.float32)

    print(f"[DISAMBIG] {len(DISAMBIGUATION_ENTRIES)} trigger words, "
          f"{sense_idx} total senses, arrays shape {disambig_face_sim.shape}")

    return disambig_face_sim, disambig_axis_proj, disambig_meta


# ---------------------------------------------------------------------------
# Algorithm 3: N-gram/Phrase Embeddings
# ---------------------------------------------------------------------------

# Curated phrase lists organized by source
QUESTION_PHRASES: list[str] = [
    "fundamentally exist",
    "true or justified",
    "worth determined",
    "ultimate purposes",
    "represented and realized",
    "right action",
    "aesthetic recognition",
    "actions and intentions",
    "construction and evolution",
    "meaningfully communicated",
    "govern interpretation",
    "practical strategies",
    "moral warrants",
    "moral obligations",
]

POLE_PAIR_PHRASES: list[str] = [
    # Ontology
    "particular universal",
    "static dynamic",
    # Epistemology
    "empirical rational",
    "certain provisional",
    # Axiology
    "absolute relative",
    "quantitative qualitative",
    # Teleology
    "immediate ultimate",
    "intentional emergent",
    # Phenomenology
    "objective subjective",
    "surface deep",
    # Ethics
    "deontological consequential",
    "agent act",
    # Aesthetics
    "autonomous contextual",
    "sensory conceptual",
    # Praxeology
    "individual coordinated",
    "reactive proactive",
    # Methodology
    "analytic synthetic",
    "deductive inductive",
    # Semiotics
    "explicit implicit",
    "syntactic semantic",
    # Hermeneutics
    "literal figurative",
    "author intent",
    "reader response",
    # Heuristics
    "systematic intuitive",
    "conservative exploratory",
]

COMPOSITIONAL_PHRASES: list[str] = [
    # Philosophical key phrases
    "first principles",
    "root cause",
    "mental model",
    "frame of reference",
    "chain of reasoning",
    "burden of proof",
    "thought experiment",
    "moral reasoning",
    "moral compass",
    "ethical framework",
    "value judgment",
    "decision making",
    "problem solving",
    "critical thinking",
    "abstract reasoning",
    "logical structure",
    "causal mechanism",
    "feedback loop",
    "emergent behavior",
    "self organization",
    "collective action",
    "game theory",
    "information theory",
    "signal processing",
    "pattern recognition",
    "knowledge representation",
    "natural language",
    "formal logic",
    "modal logic",
    "deductive reasoning",
    "inductive reasoning",
    "abductive reasoning",
    "analogical reasoning",
    "means and ends",
    "form and function",
    "cause and effect",
    "trial and error",
    "risk assessment",
    "cost benefit",
    "trade off",
    "paradigm shift",
    "cognitive bias",
    "confirmation bias",
    "selection bias",
    "base rate",
    "prior knowledge",
    "posterior probability",
    "null hypothesis",
    "statistical significance",
    "body of knowledge",
    "state of affairs",
    "point of view",
    "line of inquiry",
]

# All curated phrases
ALL_CURATED_PHRASES = QUESTION_PHRASES + POLE_PAIR_PHRASES + COMPOSITIONAL_PHRASES


def compute_ngram_embeddings(
    full_vocab: dict[str, int],
    full_vectors: np.ndarray,
    centroids: np.ndarray,
    directions: np.ndarray,
    cal_low: np.ndarray,
    cal_high: np.ndarray,
    runtime_vocab: dict[str, int],
    runtime_vectors: np.ndarray,
    disc_face_sim: np.ndarray,
    axis_proj: np.ndarray,
    idf_weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, int], list[str], dict[str, str]]:
    """Compute phrase embeddings and their face_sim/axis_proj/idf arrays.

    Phrase embedding = mean of component RETROFITTED word vectors from full_vocab.
    Face_sim and axis_proj computed through the standard pipeline.

    Returns:
        phrase_face_sim: shape (N_phrases, 12)
        phrase_axis_proj: shape (N_phrases, 24)
        phrase_idf: shape (N_phrases,) — IDF as max of component word IDFs
        phrase_vocab: canonical_phrase -> index in phrase arrays (0-based, before offset)
        phrase_keys: list of canonical phrase keys
        surface_to_canonical: surface form (with stop words) -> canonical form
    """
    print(f"\n[PHRASES] Computing n-gram/phrase embeddings ...")

    phrase_face_sims = []
    phrase_axis_projs = []
    phrase_idfs = []
    phrase_vocab: dict[str, int] = {}
    phrase_keys: list[str] = []
    surface_to_canonical: dict[str, str] = {}

    # Stop words for surface-to-canonical mapping
    phrase_stop_words = {"and", "of", "the", "or", "a", "an", "in", "on", "to", "for"}

    for phrase in ALL_CURATED_PHRASES:
        # Canonical form: lowercase, no punctuation, stop words removed
        canonical_words = []
        surface_words = phrase.lower().split()
        for w in surface_words:
            cleaned = "".join(c for c in w if c.isalpha())
            if cleaned and cleaned not in phrase_stop_words:
                canonical_words.append(cleaned)

        if len(canonical_words) < 2:
            continue  # Not a valid phrase (need at least bigram)

        canonical = " ".join(canonical_words)

        if canonical in phrase_vocab:
            continue  # Deduplicate

        # Surface form (original with stop words) -> canonical
        surface = " ".join(surface_words)
        if surface != canonical:
            surface_to_canonical[surface] = canonical

        # Compute phrase embedding from full (retrofitted) vectors
        word_indices = [full_vocab[w] for w in canonical_words if w in full_vocab]
        if not word_indices:
            continue  # No component words found in GloVe

        phrase_vec = np.mean(full_vectors[word_indices], axis=0)

        # Face sim: cosine(phrase_vec, centroid) - mean
        norm = np.linalg.norm(phrase_vec)
        if norm > 1e-9:
            phrase_unit = phrase_vec / norm
        else:
            phrase_unit = np.zeros(VECTOR_DIM, dtype=np.float32)

        raw_sim = phrase_unit @ centroids.T  # (12,)
        phrase_disc_sim = raw_sim - np.mean(raw_sim)

        # Axis proj: dot(phrase_vec, direction) calibrated
        raw_proj = phrase_vec @ directions.T  # (24,)
        cal_range = cal_high - cal_low
        cal_range = np.where(np.abs(cal_range) < 1e-8, 1.0, cal_range)
        normalized = (raw_proj - cal_low) / cal_range
        clamped = np.clip(normalized, 0.0, 1.0)

        # IDF: max of component word IDFs (phrases are rarer than any single word)
        component_idfs = []
        for w in canonical_words:
            if w in runtime_vocab:
                component_idfs.append(float(idf_weights[runtime_vocab[w]]))
        phrase_idf = max(component_idfs) if component_idfs else 0.8  # default high

        idx = len(phrase_keys)
        phrase_vocab[canonical] = idx
        phrase_keys.append(canonical)
        phrase_face_sims.append(phrase_disc_sim.astype(np.float32))
        phrase_axis_projs.append(clamped.astype(np.float32))
        phrase_idfs.append(phrase_idf)

    if phrase_keys:
        pf_sim = np.stack(phrase_face_sims)
        pa_proj = np.stack(phrase_axis_projs)
        p_idf = np.array(phrase_idfs, dtype=np.float32)
    else:
        pf_sim = np.zeros((0, 12), dtype=np.float32)
        pa_proj = np.zeros((0, 24), dtype=np.float32)
        p_idf = np.zeros(0, dtype=np.float32)

    print(f"[PHRASES] {len(phrase_keys)} phrases computed, "
          f"{len(surface_to_canonical)} surface-to-canonical mappings")

    return pf_sim, pa_proj, p_idf, phrase_vocab, phrase_keys, surface_to_canonical


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

    print(f"[EXTRACT] Extracting glove.6B.100d.txt from zip ...")
    with zipfile.ZipFile(str(GLOVE_ZIP_PATH), "r") as zf:
        target_name = "glove.6B.100d.txt"
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
# Technique F: Phase-Aware Face Weighting
# ---------------------------------------------------------------------------

PHASE_NAMES = ["comprehension", "evaluation", "application"]

PHASE_FACES: dict[str, list[str]] = {
    "comprehension": [f for f in ALL_FACES if FACE_PHASES[f] == "comprehension"],
    "evaluation": [f for f in ALL_FACES if FACE_PHASES[f] == "evaluation"],
    "application": [f for f in ALL_FACES if FACE_PHASES[f] == "application"],
}


def build_phase_centroids(
    centroids: np.ndarray,
) -> np.ndarray:
    """Build phase centroid vectors by averaging face centroids per phase.

    Returns: shape (3, VECTOR_DIM), unit-normalized.
    """
    print(f"\n[PHASE] Computing phase centroids ...")
    face_index = {face: i for i, face in enumerate(ALL_FACES)}
    phase_centroids = []

    for phase_name in PHASE_NAMES:
        faces_in_phase = PHASE_FACES[phase_name]
        face_indices = [face_index[f] for f in faces_in_phase]
        phase_vec = np.mean(centroids[face_indices], axis=0)
        norm = np.linalg.norm(phase_vec)
        if norm > 1e-9:
            phase_vec = phase_vec / norm
        phase_centroids.append(phase_vec)
        print(f"  {phase_name:15s}: {len(faces_in_phase)} faces, "
              f"norm before normalize = {norm:.4f}")

    return np.stack(phase_centroids).astype(np.float32)  # (3, VECTOR_DIM)


def compute_word_phase_sim(
    runtime_vectors: np.ndarray,
    phase_centroids: np.ndarray,
) -> np.ndarray:
    """Compute per-word cosine similarity to each phase centroid.

    Returns: shape (vocab_size, 3)
    """
    print(f"\n[PHASE] Computing word-phase similarity ({runtime_vectors.shape[0]} x 3) ...")

    # Normalize word vectors
    norms = np.linalg.norm(runtime_vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)
    normed = runtime_vectors / norms

    # Phase centroids are already unit-normalized
    sim = normed @ phase_centroids.T  # (vocab_size, 3)

    print(f"[OK] Word-phase similarity shape: {sim.shape}, "
          f"range [{sim.min():.4f}, {sim.max():.4f}]")
    return sim.astype(np.float32)


# ---------------------------------------------------------------------------
# Technique D: Per-Face Question Position Matching
# ---------------------------------------------------------------------------

# Stop words for question tokenization (shared with intent parser)
_Q_STOP_WORDS = frozenset({
    "a", "an", "the", "this", "that", "these", "those",
    "at", "in", "on", "of", "from", "to", "into", "as", "by", "with",
    "through", "between", "within", "upon", "along", "across", "about",
    "over", "under", "after", "before", "during", "against", "toward",
    "towards", "among", "around", "without",
    "and", "or", "but", "nor", "yet", "so", "if", "then", "than",
    "it", "its", "he", "she", "we", "us", "me", "my", "our", "your",
    "you", "they", "them", "their", "his", "her",
    "what", "how", "which", "where", "when", "who", "whom", "why",
    "is", "are", "was", "were", "be", "been", "being",
    "has", "have", "had", "having",
    "do", "does", "did", "doing",
    "can", "could", "will", "would", "shall", "should",
    "may", "might", "must", "need", "ought",
    "not", "no", "also", "just", "only", "very", "too", "more", "most",
    "some", "any", "all", "each", "every", "both", "such",
    "here", "there", "now", "already", "still", "even",
})


def _idf_weighted_average(
    words: list[str],
    vocab: dict[str, int],
    vectors: np.ndarray,
) -> np.ndarray:
    """Compute IDF-weighted average vector for a list of words.

    IDF approximation: words later in GloVe (higher index = less frequent)
    get higher weight. Uses log(vocab_size / (rank+1)) formula.
    """
    indices = [vocab[w] for w in words if w in vocab]
    if not indices:
        return np.zeros(VECTOR_DIM, dtype=np.float32)

    vs = vectors[indices]
    vocab_size = len(vocab)
    ranks = np.array(indices, dtype=np.float32) + 1.0
    idf = np.log(float(vocab_size) / ranks)
    # Normalize IDF to [0, 1]
    idf_min, idf_max = idf.min(), idf.max()
    if idf_max - idf_min > 1e-9:
        idf = (idf - idf_min) / (idf_max - idf_min)
    else:
        idf = np.ones_like(idf)

    total = idf.sum()
    if total < 1e-9:
        return np.mean(vs, axis=0)
    return (vs * idf[:, np.newaxis]).sum(axis=0) / total


def compute_question_position_maps(
    full_vocab: dict[str, int],
    full_vectors: np.ndarray,
    runtime_vocab: dict[str, int],
    runtime_vectors: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, list[tuple[int, int]]]:
    """Compute per-word best-matching question position for each face.

    For each of 12 faces, embed all 144 questions as IDF-weighted GloVe vectors.
    For each word in runtime vocab, find the best-matching question within each
    face and record its (x, y) position.

    Returns:
        word_question_x: shape (vocab_size, 12) dtype int8
        word_question_y: shape (vocab_size, 12) dtype int8
        question_positions: ordered list of (x, y) for the 144 questions
    """
    print(f"\n[QUESTIONS] Computing per-face question position maps ...")

    question_positions = list(BASE_QUESTIONS.keys())  # 144 (x,y) pairs
    n_questions = len(question_positions)
    vocab_size = runtime_vectors.shape[0]

    # Normalize runtime word vectors
    word_norms = np.linalg.norm(runtime_vectors, axis=1, keepdims=True)
    word_norms = np.where(word_norms == 0, 1, word_norms)
    word_normed = runtime_vectors / word_norms

    word_question_x = np.zeros((vocab_size, 12), dtype=np.int8)
    word_question_y = np.zeros((vocab_size, 12), dtype=np.int8)

    for face_idx, face in enumerate(ALL_FACES):
        domain = DOMAIN_REPLACEMENTS[face]
        question_vecs = []

        for (x, y) in question_positions:
            template = BASE_QUESTIONS[(x, y)]
            question_text = template.replace("{domain}", domain)
            # Tokenize: lowercase, remove punctuation, filter short/stop words
            cleaned = question_text.lower()
            for ch in "?.,;:!'\"()[]{}—-–/":
                cleaned = cleaned.replace(ch, " ")
            words = [w for w in cleaned.split() if w not in _Q_STOP_WORDS and len(w) > 2]

            vec = _idf_weighted_average(words, full_vocab, full_vectors)
            question_vecs.append(vec)

        q_matrix = np.stack(question_vecs)  # (144, VECTOR_DIM)
        # Normalize question vectors
        q_norms = np.linalg.norm(q_matrix, axis=1, keepdims=True)
        q_norms = np.where(q_norms == 0, 1, q_norms)
        q_normed = q_matrix / q_norms

        # Cosine similarity: (vocab_size, 144)
        similarities = word_normed @ q_normed.T
        best_idx = similarities.argmax(axis=1)  # (vocab_size,)

        for i, idx in enumerate(best_idx):
            pos = question_positions[idx]
            word_question_x[i, face_idx] = pos[0]
            word_question_y[i, face_idx] = pos[1]

        # Report a few top-matching positions
        print(f"  {face:15s}: {n_questions} questions embedded, "
              f"best-match positions range x=[{word_question_x[:, face_idx].min()}, "
              f"{word_question_x[:, face_idx].max()}], "
              f"y=[{word_question_y[:, face_idx].min()}, "
              f"{word_question_y[:, face_idx].max()}]")

    print(f"[OK] Question position maps: x={word_question_x.shape}, y={word_question_y.shape}")
    return word_question_x, word_question_y, question_positions


# ---------------------------------------------------------------------------
# Question-Guided Vocabulary Expansion
# ---------------------------------------------------------------------------

def expand_vocab_by_question_proximity(
    full_vocab: dict[str, int],
    full_vectors: np.ndarray,
    runtime_vocab: dict[str, int],
    runtime_vectors: np.ndarray,
    centroids: np.ndarray,
    directions: np.ndarray,
    cal_low: np.ndarray,
    cal_high: np.ndarray,
    idf_weights: np.ndarray,
    disc_face_sim: np.ndarray,
    axis_proj: np.ndarray,
    word_phase_sim: np.ndarray,
    word_question_x: np.ndarray,
    word_question_y: np.ndarray,
    phase_centroids: np.ndarray,
    max_additions: int = 5000,
) -> tuple[dict[str, int], np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Expand vocabulary with OOV words most relevant to the 1728 construction questions.

    For each face's 144 questions, embed the question as IDF-weighted average of
    GloVe word vectors. For each OOV word (in full GloVe but not runtime vocab),
    compute max cosine similarity to any question embedding. Select the top
    max_additions words by this max similarity score.

    Each added word enters with a known best-matching question, which gives it
    a natural (face, x, y) position grounded in the geometry.

    Returns updated: (disc_face_sim, axis_proj, idf_weights, word_phase_sim,
                      word_question_x, word_question_y, runtime_vocab)
    """
    print(f"\n[EXPAND] Question-guided vocabulary expansion (max {max_additions}) ...")

    # Step 1: Embed all 1728 questions as IDF-weighted GloVe averages
    question_positions = list(BASE_QUESTIONS.keys())  # 144 (x,y) pairs
    all_q_vecs = []      # (1728,) list -> (1728, VECTOR_DIM)
    all_q_faces = []     # face index per question
    all_q_pos = []       # (x, y) per question

    for face_idx, face in enumerate(ALL_FACES):
        domain = DOMAIN_REPLACEMENTS[face]
        for (x, y) in question_positions:
            template = BASE_QUESTIONS[(x, y)]
            question_text = template.replace("{domain}", domain)
            cleaned = question_text.lower()
            for ch in "?.,;:!'\"()[]{}—-–/":
                cleaned = cleaned.replace(ch, " ")
            words = [w for w in cleaned.split() if w not in _Q_STOP_WORDS and len(w) > 2]

            vec = _idf_weighted_average(words, full_vocab, full_vectors)
            all_q_vecs.append(vec)
            all_q_faces.append(face_idx)
            all_q_pos.append((x, y))

    q_matrix = np.stack(all_q_vecs)  # (1728, VECTOR_DIM)

    # Step 2: Normalize question vectors to unit length
    q_norms = np.linalg.norm(q_matrix, axis=1, keepdims=True)
    q_norms = np.where(q_norms < 1e-9, 1.0, q_norms)
    q_normed = q_matrix / q_norms

    # Step 3: Identify OOV words (in full GloVe but not runtime vocab)
    runtime_set = set(runtime_vocab.keys())
    oov_words = []
    oov_indices = []
    for word, idx in full_vocab.items():
        if word not in runtime_set:
            oov_words.append(word)
            oov_indices.append(idx)

    if not oov_words:
        print(f"[EXPAND] No OOV words found — skipping expansion")
        return (disc_face_sim, axis_proj, idf_weights, word_phase_sim,
                word_question_x, word_question_y, runtime_vocab)

    print(f"[EXPAND] {len(oov_words)} OOV candidates ...")

    # Step 4: Compute max cosine similarity to any question for each OOV word
    oov_vecs = full_vectors[oov_indices]  # (N_oov, VECTOR_DIM)
    oov_norms = np.linalg.norm(oov_vecs, axis=1, keepdims=True)
    oov_norms = np.where(oov_norms < 1e-9, 1.0, oov_norms)
    oov_normed = oov_vecs / oov_norms

    # Process in batches to limit memory: (batch, 1728) similarities
    batch_size = 10000
    max_sims = np.zeros(len(oov_words), dtype=np.float32)
    best_q_idx = np.zeros(len(oov_words), dtype=np.int32)

    for b_start in range(0, len(oov_words), batch_size):
        b_end = min(b_start + batch_size, len(oov_words))
        batch_normed = oov_normed[b_start:b_end]  # (batch, dim)
        sims = batch_normed @ q_normed.T            # (batch, 1728)
        max_sims[b_start:b_end] = sims.max(axis=1)
        best_q_idx[b_start:b_end] = sims.argmax(axis=1)

    # Step 5: Select top max_additions by max question similarity
    top_k = min(max_additions, len(oov_words))
    top_local_indices = np.argsort(max_sims)[::-1][:top_k]

    # Filter: require minimum similarity threshold
    min_sim = 0.3
    top_local_indices = [i for i in top_local_indices if max_sims[i] >= min_sim]

    if not top_local_indices:
        print(f"[EXPAND] No OOV words above similarity threshold {min_sim} — skipping")
        return (disc_face_sim, axis_proj, idf_weights, word_phase_sim,
                word_question_x, word_question_y, runtime_vocab)

    print(f"[EXPAND] Selected {len(top_local_indices)} OOV words "
          f"(sim range [{max_sims[top_local_indices[-1]]:.4f}, "
          f"{max_sims[top_local_indices[0]]:.4f}])")

    # Step 6: Compute all arrays for the new words
    new_face_sims = []
    new_axis_projs = []
    new_idfs = []
    new_phase_sims = []
    new_qx = []
    new_qy = []
    new_words = []

    # Pre-compute calibration range
    cal_range = cal_high - cal_low
    cal_range = np.where(np.abs(cal_range) < 1e-8, 1.0, cal_range)

    # Normalize phase centroids for cosine sim
    pc_norms = np.linalg.norm(phase_centroids, axis=1, keepdims=True)
    pc_norms = np.where(pc_norms < 1e-9, 1.0, pc_norms)
    pc_normed = phase_centroids / pc_norms

    base_runtime_size = len(runtime_vocab)

    for rank, local_i in enumerate(top_local_indices):
        word = oov_words[local_i]
        full_idx = oov_indices[local_i]
        vec = full_vectors[full_idx]

        # Face similarity: cosine(word, centroid) - mean
        vec_norm = np.linalg.norm(vec)
        if vec_norm > 1e-9:
            vec_unit = vec / vec_norm
        else:
            vec_unit = np.zeros(VECTOR_DIM, dtype=np.float32)

        raw_sim = vec_unit @ centroids.T  # (12,)
        disc_sim = raw_sim - np.mean(raw_sim)
        new_face_sims.append(disc_sim.astype(np.float32))

        # Axis projections: dot(word, direction) calibrated
        raw_proj = vec @ directions.T  # (24,)
        normalized = (raw_proj - cal_low) / cal_range
        clamped = np.clip(normalized, 0.0, 1.0)
        new_axis_projs.append(clamped.astype(np.float32))

        # IDF: based on GloVe frequency rank, same formula as compute_idf_weights
        # but for the full vocab index. Higher index = less frequent = higher IDF.
        total_full = len(full_vocab)
        idf_val = np.log(float(total_full) / (full_idx + 1.0))
        # Normalize same way: use the observed range from runtime IDF
        idf_min = 0.0  # runtime IDF is already [0, 1]
        idf_max = np.log(float(base_runtime_size))
        if idf_max > 1e-9:
            idf_normed = min(1.0, max(0.0, idf_val / idf_max))
        else:
            idf_normed = 0.5
        new_idfs.append(idf_normed)

        # Phase similarity: cosine(word, phase_centroid)
        phase_sim = vec_unit @ pc_normed.T  # (3,)
        new_phase_sims.append(phase_sim.astype(np.float32))

        # Question position: use the best-matching question's (face, x, y)
        best_q = best_q_idx[local_i]
        best_face_idx = all_q_faces[best_q]
        best_pos = all_q_pos[best_q]

        # For the best-matching face, use that question's position.
        # For other faces, find the best matching question within that face.
        qx_row = np.zeros(12, dtype=np.int8)
        qy_row = np.zeros(12, dtype=np.int8)

        # Compute per-face best question match
        for fi in range(12):
            # Slice of questions for this face: indices fi*144 to (fi+1)*144
            face_q_start = fi * 144
            face_q_end = face_q_start + 144
            face_q_sims = vec_unit @ q_normed[face_q_start:face_q_end].T  # (144,)
            best_local_q = int(np.argmax(face_q_sims))
            pos = question_positions[best_local_q]
            qx_row[fi] = pos[0]
            qy_row[fi] = pos[1]

        new_qx.append(qx_row)
        new_qy.append(qy_row)
        new_words.append(word)

    # Step 7: Extend all arrays
    n_new = len(new_words)
    new_face_sim_arr = np.stack(new_face_sims)         # (n_new, 12)
    new_axis_proj_arr = np.stack(new_axis_projs)       # (n_new, 24)
    new_idf_arr = np.array(new_idfs, dtype=np.float32) # (n_new,)
    new_phase_sim_arr = np.stack(new_phase_sims)       # (n_new, 3)
    new_qx_arr = np.stack(new_qx)                     # (n_new, 12)
    new_qy_arr = np.stack(new_qy)                     # (n_new, 12)

    disc_face_sim = np.concatenate([disc_face_sim, new_face_sim_arr], axis=0)
    axis_proj = np.concatenate([axis_proj, new_axis_proj_arr], axis=0)
    idf_weights = np.concatenate([idf_weights, new_idf_arr], axis=0)
    word_phase_sim = np.concatenate([word_phase_sim, new_phase_sim_arr], axis=0)
    word_question_x = np.concatenate([word_question_x, new_qx_arr], axis=0)
    word_question_y = np.concatenate([word_question_y, new_qy_arr], axis=0)

    # Add to runtime vocab with offset indices
    # disc_face_sim now has (old_size + n_new) rows; new words start at old_size
    expansion_offset = disc_face_sim.shape[0] - n_new
    for i, word in enumerate(new_words):
        runtime_vocab[word] = expansion_offset + i

    # Report some interesting additions
    print(f"[EXPAND] Added {n_new} words to vocabulary")
    print(f"[EXPAND] New array sizes: face_sim={disc_face_sim.shape}, "
          f"axis_proj={axis_proj.shape}, idf={idf_weights.shape}")
    # Show a few examples
    sample_count = min(10, n_new)
    print(f"[EXPAND] Sample additions (top {sample_count} by question proximity):")
    for i in range(sample_count):
        local_i = top_local_indices[i]
        word = oov_words[local_i]
        sim = max_sims[local_i]
        best_q = best_q_idx[local_i]
        best_face = ALL_FACES[all_q_faces[best_q]]
        best_pos = all_q_pos[best_q]
        print(f"  {word:20s} sim={sim:.4f} -> {best_face} ({best_pos[0]},{best_pos[1]})")

    # Check specific words of interest
    check_words = ["imitation", "ornament", "embellished", "perseveres",
                   "catharsis", "sovereignty", "metaphorical"]
    found = [w for w in check_words if w in runtime_vocab]
    missing = [w for w in check_words if w not in runtime_vocab]
    if found:
        print(f"[EXPAND] Check words now in vocab: {', '.join(found)}")
    if missing:
        print(f"[EXPAND] Check words still missing: {', '.join(missing)}")

    return (disc_face_sim, axis_proj, idf_weights, word_phase_sim,
            word_question_x, word_question_y, runtime_vocab)


# ---------------------------------------------------------------------------
# Output and reporting
# ---------------------------------------------------------------------------

def save_artifacts(
    runtime_vocab: dict[str, int],
    disc_face_sim: np.ndarray,
    axis_proj: np.ndarray,
    idf_weights: np.ndarray,
    disambig_face_sim: np.ndarray | None = None,
    disambig_axis_proj: np.ndarray | None = None,
    disambig_meta: dict | None = None,
    phrase_keys: list[str] | None = None,
    surface_to_canonical: dict[str, str] | None = None,
    phase_centroids: np.ndarray | None = None,
    word_phase_sim: np.ndarray | None = None,
    word_question_x: np.ndarray | None = None,
    word_question_y: np.ndarray | None = None,
) -> None:
    """Save all artifacts to disk."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    npz_dict = {
        "face_sim": disc_face_sim,
        "axis_proj": axis_proj,
        "idf": idf_weights,
        "faces": np.array(ALL_FACES),
    }

    # Add disambiguation arrays if present
    if disambig_face_sim is not None:
        npz_dict["disambig_face_sim"] = disambig_face_sim
    if disambig_axis_proj is not None:
        npz_dict["disambig_axis_proj"] = disambig_axis_proj

    # Add phase weighting arrays (Technique F)
    if phase_centroids is not None:
        npz_dict["phase_centroids"] = phase_centroids
    if word_phase_sim is not None:
        npz_dict["word_phase_sim"] = word_phase_sim

    # Add question position maps (Technique D)
    if word_question_x is not None:
        npz_dict["word_question_x"] = word_question_x
    if word_question_y is not None:
        npz_dict["word_question_y"] = word_question_y

    np.savez_compressed(str(NPZ_PATH), **npz_dict)
    print(f"[SAVE] {NPZ_PATH} ({NPZ_PATH.stat().st_size / 1024:.1f} KB)")

    # Build vocab JSON with optional sections
    vocab_data: dict = dict(runtime_vocab)

    # Wrap in structured format if we have extra sections
    if disambig_meta is not None or phrase_keys is not None:
        vocab_data = {
            "words": runtime_vocab,
        }
        if disambig_meta is not None:
            vocab_data["disambiguation"] = disambig_meta
        if phrase_keys is not None:
            vocab_data["phrases"] = phrase_keys
        if surface_to_canonical is not None:
            vocab_data["surface_to_canonical"] = surface_to_canonical
        # Add phase names for runtime lookup
        vocab_data["phase_names"] = PHASE_NAMES

    with open(str(VOCAB_PATH), "w", encoding="utf-8") as f:
        json.dump(vocab_data, f)
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

    # Step 3: [Alg 1] Counter-fitting (Mrksic SGD, antonym-only + VSP)
    # Replaces the disabled Faruqui-style retrofitting. Uses antonym repulsion
    # only (k2=0) with VSP to preserve neighborhood structure.
    # counterfit_vectors(full_vocab, full_vectors)  # DISABLED — testing isolation

    # Step 4: Build face centroids from AUTHORED layers only (uses counter-fitted vectors)
    print(f"\n[BUILD] Computing face centroids (authored layers only) ...")
    centroids = build_face_centroids(full_vocab, full_vectors)

    # Step 5: Build axis direction vectors (uses counter-fitted vectors)
    print(f"\n[BUILD] Computing 24 axis direction vectors ...")
    directions, cal_low, cal_high = build_axis_directions(full_vocab, full_vectors)

    # Step 6: Select runtime vocabulary
    print(f"\n[BUILD] Selecting runtime vocabulary ...")
    runtime_vocab, runtime_vectors = select_runtime_vocab(full_vocab, full_vectors)

    # Step 7: Compute per-word artifacts
    print(f"\n[BUILD] Computing per-word artifacts ...")
    disc_face_sim = compute_discriminative_face_similarity(runtime_vectors, centroids)
    axis_proj = compute_axis_projections(runtime_vectors, directions, cal_low, cal_high)
    idf_weights = compute_idf_weights(len(runtime_vocab))

    # Step 8: [Alg 2] Compute disambiguation table
    disambig_face_sim, disambig_axis_proj, disambig_meta = compute_disambiguation_table(
        full_vocab, full_vectors, centroids, directions, cal_low, cal_high, runtime_vocab,
    )

    # Step 9: [Alg 3] Compute n-gram/phrase embeddings
    phrase_face_sim, phrase_axis_proj, phrase_idf, phrase_vocab, phrase_keys, surface_to_canonical = (
        compute_ngram_embeddings(
            full_vocab, full_vectors, centroids, directions, cal_low, cal_high,
            runtime_vocab, runtime_vectors, disc_face_sim, axis_proj, idf_weights,
        )
    )

    # Step 10: Extend runtime arrays with phrase rows
    if len(phrase_keys) > 0:
        base_size = len(runtime_vocab)
        disc_face_sim = np.concatenate([disc_face_sim, phrase_face_sim], axis=0)
        axis_proj = np.concatenate([axis_proj, phrase_axis_proj], axis=0)
        idf_weights = np.concatenate([idf_weights, phrase_idf], axis=0)
        # Add phrase keys to runtime_vocab with offset indices
        for canonical, local_idx in phrase_vocab.items():
            runtime_vocab[canonical] = base_size + local_idx
        print(f"[EXTEND] Appended {len(phrase_keys)} phrase rows, "
              f"new array sizes: face_sim={disc_face_sim.shape}, "
              f"axis_proj={axis_proj.shape}, idf={idf_weights.shape}")

    # Step 11: [Technique F] Phase-aware face weighting
    phase_centroids = build_phase_centroids(centroids)
    word_phase_sim = compute_word_phase_sim(runtime_vectors, phase_centroids)
    # Extend word_phase_sim to include phrase rows (use zeros for phrases)
    if len(phrase_keys) > 0:
        phrase_phase_pad = np.zeros((len(phrase_keys), 3), dtype=np.float32)
        word_phase_sim = np.concatenate([word_phase_sim, phrase_phase_pad], axis=0)
        print(f"[EXTEND] Phase sim extended for phrases: {word_phase_sim.shape}")

    # Step 12: [Technique D] Per-face question position maps
    word_question_x, word_question_y, question_positions = compute_question_position_maps(
        full_vocab, full_vectors, runtime_vocab, runtime_vectors,
    )
    # Extend for phrase rows (default position (5, 5) = center for phrases)
    if len(phrase_keys) > 0:
        phrase_qx_pad = np.full((len(phrase_keys), 12), 5, dtype=np.int8)
        phrase_qy_pad = np.full((len(phrase_keys), 12), 5, dtype=np.int8)
        word_question_x = np.concatenate([word_question_x, phrase_qx_pad], axis=0)
        word_question_y = np.concatenate([word_question_y, phrase_qy_pad], axis=0)
        print(f"[EXTEND] Question maps extended for phrases: "
              f"x={word_question_x.shape}, y={word_question_y.shape}")

    # Step 13: Question-guided vocabulary expansion
    (disc_face_sim, axis_proj, idf_weights, word_phase_sim,
     word_question_x, word_question_y, runtime_vocab) = expand_vocab_by_question_proximity(
        full_vocab, full_vectors, runtime_vocab, runtime_vectors,
        centroids, directions, cal_low, cal_high,
        idf_weights, disc_face_sim, axis_proj,
        word_phase_sim, word_question_x, word_question_y,
        phase_centroids, max_additions=5000,
    )

    # Step 14: Save artifacts
    print(f"\n[SAVE] Saving artifacts ...")
    save_artifacts(
        runtime_vocab, disc_face_sim, axis_proj, idf_weights,
        disambig_face_sim=disambig_face_sim,
        disambig_axis_proj=disambig_axis_proj,
        disambig_meta=disambig_meta,
        phrase_keys=phrase_keys,
        surface_to_canonical=surface_to_canonical,
        phase_centroids=phase_centroids,
        word_phase_sim=word_phase_sim,
        word_question_x=word_question_x,
        word_question_y=word_question_y,
    )

    # Step 15: Reports
    report_top_words(runtime_vocab, disc_face_sim)
    pole_ok = report_pole_self_test(runtime_vocab, axis_proj)

    print(f"\n{'='*70}")
    print(f"Vocabulary size:      {len(runtime_vocab)} (words + phrases)")
    print(f"Face similarity:      {disc_face_sim.shape}")
    print(f"Axis projections:     {axis_proj.shape}")
    print(f"IDF weights:          {idf_weights.shape}")
    print(f"Disambiguation:       {len(disambig_meta)} triggers, {disambig_face_sim.shape[0]} senses")
    print(f"Phrases:              {len(phrase_keys)} n-grams")
    print(f"Phase centroids:      {phase_centroids.shape}")
    print(f"Word-phase sim:       {word_phase_sim.shape}")
    print(f"Question pos maps:    x={word_question_x.shape}, y={word_question_y.shape}")
    print(f"Artifacts:            {NPZ_PATH}")
    print(f"                      {VOCAB_PATH}")
    print(f"Pole self-test:       {'PASS' if pole_ok else 'FAIL'}")
    print(f"{'='*70}")
    print("[DONE]")


if __name__ == "__main__":
    main()
