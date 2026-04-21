#!/usr/bin/env python3
"""Build the geometric semantic bridge artifacts from BGE embeddings.

This script runs on the DEVELOPER machine at build time — never at runtime.

Vector source: BAAI/bge-large-en-v1.5 via sentence-transformers at native 1024
dimensions. No dimensionality reduction. No GloVe. No Model2Vec. Frequency
ordering comes from wordfreq.

Pre-computes per-word artifacts:
  - Discriminative face similarity: cosine(word, centroid) - mean → (N, 12)
  - Axis projections: dot(word, direction_unit) normalized by calibration → (N, 24)
  - IDF weights from wordfreq Zipf rank → (N,)

Artifacts saved:
  src/advanced_prompting_engine/data/semantic_bridge.npz
  src/advanced_prompting_engine/data/semantic_vocab.json

Build-time dependencies (install via `pip install -e .[build]`):
  sentence-transformers, torch, wordfreq, nltk

Usage:
    python3 scripts/build_semantic_bridge.py
"""

from __future__ import annotations

import json
import sys
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
BGE_MODEL_NAME = "BAAI/bge-large-en-v1.5"
BGE_DIM = 1024  # native output dim — not a hard constraint, reported for clarity
TOP_K_FREQUENT = 15000  # frequent English words to include in runtime vocab
BGE_BATCH_SIZE = 64

OUTPUT_DIR = PROJECT_ROOT / "src" / "advanced_prompting_engine" / "data"
NPZ_PATH = OUTPUT_DIR / "semantic_bridge.npz"
VOCAB_PATH = OUTPUT_DIR / "semantic_vocab.json"


# ---------------------------------------------------------------------------
# Pole synonyms — curated to disambiguate each pole in embedding space
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
    "absolute": ["unconditional", "invariant", "inherent", "intrinsic", "categorical", "non-negotiable"],
    "relative": ["conditional", "comparative", "dependent", "variable", "proportional", "graduated"],
    "quantitative": ["measurable", "numerical", "counted", "metric", "scored", "statistical"],
    "qualitative": ["descriptive", "interpretive", "narrative", "textured", "nuanced", "holistic"],
    # Teleology
    "immediate": ["proximate", "near", "tactical", "urgent", "pressing", "momentary"],
    "ultimate": ["destiny", "culmination", "telos", "paramount", "supreme", "terminal"],
    "intentional": ["deliberate", "purposeful", "willed", "motivated", "purposive", "teleological"],
    "emergent": ["spontaneous", "arising", "unplanned", "organic", "serendipitous", "unexpected"],
    # Phenomenology
    "objective": ["external", "observable", "measurable", "public", "factual", "verifiable"],
    "subjective": ["internal", "personal", "felt", "experienced", "private", "perceived", "lived"],
    "surface": ["apparent", "visible", "shallow", "exterior", "obvious", "manifest", "overt"],
    "deep": ["hidden", "underlying", "profound", "interior", "latent", "buried", "unconscious"],
    # Ethics
    "deontological": ["duty", "obligation", "principle", "commandment", "rights", "imperative", "law"],
    "consequential": ["welfare", "happiness", "suffering", "harm", "benefit", "utilitarian", "good"],
    "agent": ["character", "virtue", "conscience", "integrity", "moral", "righteous", "noble"],
    "act": ["deed", "conduct", "wrongdoing", "transgression", "sin", "justice", "judgment"],
    # Aesthetics
    "autonomous": ["intrinsic", "pure", "self-contained", "formalist", "disinterested", "absolute"],
    "contextual": ["cultural", "historical", "situated", "institutional", "social", "tradition"],
    "sensory": ["perceptual", "beautiful", "visual", "auditory", "tactile", "sublime", "elegant"],
    "conceptual": ["artistic", "creative", "imaginative", "symbolic", "expressive", "aesthetic"],
    # Praxeology
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
# Face vernacular — object-level vocabulary per face
# ---------------------------------------------------------------------------
# These words are NOT pole synonyms (pole synonyms must preserve opposition
# for axis direction vectors). They are face-identifying object-level
# vocabulary used only to enrich the face centroid. Feeds the centroid with
# concrete words that actually appear in domain texts, not just meta-level
# philosophical terms. Added at 4x weight in centroid construction.

FACE_VERNACULAR: dict[str, list[str]] = {
    # Only target faces that underperformed on the benchmark. Leaving
    # well-performing faces untouched avoids diluting their centroids with
    # broadly-shared vocabulary.
    "ethics": [
        "justice", "injustice", "fairness", "virtue",
        "sin", "duty", "obligation", "rights", "morality",
        "oppression", "liberation", "equality", "freedom",
        "righteous", "evil",
    ],
    "axiology": [
        "worth", "value", "standard", "criterion",
        "creed", "merit", "desirable", "esteem",
        "evaluation", "priority",
    ],
    "methodology": [
        "method", "procedure", "experiment", "observation", "hypothesis",
        "derivation", "theorem", "proposition", "inference",
        "technique",
    ],
}


# ---------------------------------------------------------------------------
# Disambiguation entries — polysemous triggers with sense-specific overrides
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
    "motion": [
        {"context_words": {"force", "body", "rest", "velocity", "acceleration", "uniform", "line", "state", "change", "impressed"},
         "target_face": "methodology", "seed_words": ["systematic", "deductive", "formal", "mathematical", "law"]},
    ],
    "magnitude": [
        {"context_words": {"tragedy", "action", "serious", "complete", "language", "ornament", "imitation", "artistic"},
         "target_face": "aesthetics", "seed_words": ["artistic", "dramatic", "theatrical", "magnitude", "sublime"]},
    ],
    "serious": [
        {"context_words": {"tragedy", "action", "complete", "magnitude", "language", "imitation", "artistic"},
         "target_face": "aesthetics", "seed_words": ["dramatic", "weighty", "solemn", "dignified", "gravitas"]},
    ],
    "meaning": [
        {"context_words": {"creed", "true", "nation", "dream", "equal", "content", "character", "judged"},
         "target_face": "semiotics", "seed_words": ["meaning", "signify", "symbol", "creed", "declaration"]},
    ],
    "creed": [
        {"context_words": {"meaning", "true", "nation", "dream", "equal", "created"},
         "target_face": "semiotics", "seed_words": ["creed", "declaration", "proclamation", "signify", "charter"]},
    ],
    # --- Ethics routing corrections (v0.7.3) ---
    # Field observations showed duty-bearing vocabulary systematically routing
    # to axiology rather than ethics because axiology's abstract worth-cloud
    # absorbs deontic terms. Context-gated redirects route to ethics when the
    # surrounding prose is morally framed. Principle 1 (specificity wins):
    # culpable/forbidden/virtue/duty/moral are more specific to ethics than
    # to axiology, so ethics should claim them when context is ethical.
    "duty": [
        {"context_words": {"moral", "obligation", "ought", "owe", "warrant", "responsibility",
                           "honor", "forbidden", "wrong", "ethical", "virtue", "right"},
         "target_face": "ethics",
         "seed_words": ["moral duty", "deontic obligation", "ethical responsibility",
                        "right action", "binding commandment"]},
    ],
    "owe": [
        {"context_words": {"duty", "moral", "obligation", "debt", "trust", "honor",
                           "responsibility", "pledge", "ethical", "bound", "warrant"},
         "target_face": "ethics",
         "seed_words": ["moral obligation", "duty owed", "ethical debt",
                        "responsibility bound", "honoring pledge"]},
    ],
    "moral": [
        {"context_words": {"duty", "obligation", "ethical", "ought", "right", "wrong",
                           "virtue", "vice", "responsibility", "forbidden", "owe", "honor"},
         "target_face": "ethics",
         "seed_words": ["moral duty", "ethical obligation", "right action",
                        "deontic principle", "virtue"]},
    ],
    "virtue": [
        {"context_words": {"moral", "ethical", "duty", "vice", "character", "honor",
                           "integrity", "good", "evil", "ought", "righteous"},
         "target_face": "ethics",
         "seed_words": ["moral virtue", "ethical character", "virtuous conduct",
                        "moral excellence", "righteous action"]},
    ],
    "culpable": [
        {"context_words": {"moral", "guilt", "fault", "blame", "responsibility", "wrong",
                           "accountable", "duty", "sin", "punishment", "ethical"},
         "target_face": "ethics",
         "seed_words": ["morally culpable", "blameworthy", "guilty wrongdoing",
                        "moral fault", "ethical violation"]},
    ],
    "forbidden": [
        {"context_words": {"moral", "wrong", "taboo", "unlawful", "prohibited",
                           "commandment", "sin", "ethical", "virtue", "duty"},
         "target_face": "ethics",
         "seed_words": ["morally forbidden", "prohibited conduct", "ethical prohibition",
                        "deontic taboo", "commandment forbids"]},
    ],
    "warrant": [
        {"context_words": {"moral", "duty", "obligation", "ought", "right",
                           "ethical", "responsibility", "trust", "owe"},
         "target_face": "ethics",
         "seed_words": ["moral warrant", "ethical justification", "right claim",
                        "deontic grounds", "rightful duty"]},
    ],
    "obligation": [
        {"context_words": {"duty", "moral", "owe", "ethical", "ought", "responsibility",
                           "bound", "commandment", "pledge", "warrant", "honor"},
         "target_face": "ethics",
         "seed_words": ["moral obligation", "deontic duty", "ethical responsibility",
                        "binding pledge", "owed duty"]},
    ],
    "ought": [
        {"context_words": {"moral", "duty", "obligation", "ethical", "right", "wrong",
                           "responsibility", "virtue", "good", "ought"},
         "target_face": "ethics",
         "seed_words": ["moral ought", "ethical imperative", "right action",
                        "deontic principle", "binding moral"]},
    ],
    # --- Teleology routing correction (v0.7.3) ---
    # Principle 2 (evaluative triad ordering): teleology grounds ethics grounds
    # axiology. "Purpose" currently splits between teleology and axiology;
    # when grounded in aim/goal/end/design context it should claim teleology.
    "purpose": [
        {"context_words": {"goal", "aim", "ultimate", "end", "intention", "design",
                           "function", "role", "destined", "teleological", "meant"},
         "target_face": "teleology",
         "seed_words": ["ultimate purpose", "telic goal", "intentional end",
                        "designed purpose", "destined aim"]},
    ],
}


# ---------------------------------------------------------------------------
# Curated phrases
# ---------------------------------------------------------------------------

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
    "particular universal", "static dynamic",
    "empirical rational", "certain provisional",
    "absolute relative", "quantitative qualitative",
    "immediate ultimate", "intentional emergent",
    "objective subjective", "surface deep",
    "deontological consequential", "agent act",
    "autonomous contextual", "sensory conceptual",
    "individual coordinated", "reactive proactive",
    "analytic synthetic", "deductive inductive",
    "explicit implicit", "syntactic semantic",
    "literal figurative", "author intent", "reader response",
    "systematic intuitive", "conservative exploratory",
]

COMPOSITIONAL_PHRASES: list[str] = [
    "first principles", "root cause", "mental model", "frame of reference",
    "chain of reasoning", "burden of proof", "thought experiment",
    "moral reasoning", "moral compass", "ethical framework", "value judgment",
    "decision making", "problem solving", "critical thinking",
    "abstract reasoning", "logical structure", "causal mechanism",
    "feedback loop", "emergent behavior", "self organization",
    "collective action", "game theory", "information theory",
    "signal processing", "pattern recognition", "knowledge representation",
    "natural language", "formal logic", "modal logic",
    "deductive reasoning", "inductive reasoning", "abductive reasoning",
    "analogical reasoning", "means and ends", "form and function",
    "cause and effect", "trial and error", "risk assessment",
    "cost benefit", "trade off", "paradigm shift", "cognitive bias",
    "confirmation bias", "selection bias", "base rate", "prior knowledge",
    "posterior probability", "null hypothesis", "statistical significance",
    "body of knowledge", "state of affairs", "point of view", "line of inquiry",
]

ALL_CURATED_PHRASES = QUESTION_PHRASES + POLE_PAIR_PHRASES + COMPOSITIONAL_PHRASES


# ---------------------------------------------------------------------------
# Text tokenization
# ---------------------------------------------------------------------------

def _tokenize_text(text: str) -> list[str]:
    """Simple whitespace tokenizer with punctuation removal, lowercased."""
    cleaned = text.lower()
    for ch in "?.,;:!'\"()[]{}—-–/":
        cleaned = cleaned.replace(ch, " ")
    return [w for w in cleaned.split() if len(w) > 1]


# ---------------------------------------------------------------------------
# Question stop words (shared with intent parser)
# ---------------------------------------------------------------------------

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

PHRASE_STOP_WORDS = {"and", "of", "the", "or", "a", "an", "in", "on", "to", "for"}


# ---------------------------------------------------------------------------
# BGE encoder
# ---------------------------------------------------------------------------

def load_bge():
    """Load the BGE-large-en-v1.5 sentence transformer."""
    from sentence_transformers import SentenceTransformer

    print(f"[BGE] Loading {BGE_MODEL_NAME} ...")
    model = SentenceTransformer(BGE_MODEL_NAME)
    print(f"[BGE] Model loaded. Max seq length: {model.max_seq_length}")
    return model


def encode(model, texts: list[str]) -> np.ndarray:
    """Encode a list of texts through BGE, returning L2-normalized float32 vectors."""
    vectors = model.encode(
        texts,
        batch_size=BGE_BATCH_SIZE,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=len(texts) > 500,
    )
    return vectors.astype(np.float32)


# ---------------------------------------------------------------------------
# Vocabulary assembly
# ---------------------------------------------------------------------------

def build_target_vocab() -> list[str]:
    """Assemble the target vocabulary to encode through BGE.

    Union of:
      - Top-K frequent English words from wordfreq
      - Face names
      - All pole synonym words (keys and values)
      - All words from axis-pole labels
      - All words from core questions
      - All words from domain replacements
      - All words from disambiguation seed_words and context_words
      - All words from curated phrases

    Returns a list sorted by wordfreq Zipf rank (most frequent first).
    """
    from wordfreq import top_n_list, zipf_frequency

    print(f"[VOCAB] Loading top {TOP_K_FREQUENT} frequent English words from wordfreq ...")
    frequent = top_n_list("en", TOP_K_FREQUENT, wordlist="large")
    frequent_set = set(frequent)
    print(f"[VOCAB] Got {len(frequent_set)} frequent words")

    domain_words: set[str] = set()

    # Face names
    for face in ALL_FACES:
        domain_words.add(face)

    # Face definitions: axis pole labels, core questions, domain replacements
    for face in ALL_FACES:
        defn = FACE_DEFINITIONS[face]
        domain_words.update(_tokenize_text(defn["core_question"]))
        domain_words.update(_tokenize_text(DOMAIN_REPLACEMENTS[face]))
        for key in ("x_axis_low", "x_axis_high", "y_axis_low", "y_axis_high"):
            domain_words.update(_tokenize_text(defn[key]))

    # Pole synonyms: both keys and values
    for pole_word, synonyms in POLE_SYNONYMS.items():
        domain_words.add(pole_word.lower())
        for syn in synonyms:
            domain_words.update(_tokenize_text(syn))

    # Face vernacular: object-level vocabulary per face
    for vern_list in FACE_VERNACULAR.values():
        for word in vern_list:
            domain_words.update(_tokenize_text(word))

    # Disambiguation: seed_words and context_words
    for trigger, entries in DISAMBIGUATION_ENTRIES.items():
        domain_words.add(trigger.lower())
        for entry in entries:
            domain_words.update(w.lower() for w in entry.get("context_words", set()))
            domain_words.update(w.lower() for w in entry.get("seed_words", []))

    # Phrase component words
    for phrase in ALL_CURATED_PHRASES:
        for w in _tokenize_text(phrase):
            if w not in PHRASE_STOP_WORDS:
                domain_words.add(w)

    # Question templates — every word in any template
    for template in BASE_QUESTIONS.values():
        for domain in DOMAIN_REPLACEMENTS.values():
            text = template.replace("{domain}", domain)
            for w in _tokenize_text(text):
                if w not in _Q_STOP_WORDS and len(w) > 2:
                    domain_words.add(w)

    # Clean: ensure lowercase, strip whitespace
    domain_words = {w.strip().lower() for w in domain_words if w.strip()}
    domain_words = {w for w in domain_words if all(c.isalpha() or c in "-" for c in w) and len(w) > 1}

    # Union with frequent
    all_words = frequent_set | domain_words

    # Sort: preserve wordfreq rank for frequent words; append domain-only words after
    # by their own Zipf frequency (descending)
    def sort_key(word: str) -> tuple[int, float]:
        # Primary: 0 if in wordfreq list, 1 otherwise (so frequent come first)
        primary = 0 if word in frequent_set else 1
        # Secondary: negative Zipf so higher frequency comes first
        try:
            zipf = zipf_frequency(word, "en")
        except Exception:
            zipf = 0.0
        return (primary, -zipf)

    sorted_words = sorted(all_words, key=sort_key)

    domain_only = domain_words - frequent_set
    print(f"[VOCAB] Domain-specific words not in top-{TOP_K_FREQUENT}: {len(domain_only)}")
    print(f"[VOCAB] Total vocabulary: {len(sorted_words)}")
    return sorted_words


# ---------------------------------------------------------------------------
# Face centroid construction (AUTHORED LAYERS ONLY)
# ---------------------------------------------------------------------------

def build_face_centroids(
    vocab: dict[str, int],
    vectors: np.ndarray,
    question_vecs: np.ndarray | None = None,
    question_weight: float = 0.4,
) -> np.ndarray:
    """Build a centroid vector for each of the 12 faces.

    Authored-layer centroid (weighted mean of word vectors):
      - Face name (2x)
      - Core question words (1x)
      - Sub-dimension labels (5x) — axis pole labels
      - Pole synonyms (3x)
      - Face vernacular (4x) — object-level domain vocabulary
      - Domain replacement words (2x)

    If question_vecs is provided (1728 BGE-encoded questions in face-blocks
    of 144), a per-face question centroid is computed and blended with the
    authored centroid:
        final = normalize((1 - qw) * authored + qw * question)
    where qw is the question_weight.

    Question centroids bring BGE-encoded philosophical vernacular from the
    construction questions into the face anchor without requiring explicit
    vocabulary curation.

    Returns: shape (12, embedding_dim), unit-normalized.
    """
    centroids = []
    embed_dim = vectors.shape[1]
    n_questions_per_face = 144  # from BASE_QUESTIONS

    for face_idx, face in enumerate(ALL_FACES):
        defn = FACE_DEFINITIONS[face]
        all_words: list[str] = []

        all_words.extend([face] * 2)
        all_words.extend(_tokenize_text(defn["core_question"]))

        for key in ("x_axis_low", "x_axis_high", "y_axis_low", "y_axis_high"):
            label_words = _tokenize_text(defn[key])
            all_words.extend(label_words * 5)

        for key in ("x_axis_low", "x_axis_high", "y_axis_low", "y_axis_high"):
            label = defn[key].lower()
            synonyms = POLE_SYNONYMS.get(label, [])
            for syn in synonyms:
                syn_words = _tokenize_text(syn)
                all_words.extend(syn_words * 3)

        # Face vernacular — object-level vocabulary (4x weight)
        for vern in FACE_VERNACULAR.get(face, []):
            all_words.extend(_tokenize_text(vern) * 4)

        all_words.extend(_tokenize_text(DOMAIN_REPLACEMENTS[face]) * 2)

        # Average vectors for words in vocab
        indices = [vocab[w] for w in all_words if w in vocab]
        if not indices:
            authored = np.zeros(embed_dim, dtype=np.float32)
        else:
            authored = np.mean(vectors[indices], axis=0)

        authored_norm = np.linalg.norm(authored)
        if authored_norm > 1e-9:
            authored_unit = authored / authored_norm
        else:
            authored_unit = np.zeros(embed_dim, dtype=np.float32)

        # Optional: blend with question centroid
        if question_vecs is not None:
            q_start = face_idx * n_questions_per_face
            q_end = q_start + n_questions_per_face
            face_q_vecs = question_vecs[q_start:q_end]  # (144, dim)
            question_centroid = np.mean(face_q_vecs, axis=0)
            q_norm = np.linalg.norm(question_centroid)
            if q_norm > 1e-9:
                question_unit = question_centroid / q_norm
            else:
                question_unit = np.zeros(embed_dim, dtype=np.float32)

            combined = (1.0 - question_weight) * authored_unit + question_weight * question_unit
            final_norm = np.linalg.norm(combined)
            if final_norm > 1e-9:
                centroid = combined / final_norm
            else:
                centroid = authored_unit
        else:
            centroid = authored_unit

        in_vocab = len(indices)
        blend_note = f", +question centroid (w={question_weight})" if question_vecs is not None else ""
        print(f"  {face:15s}: {len(all_words)} authored words, {in_vocab} in vocab{blend_note}")
        centroids.append(centroid.astype(np.float32))

    return np.stack(centroids)


# ---------------------------------------------------------------------------
# Axis direction vectors (24 total: 12 faces x 2 axes)
# ---------------------------------------------------------------------------

def build_axis_directions(
    vocab: dict[str, int],
    vectors: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build 24 axis direction vectors (high_pole - low_pole).

    For each face, for each axis (x=0, y=1):
      - low_pole = average BGE vector of (low_label + POLE_SYNONYMS)
      - high_pole = average BGE vector of (high_label + POLE_SYNONYMS)
      - direction = high_pole - low_pole, unit-normalized

    Also performs calibration: projects each pole onto its direction.

    Returns:
        directions: shape (24, embedding_dim) — unit-normalized
        cal_low: shape (24,) — expected projection of low pole
        cal_high: shape (24,) — expected projection of high pole
    """
    directions = []
    cal_low_arr = []
    cal_high_arr = []
    embed_dim = vectors.shape[1]

    def _avg(words: list[str]) -> np.ndarray:
        indices = [vocab[w] for w in words if w in vocab]
        if not indices:
            return np.zeros(embed_dim, dtype=np.float32)
        return np.mean(vectors[indices], axis=0)

    for face in ALL_FACES:
        defn = FACE_DEFINITIONS[face]
        for low_key, high_key in [
            ("x_axis_low", "x_axis_high"),
            ("y_axis_low", "y_axis_high"),
        ]:
            low_words = _tokenize_text(defn[low_key])
            high_words = _tokenize_text(defn[high_key])

            for w in list(low_words):
                if w in POLE_SYNONYMS:
                    low_words.extend(POLE_SYNONYMS[w])
            for w in list(high_words):
                if w in POLE_SYNONYMS:
                    high_words.extend(POLE_SYNONYMS[w])

            low_vec = _avg(low_words)
            high_vec = _avg(high_words)

            direction = high_vec - low_vec
            dir_norm = np.linalg.norm(direction)
            if dir_norm > 0:
                direction_unit = direction / dir_norm
            else:
                direction_unit = np.zeros(embed_dim, dtype=np.float32)

            proj_low = float(np.dot(low_vec, direction_unit))
            proj_high = float(np.dot(high_vec, direction_unit))

            directions.append(direction_unit.astype(np.float32))
            cal_low_arr.append(proj_low)
            cal_high_arr.append(proj_high)

    return (
        np.stack(directions),
        np.array(cal_low_arr, dtype=np.float32),
        np.array(cal_high_arr, dtype=np.float32),
    )


# ---------------------------------------------------------------------------
# Per-word artifact computation
# ---------------------------------------------------------------------------

def compute_discriminative_face_similarity(
    vectors: np.ndarray,
    centroids: np.ndarray,
) -> np.ndarray:
    """For each word: cosine(word, centroid[f]) - mean over faces."""
    print(f"[COMPUTE] Discriminative face similarity ({vectors.shape[0]} x 12) ...")
    # vectors are already L2-normalized from BGE
    raw_sim = vectors @ centroids.T  # (N, 12)
    mean_sim = np.mean(raw_sim, axis=1, keepdims=True)
    disc_sim = raw_sim - mean_sim
    print(f"[OK] Face similarity shape: {disc_sim.shape}, "
          f"range [{disc_sim.min():.4f}, {disc_sim.max():.4f}]")
    return disc_sim.astype(np.float32)


def compute_axis_projections(
    vectors: np.ndarray,
    directions: np.ndarray,
    cal_low: np.ndarray,
    cal_high: np.ndarray,
) -> np.ndarray:
    """For each word & axis: calibrated projection in [0, 1]."""
    print(f"[COMPUTE] Axis projections ({vectors.shape[0]} x 24) ...")
    raw_proj = vectors @ directions.T  # (N, 24)
    cal_range = cal_high - cal_low
    cal_range = np.where(np.abs(cal_range) < 1e-8, 1.0, cal_range)
    normalized = (raw_proj - cal_low[np.newaxis, :]) / cal_range[np.newaxis, :]
    clamped = np.clip(normalized, 0.0, 1.0)
    print(f"[OK] Axis projections shape: {clamped.shape}")
    return clamped.astype(np.float32)


def compute_idf_weights(words: list[str]) -> np.ndarray:
    """Compute IDF-like weights from wordfreq Zipf frequency.

    Zipf frequency: log10(count_per_billion). Range roughly [0, 8].
    Common words like "the" ~= 7.8; rare words ~= 2-3.

    IDF = 1 - (zipf / 8), clamped to [0, 1]. Rarer = higher weight.
    """
    from wordfreq import zipf_frequency

    print(f"[COMPUTE] IDF weights for {len(words)} words ...")
    zipfs = np.array([zipf_frequency(w, "en") for w in words], dtype=np.float32)
    # Clamp zipf to [0, 8] then invert
    zipfs_clamped = np.clip(zipfs, 0.0, 8.0)
    idf = 1.0 - (zipfs_clamped / 8.0)
    # Words not in wordfreq get zipf=0 -> idf=1 (treat as rare/informative)
    print(f"[OK] IDF range: [{idf.min():.4f}, {idf.max():.4f}], mean {idf.mean():.4f}")
    return idf.astype(np.float32)


# ---------------------------------------------------------------------------
# Disambiguation table
# ---------------------------------------------------------------------------

def compute_disambiguation_table(
    model,
    centroids: np.ndarray,
    directions: np.ndarray,
    cal_low: np.ndarray,
    cal_high: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Compute override face_sim and axis_proj for polysemous senses.

    For each sense with seed_words, encode the seed words as a BGE phrase
    (joined with spaces). Compute face_sim and axis_proj through the
    standard pipeline.
    """
    print(f"\n[DISAMBIG] Computing disambiguation table ...")

    embed_dim = centroids.shape[1]

    # Collect sense texts to encode in one batch
    sense_texts: list[str] = []
    sense_keys: list[tuple[str, int]] = []  # (trigger, entry_index)
    sense_is_suppress: list[bool] = []

    for trigger, entries in DISAMBIGUATION_ENTRIES.items():
        for entry_idx, entry in enumerate(entries):
            override_type = entry.get("override_type", "redirect")
            if override_type == "suppress":
                sense_texts.append("")
                sense_is_suppress.append(True)
            else:
                seed_text = " ".join(entry["seed_words"])
                sense_texts.append(seed_text)
                sense_is_suppress.append(False)
            sense_keys.append((trigger, entry_idx))

    # Encode all non-suppress senses
    non_suppress_texts = [t for t, supp in zip(sense_texts, sense_is_suppress) if not supp]
    if non_suppress_texts:
        non_suppress_vecs = encode(model, non_suppress_texts)
    else:
        non_suppress_vecs = np.zeros((0, embed_dim), dtype=np.float32)

    # Reassemble in original order
    sense_face_sims = []
    sense_axis_projs = []
    ns_idx = 0
    disambig_meta: dict[str, list[dict]] = {}
    sense_idx = 0

    cal_range = cal_high - cal_low
    cal_range = np.where(np.abs(cal_range) < 1e-8, 1.0, cal_range)

    for (trigger, entry_idx), supp in zip(sense_keys, sense_is_suppress):
        entry = DISAMBIGUATION_ENTRIES[trigger][entry_idx]
        context_words = sorted(entry["context_words"])
        threshold = 2

        if supp:
            sense_face_sims.append(np.zeros(12, dtype=np.float32))
            sense_axis_projs.append(np.full(24, 0.5, dtype=np.float32))
        else:
            sense_vec = non_suppress_vecs[ns_idx]
            ns_idx += 1
            # face_sim: cosine(sense, centroid) - mean — vectors are unit-normed
            raw_sim = sense_vec @ centroids.T
            disc_sim = raw_sim - np.mean(raw_sim)
            sense_face_sims.append(disc_sim.astype(np.float32))

            # axis_proj: calibrated projection
            raw_proj = sense_vec @ directions.T
            normalized = (raw_proj - cal_low) / cal_range
            clamped = np.clip(normalized, 0.0, 1.0)
            sense_axis_projs.append(clamped.astype(np.float32))

        meta_entry = {
            "context_words": context_words,
            "sense_idx": sense_idx,
            "override_type": entry.get("override_type", "redirect"),
            "threshold": threshold,
        }
        if "target_face" in entry:
            meta_entry["target_face"] = entry["target_face"]

        disambig_meta.setdefault(trigger, []).append(meta_entry)
        sense_idx += 1

    disambig_face_sim = (
        np.stack(sense_face_sims).astype(np.float32)
        if sense_face_sims
        else np.zeros((0, 12), dtype=np.float32)
    )
    disambig_axis_proj = (
        np.stack(sense_axis_projs).astype(np.float32)
        if sense_axis_projs
        else np.zeros((0, 24), dtype=np.float32)
    )

    print(f"[DISAMBIG] {len(DISAMBIGUATION_ENTRIES)} triggers, {sense_idx} senses, "
          f"shapes {disambig_face_sim.shape} / {disambig_axis_proj.shape}")
    return disambig_face_sim, disambig_axis_proj, disambig_meta


# ---------------------------------------------------------------------------
# Phrase embeddings
# ---------------------------------------------------------------------------

def compute_phrase_embeddings(
    model,
    centroids: np.ndarray,
    directions: np.ndarray,
    cal_low: np.ndarray,
    cal_high: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], dict[str, str]]:
    """Encode each curated phrase as a full sentence through BGE.

    Returns:
        phrase_face_sim: (N_phrases, 12)
        phrase_axis_proj: (N_phrases, 24)
        phrase_idf: (N_phrases,)
        phrase_keys: canonical phrase strings
        surface_to_canonical: surface -> canonical mapping
    """
    from wordfreq import zipf_frequency

    print(f"\n[PHRASES] Computing phrase embeddings through BGE ...")

    phrase_keys: list[str] = []
    surface_to_canonical: dict[str, str] = {}
    phrase_texts: list[str] = []

    seen: set[str] = set()
    for phrase in ALL_CURATED_PHRASES:
        surface_words = phrase.lower().split()
        canonical_words = []
        for w in surface_words:
            cleaned = "".join(c for c in w if c.isalpha())
            if cleaned and cleaned not in PHRASE_STOP_WORDS:
                canonical_words.append(cleaned)

        if len(canonical_words) < 2:
            continue

        canonical = " ".join(canonical_words)
        if canonical in seen:
            continue
        seen.add(canonical)

        surface = " ".join(surface_words)
        if surface != canonical:
            surface_to_canonical[surface] = canonical

        phrase_keys.append(canonical)
        # Encode the full phrase as a sentence — BGE handles composition
        phrase_texts.append(phrase)

    if not phrase_keys:
        empty = np.zeros((0, 12), dtype=np.float32)
        return empty, np.zeros((0, 24), dtype=np.float32), np.zeros(0, dtype=np.float32), [], {}

    phrase_vecs = encode(model, phrase_texts)  # (N, embed_dim)

    # face_sim
    raw_sim = phrase_vecs @ centroids.T
    mean_sim = np.mean(raw_sim, axis=1, keepdims=True)
    phrase_face_sim = (raw_sim - mean_sim).astype(np.float32)

    # axis_proj
    raw_proj = phrase_vecs @ directions.T
    cal_range = cal_high - cal_low
    cal_range = np.where(np.abs(cal_range) < 1e-8, 1.0, cal_range)
    normalized = (raw_proj - cal_low[np.newaxis, :]) / cal_range[np.newaxis, :]
    phrase_axis_proj = np.clip(normalized, 0.0, 1.0).astype(np.float32)

    # IDF: max component IDF (phrases are rarer than any single word)
    phrase_idfs = []
    for canonical in phrase_keys:
        idfs = []
        for w in canonical.split():
            zipf = zipf_frequency(w, "en")
            zipf_clamped = max(0.0, min(8.0, zipf))
            idfs.append(1.0 - zipf_clamped / 8.0)
        phrase_idfs.append(max(idfs) if idfs else 0.9)
    phrase_idf = np.array(phrase_idfs, dtype=np.float32)

    print(f"[PHRASES] {len(phrase_keys)} phrases encoded, "
          f"{len(surface_to_canonical)} surface mappings")
    return phrase_face_sim, phrase_axis_proj, phrase_idf, phrase_keys, surface_to_canonical


# ---------------------------------------------------------------------------
# Phase-aware face weighting
# ---------------------------------------------------------------------------

PHASE_NAMES = ["comprehension", "evaluation", "application"]

PHASE_FACES: dict[str, list[str]] = {
    "comprehension": [f for f in ALL_FACES if FACE_PHASES[f] == "comprehension"],
    "evaluation": [f for f in ALL_FACES if FACE_PHASES[f] == "evaluation"],
    "application": [f for f in ALL_FACES if FACE_PHASES[f] == "application"],
}


def build_phase_centroids(centroids: np.ndarray) -> np.ndarray:
    """Build phase centroid vectors by averaging face centroids per phase."""
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
        print(f"  {phase_name:15s}: {len(faces_in_phase)} faces")
    return np.stack(phase_centroids).astype(np.float32)


def compute_word_phase_sim(vectors: np.ndarray, phase_centroids: np.ndarray) -> np.ndarray:
    """Per-word cosine similarity to each phase centroid (vectors already unit-normed)."""
    print(f"[PHASE] Computing word-phase similarity ({vectors.shape[0]} x 3) ...")
    sim = vectors @ phase_centroids.T
    return sim.astype(np.float32)


# ---------------------------------------------------------------------------
# Question position maps
# ---------------------------------------------------------------------------

def encode_all_questions(model) -> np.ndarray:
    """Encode the 1728 construction questions as full sentences through BGE.

    Returns: (1728, embedding_dim) — face-major ordering (face 0's 144
    questions, then face 1's 144, etc.) matching ALL_FACES and
    BASE_QUESTIONS key order.
    """
    question_positions = list(BASE_QUESTIONS.keys())
    question_texts: list[str] = []
    for face in ALL_FACES:
        domain = DOMAIN_REPLACEMENTS[face]
        for (x, y) in question_positions:
            template = BASE_QUESTIONS[(x, y)]
            question_texts.append(template.replace("{domain}", domain))
    print(f"[QUESTIONS] Encoding {len(question_texts)} questions through BGE ...")
    return encode(model, question_texts)


def compute_question_position_maps(
    vectors: np.ndarray,
    q_vecs: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, list[tuple[int, int]]]:
    """For each word and each face, find best-matching question position.

    Consumes pre-computed question vectors from encode_all_questions().
    """
    print(f"\n[QUESTIONS] Computing per-face question position maps ...")

    question_positions = list(BASE_QUESTIONS.keys())
    n_questions = len(question_positions)
    n_words = vectors.shape[0]

    word_question_x = np.zeros((n_words, 12), dtype=np.int8)
    word_question_y = np.zeros((n_words, 12), dtype=np.int8)

    for face_idx in range(12):
        face_q_start = face_idx * n_questions
        face_q_end = face_q_start + n_questions
        face_q_vecs = q_vecs[face_q_start:face_q_end]

        similarities = vectors @ face_q_vecs.T  # (N, 144)
        best_idx = similarities.argmax(axis=1)
        for i, idx in enumerate(best_idx):
            pos = question_positions[idx]
            word_question_x[i, face_idx] = pos[0]
            word_question_y[i, face_idx] = pos[1]

        print(f"  {ALL_FACES[face_idx]:15s}: best-match x=[{word_question_x[:, face_idx].min()},"
              f" {word_question_x[:, face_idx].max()}], y=[{word_question_y[:, face_idx].min()},"
              f" {word_question_y[:, face_idx].max()}]")

    return word_question_x, word_question_y, question_positions


# ---------------------------------------------------------------------------
# Save / reports
# ---------------------------------------------------------------------------

def save_artifacts(
    vocab: dict[str, int],
    disc_face_sim: np.ndarray,
    axis_proj: np.ndarray,
    idf_weights: np.ndarray,
    disambig_face_sim: np.ndarray,
    disambig_axis_proj: np.ndarray,
    disambig_meta: dict,
    phrase_keys: list[str],
    surface_to_canonical: dict[str, str],
    phase_centroids: np.ndarray,
    word_phase_sim: np.ndarray,
    word_question_x: np.ndarray,
    word_question_y: np.ndarray,
    vector_source: str,
) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    npz_dict = {
        "face_sim": disc_face_sim,
        "axis_proj": axis_proj,
        "idf": idf_weights,
        "faces": np.array(ALL_FACES),
        "disambig_face_sim": disambig_face_sim,
        "disambig_axis_proj": disambig_axis_proj,
        "phase_centroids": phase_centroids,
        "word_phase_sim": word_phase_sim,
        "word_question_x": word_question_x,
        "word_question_y": word_question_y,
    }
    np.savez_compressed(str(NPZ_PATH), **npz_dict)
    print(f"[SAVE] {NPZ_PATH} ({NPZ_PATH.stat().st_size / 1024:.1f} KB)")

    vocab_data = {
        "words": vocab,
        "disambiguation": disambig_meta,
        "phrases": phrase_keys,
        "surface_to_canonical": surface_to_canonical,
        "phase_names": PHASE_NAMES,
        "vector_source": vector_source,
    }
    with open(str(VOCAB_PATH), "w", encoding="utf-8") as f:
        json.dump(vocab_data, f)
    print(f"[SAVE] {VOCAB_PATH} ({VOCAB_PATH.stat().st_size / 1024:.1f} KB)")


def report_top_words(vocab: dict[str, int], disc_face_sim: np.ndarray, top_n: int = 10) -> None:
    idx_to_word = {i: w for w, i in vocab.items()}
    print(f"\n{'='*70}\nTop {top_n} discriminative words per face\n{'='*70}")
    for col_idx, face in enumerate(ALL_FACES):
        scores = disc_face_sim[:, col_idx]
        top_indices = np.argsort(scores)[::-1][:top_n]
        top_words = [(idx_to_word.get(int(i), "?"), float(scores[i])) for i in top_indices]
        words_str = ", ".join(f"{w}({s:.3f})" for w, s in top_words)
        print(f"\n{face}:\n  {words_str}")


def report_pole_self_test(vocab: dict[str, int], axis_proj: np.ndarray) -> bool:
    """Each pole's own words should project toward its side."""
    print(f"\n{'='*70}\nPole self-test (low < 0.3, high > 0.7)\n{'='*70}")
    all_pass = True
    axis_idx = 0
    for face in ALL_FACES:
        defn = FACE_DEFINITIONS[face]
        for low_key, high_key in [("x_axis_low", "x_axis_high"), ("y_axis_low", "y_axis_high")]:
            low_words = _tokenize_text(defn[low_key])
            high_words = _tokenize_text(defn[high_key])
            for w in list(low_words):
                if w in POLE_SYNONYMS:
                    low_words.extend(POLE_SYNONYMS[w])
            for w in list(high_words):
                if w in POLE_SYNONYMS:
                    high_words.extend(POLE_SYNONYMS[w])

            low_indices = [vocab[w] for w in low_words if w in vocab]
            high_indices = [vocab[w] for w in high_words if w in vocab]

            low_proj = float(np.mean(axis_proj[low_indices, axis_idx])) if low_indices else 0.5
            high_proj = float(np.mean(axis_proj[high_indices, axis_idx])) if high_indices else 0.5

            low_ok = low_proj < 0.3
            high_ok = high_proj > 0.7
            if not (low_ok and high_ok):
                all_pass = False
            status = "PASS" if (low_ok and high_ok) else "FAIL"
            print(f"  {face:15s} {defn[low_key]:20s} -> {low_proj:.3f}"
                  f"  |  {defn[high_key]:20s} -> {high_proj:.3f}  [{status}]")
            axis_idx += 1
    print(f"\n{'='*70}\nPole self-test: {'ALL PASS' if all_pass else 'SOME FAILURES'}\n{'='*70}")
    return all_pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 70)
    print("Geometric Semantic Bridge Builder — BGE edition")
    print("=" * 70)

    # Step 1: Load BGE
    model = load_bge()
    vector_source = f"BGE (BAAI/bge-large-en-v1.5, native {BGE_DIM}d)"
    print(f"\n[VECTORS] Active vector source: {vector_source}")

    # Step 2: Build target vocab (frequent + all domain/pole/question/phrase words)
    words = build_target_vocab()
    vocab = {w: i for i, w in enumerate(words)}

    # Step 3: Encode vocabulary through BGE
    print(f"\n[BGE] Encoding {len(words)} words ...")
    vectors = encode(model, words)  # (N, 1024), unit-normalized
    print(f"[BGE] Encoded vectors shape: {vectors.shape}")

    # Step 3b: Encode 1728 construction questions as full sentences.
    # Needed early so face centroids can blend in per-face question centroids.
    q_vecs = encode_all_questions(model)

    # Step 4: Build face centroids — authored layers + FACE_VERNACULAR.
    # Question-centroid blend is disabled: the 1728 questions share identical
    # template structure (only {domain} differs), so per-face averages collapse
    # toward a common mean rather than sharpening face distinctions.
    print(f"\n[BUILD] Computing face centroids (authored + FACE_VERNACULAR) ...")
    centroids = build_face_centroids(vocab, vectors, question_vecs=None)

    # Step 5: Build axis direction vectors
    print(f"\n[BUILD] Computing 24 axis direction vectors ...")
    directions, cal_low, cal_high = build_axis_directions(vocab, vectors)

    # Step 6: Per-word artifacts
    print(f"\n[BUILD] Computing per-word artifacts ...")
    disc_face_sim = compute_discriminative_face_similarity(vectors, centroids)
    axis_proj = compute_axis_projections(vectors, directions, cal_low, cal_high)
    idf_weights = compute_idf_weights(words)

    # Step 7: Disambiguation table (encoded through BGE)
    disambig_face_sim, disambig_axis_proj, disambig_meta = compute_disambiguation_table(
        model, centroids, directions, cal_low, cal_high,
    )

    # Step 8: Phrase embeddings (encoded through BGE)
    phrase_face_sim, phrase_axis_proj, phrase_idf, phrase_keys, surface_to_canonical = (
        compute_phrase_embeddings(model, centroids, directions, cal_low, cal_high)
    )

    # Step 9: Extend per-word arrays with phrase rows
    if phrase_keys:
        base_size = len(vocab)
        disc_face_sim = np.concatenate([disc_face_sim, phrase_face_sim], axis=0)
        axis_proj = np.concatenate([axis_proj, phrase_axis_proj], axis=0)
        idf_weights = np.concatenate([idf_weights, phrase_idf], axis=0)
        for local_idx, canonical in enumerate(phrase_keys):
            vocab[canonical] = base_size + local_idx
        print(f"[EXTEND] Appended {len(phrase_keys)} phrase rows, "
              f"new array sizes: face_sim={disc_face_sim.shape}")

    # Step 10: Phase centroids + word-phase similarity
    phase_centroids = build_phase_centroids(centroids)
    word_phase_sim = compute_word_phase_sim(vectors, phase_centroids)
    if phrase_keys:
        phrase_phase_pad = np.zeros((len(phrase_keys), 3), dtype=np.float32)
        word_phase_sim = np.concatenate([word_phase_sim, phrase_phase_pad], axis=0)

    # Step 11: Question position maps — reuses q_vecs from Step 3b
    word_question_x, word_question_y, _ = compute_question_position_maps(vectors, q_vecs)
    if phrase_keys:
        phrase_qx_pad = np.full((len(phrase_keys), 12), 5, dtype=np.int8)
        phrase_qy_pad = np.full((len(phrase_keys), 12), 5, dtype=np.int8)
        word_question_x = np.concatenate([word_question_x, phrase_qx_pad], axis=0)
        word_question_y = np.concatenate([word_question_y, phrase_qy_pad], axis=0)

    # Step 12: Save
    print(f"\n[SAVE] Saving artifacts ...")
    save_artifacts(
        vocab, disc_face_sim, axis_proj, idf_weights,
        disambig_face_sim, disambig_axis_proj, disambig_meta,
        phrase_keys, surface_to_canonical,
        phase_centroids, word_phase_sim,
        word_question_x, word_question_y,
        vector_source,
    )

    # Step 13: Reports
    report_top_words(vocab, disc_face_sim)
    pole_ok = report_pole_self_test(vocab, axis_proj)

    print(f"\n{'='*70}")
    print(f"Vector source:        {vector_source}")
    print(f"Vocabulary size:      {len(vocab)} (words + phrases)")
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
