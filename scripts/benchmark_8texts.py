#!/usr/bin/env python3
"""8-text literary benchmark for the semantic bridge.

Tests face relevance detection across 8 canonical literary/philosophical texts.
Each text has 2-3 expected faces that should appear in the top 6.

Scoring: each expected face found in top 6 = 1 point. Max 20 points.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project source is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from advanced_prompting_engine.math.semantic import GeometricBridge
from advanced_prompting_engine.graph.schema import ALL_FACES


# ---------------------------------------------------------------------------
# 8 benchmark texts with expected top faces
# ---------------------------------------------------------------------------

BENCHMARK_TEXTS: list[dict] = [
    {
        "name": "Shakespeare (Hamlet — 'To be or not to be')",
        "text": (
            "To be, or not to be, that is the question: "
            "Whether 'tis nobler in the mind to suffer "
            "The slings and arrows of outrageous fortune, "
            "Or to take arms against a sea of troubles, "
            "And by opposing end them. To die: to sleep; "
            "No more; and by a sleep to say we end "
            "The heart-ache and the thousand natural shocks "
            "That flesh is heir to, 'tis a consummation "
            "Devoutly to be wish'd."
        ),
        "expected_faces": ["ontology", "ethics", "phenomenology"],
    },
    {
        "name": "Genesis (Creation — 'In the beginning')",
        "text": (
            "In the beginning God created the heaven and the earth. "
            "And the earth was without form, and void; and darkness was "
            "upon the face of the deep. And the Spirit of God moved upon "
            "the face of the waters. And God said, Let there be light: "
            "and there was light. And God saw the light, that it was good: "
            "and God divided the light from the darkness."
        ),
        "expected_faces": ["ontology", "teleology"],
    },
    {
        "name": "Marx (Communist Manifesto — opening)",
        "text": (
            "The history of all hitherto existing society is the history "
            "of class struggles. Freeman and slave, patrician and plebeian, "
            "lord and serf, guild-master and journeyman, in a word, "
            "oppressor and oppressed, stood in constant opposition to one "
            "another, carried on an uninterrupted, now hidden, now open fight, "
            "a fight that each time ended, either in a revolutionary "
            "reconstitution of society at large, or in the common ruin "
            "of the contending classes."
        ),
        "expected_faces": ["praxeology", "ethics", "axiology"],
    },
    {
        "name": "MLK (I Have a Dream — 'I have a dream')",
        "text": (
            "I have a dream that one day this nation will rise up and live "
            "out the true meaning of its creed: We hold these truths to be "
            "self-evident, that all men are created equal. I have a dream "
            "that one day on the red hills of Georgia, the sons of former "
            "slaves and the sons of former slave owners will be able to sit "
            "down together at the table of brotherhood."
        ),
        "expected_faces": ["ethics", "axiology", "semiotics"],
    },
    {
        "name": "Newton (Principia — Laws of Motion)",
        "text": (
            "Every body perseveres in its state of rest, or of uniform "
            "motion in a right line, unless it is compelled to change that "
            "state by forces impressed thereon. The alteration of motion is "
            "ever proportional to the motive force impressed; and is made "
            "in the direction of the right line in which that force is "
            "impressed. To every action there is always opposed an equal "
            "reaction."
        ),
        "expected_faces": ["methodology", "ontology"],
    },
    {
        "name": "Aristotle (Poetics — definition of tragedy)",
        "text": (
            "Tragedy, then, is an imitation of an action that is serious, "
            "complete, and of a certain magnitude; in language embellished "
            "with each kind of artistic ornament, the several kinds being "
            "found in separate parts of the play; in the form of action, "
            "not of narrative; through pity and fear effecting the proper "
            "purgation of these emotions."
        ),
        "expected_faces": ["aesthetics", "phenomenology"],
    },
    {
        "name": "Tao Te Ching (Chapter 1 — 'The Tao that can be told')",
        "text": (
            "The Tao that can be told is not the eternal Tao. "
            "The name that can be named is not the eternal name. "
            "The nameless is the beginning of heaven and earth. "
            "The named is the mother of ten thousand things. "
            "Ever desireless, one can see the mystery. "
            "Ever desiring, one can see the manifestations."
        ),
        "expected_faces": ["ontology", "epistemology", "hermeneutics"],
    },
    {
        "name": "Descartes (Meditations — 'Cogito ergo sum')",
        "text": (
            "But I have convinced myself that there is absolutely nothing "
            "in the world, no sky, no earth, no minds, no bodies. Does it "
            "now follow that I too do not exist? No: if I convinced myself "
            "of something then I certainly existed. But there is a deceiver "
            "of supreme power and cunning who is deliberately and constantly "
            "deceiving me. In that case I too undoubtedly exist, if he is "
            "deceiving me. I think, therefore I am."
        ),
        "expected_faces": ["epistemology", "ontology"],
    },
]


def run_benchmark() -> int:
    """Run the 8-text benchmark and return score out of 20."""
    bridge = GeometricBridge()
    bridge.load()

    if not bridge.is_loaded:
        print("ERROR: GeometricBridge failed to load. Cannot run benchmark.")
        return 0

    # Report vector source if available
    vocab_path = (
        Path(__file__).resolve().parent.parent
        / "src" / "advanced_prompting_engine" / "data" / "semantic_vocab.json"
    )
    try:
        import json
        with open(vocab_path) as f:
            vocab_data = json.load(f)
        vector_source = vocab_data.get("vector_source", "unknown")
        print(f"Vector source: {vector_source}")
    except Exception:
        print("Vector source: unknown")

    total_score = 0
    total_expected = 0
    print(f"\n{'='*70}")
    print("8-Text Literary Benchmark")
    print(f"{'='*70}")

    for entry in BENCHMARK_TEXTS:
        name = entry["name"]
        text = entry["text"]
        expected = entry["expected_faces"]

        # Tokenize same way as intent parser
        cleaned = text.lower()
        for ch in "?.,;:!'\"()[]{}—-–/":
            cleaned = cleaned.replace(ch, " ")
        tokens = [w for w in cleaned.split() if len(w) > 1]

        # Get face relevance scores
        scores = bridge.face_relevance(tokens)

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top6_faces = [f for f, s in ranked[:6]]

        hits = [f for f in expected if f in top6_faces]
        misses = [f for f in expected if f not in top6_faces]
        score = len(hits)
        total_score += score
        total_expected += len(expected)

        print(f"\n{name}")
        print(f"  Expected: {', '.join(expected)}")
        print(f"  Top 6:    {', '.join(top6_faces)}")
        print(f"  Score:    {score}/{len(expected)}", end="")
        if misses:
            # Show where misses ranked
            miss_info = []
            for m in misses:
                rank = [f for f, _ in ranked].index(m) + 1
                miss_info.append(f"{m}(#{rank})")
            print(f"  MISS: {', '.join(miss_info)}")
        else:
            print("  ALL HIT")

    print(f"\n{'='*70}")
    print(f"TOTAL SCORE: {total_score}/{total_expected}")
    print(f"{'='*70}")
    return total_score


if __name__ == "__main__":
    score = run_benchmark()
    sys.exit(0 if score >= 15 else 1)
