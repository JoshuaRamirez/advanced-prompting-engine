#!/usr/bin/env python3
"""Propose pole-synonym expansions using WordNet (and optionally Moby).

Emits a JSON proposals file for human review. Does not modify
POLE_SYNONYMS in build_semantic_bridge.py — the human curates accepted
additions and commits them manually.

For each pole word in POLE_SYNONYMS:
  S = WordNet synonyms (same POS, multi-synset union)
  A = WordNet antonyms (across synsets)
  candidates = (S minus A) minus already_present
  filtered = [c for c in candidates if zipf_freq(c) >= MIN_ZIPF]
  emit pole_word, existing, proposed with sources and Zipf scores

Usage:
    pip install -e .[build]   # one-time: get nltk + wordfreq
    python -m nltk.downloader wordnet omw-1.4
    python3 scripts/expand_pole_synonyms.py
    # -> writes Documentation/Temporary/Execution/pole_synonym_proposals.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build_semantic_bridge import POLE_SYNONYMS  # noqa: E402

# Configuration
MIN_ZIPF = 2.5       # Drop words rarer than this (roughly top 50K English)
MAX_CANDIDATES = 12  # Top-N proposals per pole

OUTPUT_PATH = (
    PROJECT_ROOT
    / "Documentation"
    / "Temporary"
    / "Execution"
    / "pole_synonym_proposals.json"
)


def _load_wordnet():
    """Load NLTK WordNet, printing a helpful message if not installed."""
    try:
        from nltk.corpus import wordnet as wn
        # Trigger load to force LookupError if data missing
        _ = wn.synsets("test")
        return wn
    except LookupError:
        print("[ERROR] WordNet data not downloaded. Run:")
        print("        python -m nltk.downloader wordnet omw-1.4")
        sys.exit(1)
    except ImportError:
        print("[ERROR] nltk not installed. Run: pip install -e .[build]")
        sys.exit(1)


def _wordnet_synonyms_and_antonyms(wn, word: str) -> tuple[set[str], set[str]]:
    """Return (synonyms, antonyms) for a word across all synsets."""
    synonyms: set[str] = set()
    antonyms: set[str] = set()
    for syn in wn.synsets(word):
        for lemma in syn.lemmas():
            name = lemma.name().lower().replace("_", " ")
            if name != word:
                synonyms.add(name)
            for ant in lemma.antonyms():
                antonyms.add(ant.name().lower().replace("_", " "))
    return synonyms, antonyms


def propose():
    from wordfreq import zipf_frequency

    wn = _load_wordnet()

    proposals: dict[str, dict] = {}

    for pole_word, existing_synonyms in POLE_SYNONYMS.items():
        existing = {pole_word.lower(), *{s.lower() for s in existing_synonyms}}

        # Collect candidates from WordNet
        syns, ants = _wordnet_synonyms_and_antonyms(wn, pole_word)

        # Candidates = synonyms minus antonyms minus already present
        candidates = (syns - ants) - existing

        # Filter single-word (we avoid multi-word phrases as pole synonyms for now)
        # and drop words below MIN_ZIPF
        scored: list[tuple[str, float]] = []
        for cand in candidates:
            if " " in cand:
                continue  # skip multi-word phrases
            if not all(c.isalpha() or c == "-" for c in cand):
                continue
            zipf = zipf_frequency(cand, "en")
            if zipf < MIN_ZIPF:
                continue
            scored.append((cand, zipf))

        # Sort by Zipf descending (more frequent = more useful)
        scored.sort(key=lambda x: -x[1])
        top = scored[:MAX_CANDIDATES]

        proposals[pole_word] = {
            "existing": list(existing_synonyms),
            "proposed": [
                {"word": w, "zipf": round(z, 2), "source": "wordnet"}
                for w, z in top
            ],
            "wordnet_antonyms": sorted(ants - existing)[:10],
        }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "description": (
                    "Pole-synonym expansion proposals. Review and manually add accepted "
                    "entries to POLE_SYNONYMS in scripts/build_semantic_bridge.py."
                ),
                "config": {
                    "min_zipf": MIN_ZIPF,
                    "max_candidates_per_pole": MAX_CANDIDATES,
                    "source": "WordNet (NLTK) — typed synonyms/antonyms",
                },
                "proposals": proposals,
            },
            f,
            indent=2,
            sort_keys=False,
        )

    print(f"[OK] Proposals written to {OUTPUT_PATH}")
    print(f"[OK] {len(proposals)} poles processed")
    total = sum(len(p["proposed"]) for p in proposals.values())
    print(f"[OK] {total} total candidate additions proposed")


if __name__ == "__main__":
    propose()
