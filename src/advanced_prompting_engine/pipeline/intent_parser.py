"""Stage 1 — Intent Parser: natural language → partial coordinate.

Authoritative source: Spec 06 §1.
Two-tier matching: tag overlap (60%) + TF-IDF cosine similarity (40%).
Bypassed entirely if input is a pre-formed coordinate dict.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.canonical import _stem
from advanced_prompting_engine.graph.schema import ALL_BRANCHES, PipelineState

MATCH_THRESHOLD = 0.15

# Stop words for tokenization (same as tag derivation)
_STOP_WORDS = frozenset({
    "what", "is", "the", "of", "a", "an", "at", "in", "from", "how", "does",
    "do", "that", "this", "which", "for", "to", "and", "or", "by", "with",
    "its", "are", "be", "into", "as", "when", "where", "can", "has", "have",
    "through", "between", "within", "upon", "along", "across",
})


class IntentParser:
    """Stage 1: Map natural language intent to partial grid coordinates."""

    def __init__(self, tfidf_cache, query_layer):
        self._tfidf = tfidf_cache
        self._query = query_layer

    def execute(self, state: PipelineState):
        raw = state.raw_input

        # Bypass: pre-formed coordinate dict
        if isinstance(raw, dict):
            self._validate_coordinate(raw)
            state.partial_coordinate = raw
            return

        # Natural language path
        intent = str(raw).strip()
        if not intent:
            state.partial_coordinate = {b: None for b in ALL_BRANCHES}
            return

        tokens = self._tokenize(intent)
        tfidf_results = self._tfidf.query(intent)

        # Group TF-IDF results by branch
        tfidf_by_branch: dict[str, list[tuple[str, float]]] = {b: [] for b in ALL_BRANCHES}
        for construct_id, sim in tfidf_results:
            parts = construct_id.split(".")
            if len(parts) >= 2:
                branch = parts[0]
                if branch in tfidf_by_branch:
                    tfidf_by_branch[branch].append((construct_id, sim))

        # Track all matched tokens for weight computation
        all_matched_tokens: list[str] = []
        branch_matched_tokens: dict[str, list[str]] = {b: [] for b in ALL_BRANCHES}

        partial: dict[str, dict | None] = {}

        for branch in ALL_BRANCHES:
            best_id = None
            best_score = 0.0
            best_tag_score = 0.0
            best_tfidf_score = 0.0

            constructs = self._query.list_constructs(branch)
            for c in constructs:
                # Tag score
                c_tags = set(c.get("tags", []))
                if not c_tags:
                    tag_score = 0.0
                else:
                    overlap = len(tokens & c_tags)
                    tag_score = overlap / len(c_tags)

                # TF-IDF score
                tfidf_score = 0.0
                for cid, sim in tfidf_by_branch[branch]:
                    if cid == c["id"]:
                        tfidf_score = sim
                        break

                combined = tag_score * 0.6 + tfidf_score * 0.4

                if combined > best_score:
                    best_score = combined
                    best_id = c["id"]
                    best_tag_score = tag_score
                    best_tfidf_score = tfidf_score

            if best_score >= MATCH_THRESHOLD and best_id is not None:
                # Parse position from ID
                pos_part = best_id.split(".")[1]
                x, y = map(int, pos_part.split("_"))

                # Track matched tokens for this branch
                c_data = self._query.get_construct_by_id(best_id)
                if c_data:
                    c_tags = set(c_data.get("tags", []))
                    matched = list(tokens & c_tags)
                    branch_matched_tokens[branch] = matched
                    all_matched_tokens.extend(matched)

                partial[branch] = {
                    "x": x,
                    "y": y,
                    "weight": 0.0,  # computed below
                    "confidence": best_score,
                }
            else:
                partial[branch] = None

        # Compute weights: token emphasis ratio
        total_matched = max(len(all_matched_tokens), 1)
        for branch in ALL_BRANCHES:
            if partial[branch] is not None:
                branch_count = len(branch_matched_tokens[branch])
                partial[branch]["weight"] = max(0.1, branch_count / total_matched)

        state.partial_coordinate = partial

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize and stem to match the stemmed tags in canonical constructs."""
        words = text.lower().replace("?", "").replace(",", "").replace("'", "").split()
        return {_stem(w) for w in words if w not in _STOP_WORDS and len(w) > 1}

    def _validate_coordinate(self, coord: dict):
        for branch in ALL_BRANCHES:
            if branch not in coord:
                raise ValueError(f"Missing branch {branch!r} in coordinate")
            entry = coord[branch]
            if entry is not None:
                if not isinstance(entry, dict):
                    raise ValueError(f"Branch {branch!r} entry must be dict or None")
                for key in ("x", "y", "weight"):
                    if key not in entry:
                        raise ValueError(f"Branch {branch!r} missing {key!r}")
                if not (0 <= entry["x"] <= 9 and 0 <= entry["y"] <= 9):
                    raise ValueError(f"Branch {branch!r} position ({entry['x']}, {entry['y']}) out of range")
