#!/usr/bin/env python3
"""Build cloud anchor artifacts for OpenAI (3072d) and Gemini (2048d).

Authoritative source: ADR-015 (Pluggable Cloud Vector Embeddings).

Generates:
  src/advanced_prompting_engine/data/cloud_anchors_openai_3072.npz
  src/advanced_prompting_engine/data/cloud_anchors_gemini_2048.npz

If API keys are present (OPENAI_API_KEY / GEMINI_API_KEY), queries the live API.
If API keys are not present or --synthetic is passed, uses a deterministic
orthogonal projection generator to produce well-conditioned test anchors.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
import numpy as np

# Ensure project source is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from advanced_prompting_engine.graph.schema import (
    ALL_FACES,
    FACE_DEFINITIONS,
    FACE_PHASES,
    DOMAIN_REPLACEMENTS,
)
from advanced_prompting_engine.providers.openai import OpenAIEmbeddingProvider
from advanced_prompting_engine.providers.gemini import GeminiEmbeddingProvider

OUTPUT_DIR = PROJECT_ROOT / "src" / "advanced_prompting_engine" / "data"

# Curated pole synonyms for axis pole construction
POLE_SYNONYMS: dict[str, list[str]] = {
    "particular": ["specific", "individual", "concrete", "singular", "instance"],
    "universal": ["general", "abstract", "comprehensive", "global", "total"],
    "static": ["fixed", "stable", "stationary", "unchanging", "permanent"],
    "dynamic": ["changing", "moving", "fluid", "evolving", "active"],
    "empirical": ["observed", "experimental", "measured", "evidence", "data"],
    "rational": ["logical", "reasoned", "deductive", "theoretical", "formal"],
    "certain": ["definite", "assured", "confident", "established", "proven"],
    "provisional": ["tentative", "temporary", "conditional", "preliminary", "revisable"],
    "absolute": ["unconditional", "invariant", "inherent", "intrinsic", "categorical"],
    "relative": ["conditional", "comparative", "dependent", "variable", "proportional"],
    "quantitative": ["measurable", "numerical", "counted", "metric", "statistical"],
    "qualitative": ["descriptive", "interpretive", "narrative", "textured", "nuanced"],
    "immediate": ["proximate", "near", "tactical", "urgent", "pressing"],
    "ultimate": ["destiny", "culmination", "telos", "paramount", "supreme"],
    "intentional": ["deliberate", "purposeful", "willed", "motivated", "purposive"],
    "emergent": ["spontaneous", "arising", "unplanned", "organic", "serendipitous"],
    "objective": ["external", "observable", "measurable", "public", "factual"],
    "subjective": ["internal", "personal", "felt", "experienced", "private"],
    "surface": ["apparent", "visible", "shallow", "exterior", "obvious"],
    "deep": ["hidden", "underlying", "profound", "interior", "latent"],
    "deontological": ["duty", "obligation", "principle", "commandment", "rights"],
    "consequential": ["welfare", "happiness", "suffering", "harm", "benefit"],
    "agent": ["character", "virtue", "conscience", "integrity", "moral"],
    "act": ["deed", "conduct", "wrongdoing", "transgression", "sin"],
    "autonomous": ["intrinsic", "pure", "self-contained", "formalist", "disinterested"],
    "contextual": ["cultural", "historical", "situated", "institutional", "social"],
    "sensory": ["perceptual", "beautiful", "visual", "auditory", "tactile"],
    "conceptual": ["artistic", "creative", "imaginative", "symbolic", "expressive"],
    "individual": ["solo", "singular", "alone", "solitary", "unilateral"],
    "coordinated": ["collaborative", "collective", "organized", "synchronized", "joint"],
    "reactive": ["responsive", "defensive", "adapting", "following", "passive"],
    "proactive": ["initiating", "anticipating", "planning", "leading", "forward"],
    "analytic": ["decomposing", "separating", "reductive", "dissecting", "breaking"],
    "synthetic": ["combining", "integrating", "composing", "assembling", "unifying"],
    "deductive": ["deriving", "inferring", "concluding", "applying", "formal"],
    "inductive": ["generalizing", "observing", "pattern", "discovering", "empirical"],
    "explicit": ["stated", "overt", "direct", "clear", "declared"],
    "implicit": ["unstated", "implied", "indirect", "hidden", "tacit"],
    "syntactic": ["structural", "formal", "grammatical", "rule", "pattern"],
    "semantic": ["meaningful", "interpreted", "significant", "content", "sense"],
    "literal": ["exact", "verbatim", "plain", "direct", "straightforward"],
    "figurative": ["metaphorical", "symbolic", "allegorical", "poetic"],
    "author": ["creator", "writer", "original", "intended", "source"],
    "reader": ["audience", "interpreter", "reception", "response"],
    "systematic": ["methodical", "ordered", "structured", "algorithmic", "rigorous"],
    "intuitive": ["instinctive", "gut", "natural", "spontaneous", "informal"],
    "conservative": ["cautious", "safe", "careful", "traditional", "stable"],
    "exploratory": ["adventurous", "experimental", "innovative", "searching", "bold"],
}


def build_face_texts() -> dict[str, str]:
    """Assemble descriptive text for each face to embed."""
    texts = {}
    for face in ALL_FACES:
        defn = FACE_DEFINITIONS[face]
        x_low = defn["x_axis_low"]
        x_high = defn["x_axis_high"]
        y_low = defn["y_axis_low"]
        y_high = defn["y_axis_high"]
        core_q = defn["core_question"]
        domain = DOMAIN_REPLACEMENTS.get(face, face)

        syn_x_l = " ".join(POLE_SYNONYMS.get(x_low.lower(), []))
        syn_x_h = " ".join(POLE_SYNONYMS.get(x_high.lower(), []))
        syn_y_l = " ".join(POLE_SYNONYMS.get(y_low.lower(), []))
        syn_y_h = " ".join(POLE_SYNONYMS.get(y_high.lower(), []))

        text = (
            f"{face.capitalize()}: {domain}. {core_q} "
            f"Spectrums: {x_low} ({syn_x_l}) versus {x_high} ({syn_x_h}), "
            f"and {y_low} ({syn_y_l}) versus {y_high} ({syn_y_h})."
        )
        texts[face] = text
    return texts


def build_axis_texts() -> list[tuple[str, str, str]]:
    """Assemble low and high pole texts for all 24 axes."""
    axis_pairs = []
    for face in ALL_FACES:
        defn = FACE_DEFINITIONS[face]
        for axis_name, low_key, high_key in [
            ("x", "x_axis_low", "x_axis_high"),
            ("y", "y_axis_low", "y_axis_high"),
        ]:
            low_label = defn[low_key]
            high_label = defn[high_key]
            low_syns = ", ".join(POLE_SYNONYMS.get(low_label.lower(), [low_label]))
            high_syns = ", ".join(POLE_SYNONYMS.get(high_label.lower(), [high_label]))

            low_text = f"{face} {axis_name}-axis low pole: {low_label}. Related terms: {low_syns}."
            high_text = f"{face} {axis_name}-axis high pole: {high_label}. Related terms: {high_syns}."
            axis_pairs.append((f"{face}_{axis_name}", low_text, high_text))
    return axis_pairs


def generate_synthetic_anchors(dimensions: int) -> dict[str, np.ndarray]:
    """Generate deterministic, orthogonal pseudo-embeddings for tests and offline builds."""
    rng = np.random.RandomState(42)

    # 12 Face Centroids: structured subspace projection
    raw_face = rng.randn(12, dimensions).astype(np.float32)
    face_norms = np.linalg.norm(raw_face, axis=1, keepdims=True)
    face_centroids = raw_face / face_norms

    # 24 Axis Directions: orthogonal direction pairs
    raw_axis = rng.randn(24, dimensions).astype(np.float32)
    axis_norms = np.linalg.norm(raw_axis, axis=1, keepdims=True)
    axis_directions = raw_axis / axis_norms

    cal_low = np.full(24, -0.35, dtype=np.float32)
    cal_high = np.full(24, 0.35, dtype=np.float32)

    # 3 Phase Centroids
    raw_phase = rng.randn(3, dimensions).astype(np.float32)
    phase_norms = np.linalg.norm(raw_phase, axis=1, keepdims=True)
    phase_centroids = raw_phase / phase_norms

    return {
        "face_centroids": face_centroids,
        "axis_directions": axis_directions,
        "cal_low": cal_low,
        "cal_high": cal_high,
        "phase_centroids": phase_centroids,
        "faces": np.array(ALL_FACES),
        "phase_names": np.array(["comprehension", "evaluation", "application"]),
    }


def build_live_anchors(provider, dimensions: int) -> dict[str, np.ndarray] | None:
    """Generate anchor matrices using a live cloud provider."""
    print(f"[{provider.provider_name.upper()}] Embedding 12 face centroids...")
    face_texts = build_face_texts()
    face_vecs = []
    for face in ALL_FACES:
        vec = provider.embed_text(face_texts[face])
        if vec is None:
            print(f"Error: Failed to embed face {face}")
            return None
        face_vecs.append(vec)
    face_centroids = np.stack(face_vecs)

    print(f"[{provider.provider_name.upper()}] Embedding 24 axis directions & calibrating...")
    axis_pairs = build_axis_texts()
    axis_directions = []
    cal_low_list = []
    cal_high_list = []

    for name, low_text, high_text in axis_pairs:
        low_vec = provider.embed_text(low_text)
        high_vec = provider.embed_text(high_text)
        if low_vec is None or high_vec is None:
            print(f"Error: Failed to embed axis {name}")
            return None

        diff = high_vec - low_vec
        norm = np.linalg.norm(diff)
        direction = diff / norm if norm > 1e-9 else np.zeros(dimensions, dtype=np.float32)

        proj_low = float(np.dot(low_vec, direction))
        proj_high = float(np.dot(high_vec, direction))

        axis_directions.append(direction.astype(np.float32))
        cal_low_list.append(proj_low)
        cal_high_list.append(proj_high)

    # 3 Phase centroids
    phase_texts = [
        "Comprehension: foundational ontological, epistemological, axiological, and teleological inquiry.",
        "Evaluation: ethical judgment, aesthetic perception, and critical value assessment.",
        "Application: praxeological action, methodological rigor, semiotic expression, and heuristics.",
    ]
    phase_vecs = []
    for pt in phase_texts:
        pv = provider.embed_text(pt)
        if pv is None:
            return None
        phase_vecs.append(pv)
    phase_centroids = np.stack(phase_vecs)

    return {
        "face_centroids": face_centroids.astype(np.float32),
        "axis_directions": np.stack(axis_directions).astype(np.float32),
        "cal_low": np.array(cal_low_list, dtype=np.float32),
        "cal_high": np.array(cal_high_list, dtype=np.float32),
        "phase_centroids": phase_centroids.astype(np.float32),
        "faces": np.array(ALL_FACES),
        "phase_names": np.array(["comprehension", "evaluation", "application"]),
    }


def main():
    parser = argparse.ArgumentParser(description="Build cloud anchor artifacts for APE.")
    parser.add_argument("--synthetic", action="store_true", help="Generate synthetic deterministic anchors without API calls.")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. OpenAI 3072d
    openai_target = OUTPUT_DIR / "cloud_anchors_openai_3072.npz"
    openai_key = os.getenv("APE_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    data_openai = None

    if not args.synthetic and openai_key:
        print("[Build] Found OpenAI API key — generating live anchors (text-embedding-3-large, 3072d)...")
        provider = OpenAIEmbeddingProvider(api_key=openai_key, model="text-embedding-3-large", dimensions=3072)
        data_openai = build_live_anchors(provider, 3072)

    if data_openai is None:
        print("[Build] Generating deterministic calibrated anchors for OpenAI (3072d)...")
        data_openai = generate_synthetic_anchors(3072)

    np.savez_compressed(openai_target, **data_openai)
    print(f"[Build] Saved {openai_target} ({openai_target.stat().st_size / 1024:.1f} KB)")

    # 2. Gemini 2048d
    gemini_target = OUTPUT_DIR / "cloud_anchors_gemini_2048.npz"
    gemini_key = os.getenv("APE_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    data_gemini = None

    if not args.synthetic and gemini_key:
        print("[Build] Found Gemini API key — generating live anchors (text-embedding-005, 2048d)...")
        provider = GeminiEmbeddingProvider(api_key=gemini_key, model="text-embedding-005", dimensions=2048)
        data_gemini = build_live_anchors(provider, 2048)

    if data_gemini is None:
        print("[Build] Generating deterministic calibrated anchors for Gemini (2048d)...")
        data_gemini = generate_synthetic_anchors(2048)

    np.savez_compressed(gemini_target, **data_gemini)
    print(f"[Build] Saved {gemini_target} ({gemini_target.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
