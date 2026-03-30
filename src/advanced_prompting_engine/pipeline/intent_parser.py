"""Stage 1 — Intent Parser: natural language → partial coordinate.

Authoritative source: Spec 06 §1.
Two-phase matching:
  Phase 1: Determine branch relevance by matching intent against branch
           core questions and domain terms.
  Phase 2: Within each branch, find the best grid position via tag overlap
           and per-branch TF-IDF.
"""

from __future__ import annotations

from advanced_prompting_engine.graph.canonical import _stem
from advanced_prompting_engine.graph.schema import (
    ALL_BRANCHES,
    BRANCH_DEFINITIONS,
    DOMAIN_REPLACEMENTS,
    PipelineState,
)

MATCH_THRESHOLD = 0.10  # lowered — two-phase matching is more selective

# Stop words for tokenization (same as tag derivation)
_STOP_WORDS = frozenset({
    "what", "is", "the", "of", "a", "an", "at", "in", "from", "how", "does",
    "do", "that", "this", "which", "for", "to", "and", "or", "by", "with",
    "its", "are", "be", "into", "as", "when", "where", "can", "has", "have",
    "through", "between", "within", "upon", "along", "across",
})

# Branch semantic keywords — terms that signal relevance to a specific branch
# beyond just the branch name. These are domain-specific, not structural.
_BRANCH_KEYWORDS: dict[str, set[str]] = {
    "ontology": {_stem(w) for w in ["entity", "exist", "real", "being", "object", "structure", "category", "relationship", "boundary", "hierarchy", "component", "thing", "nature", "essence"]},
    "epistemology": {_stem(w) for w in ["know", "truth", "verify", "evidence", "proof", "belief", "justify", "valid", "certain", "empirical", "rational", "knowledge", "fact", "correct"]},
    "axiology": {_stem(w) for w in ["value", "ethic", "moral", "aesthetic", "worth", "good", "quality", "trust", "integrity", "fair", "right", "maintain", "evaluate", "criteria"]},
    "teleology": {_stem(w) for w in ["purpose", "goal", "end", "aim", "target", "outcome", "result", "intent", "direct", "achieve", "objective", "why", "reason", "cause"]},
    "phenomenology": {_stem(w) for w in ["experience", "conscious", "perceive", "feel", "aware", "sense", "interact", "user", "gesture", "interface", "subjective", "represent", "present", "flow"]},
    "praxeology": {_stem(w) for w in ["action", "behavior", "act", "do", "perform", "execute", "practice", "delegate", "invoke", "response", "initiative", "coordinate", "react", "operate"]},
    "methodology": {_stem(w) for w in ["method", "process", "system", "approach", "technique", "procedure", "workflow", "framework", "construct", "design", "build", "test", "analyze", "iterate"]},
    "semiotics": {_stem(w) for w in ["sign", "signal", "meaning", "communicate", "message", "encode", "decode", "symbol", "semantic", "syntax", "format", "payload", "convention", "interpret"]},
    "hermeneutics": {_stem(w) for w in ["interpret", "understand", "ambiguity", "context", "read", "translate", "clarify", "meaning", "frame", "perspective", "narrative", "exegesis", "text", "nuance"]},
    "heuristics": {_stem(w) for w in ["strategy", "heuristic", "solve", "problem", "adapt", "fallback", "pragmatic", "rule", "shortcut", "approximate", "trial", "error", "explore", "robust"]},
}


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

        # --- Phase 1: Branch relevance ---
        # Score each branch by how many domain-specific keywords match
        branch_relevance: dict[str, float] = {}
        for branch in ALL_BRANCHES:
            keywords = _BRANCH_KEYWORDS.get(branch, set())
            branch_name_stem = _stem(branch)
            domain_stems = {_stem(w) for w in DOMAIN_REPLACEMENTS[branch].split()}

            # Keyword overlap
            keyword_overlap = len(tokens & keywords)
            # Branch name match
            name_match = 1.0 if branch_name_stem in tokens else 0.0
            # Domain term match
            domain_match = len(tokens & domain_stems)

            relevance = keyword_overlap * 1.0 + name_match * 2.0 + domain_match * 1.5
            branch_relevance[branch] = relevance

        max_relevance = max(branch_relevance.values()) if branch_relevance else 0.0

        # --- Phase 2: Position matching within each branch ---
        partial: dict[str, dict | None] = {}
        all_matched_tokens: list[str] = []
        branch_matched_tokens: dict[str, list[str]] = {b: [] for b in ALL_BRANCHES}

        for branch in ALL_BRANCHES:
            relevance = branch_relevance[branch]

            # Per-branch TF-IDF for position selection
            branch_tfidf = {
                cid: sim for cid, sim in self._tfidf.query_branch(intent, branch)
            }

            best_id = None
            best_score = 0.0

            constructs = self._query.list_constructs(branch)
            for c in constructs:
                # Tag score
                c_tags = set(c.get("tags", []))
                if not c_tags:
                    tag_score = 0.0
                else:
                    overlap = len(tokens & c_tags)
                    tag_score = overlap / len(c_tags)

                # TF-IDF score (per-branch)
                tfidf_score = branch_tfidf.get(c["id"], 0.0)

                combined = tag_score * 0.6 + tfidf_score * 0.4

                if combined > best_score:
                    best_score = combined
                    best_id = c["id"]

            if best_score >= MATCH_THRESHOLD and best_id is not None:
                pos_part = best_id.split(".")[1]
                x, y = map(int, pos_part.split("_"))

                # Weight from branch relevance (Phase 1) + match confidence (Phase 2)
                if max_relevance > 0:
                    relevance_weight = relevance / max_relevance
                else:
                    relevance_weight = 0.0

                weight = max(0.1, (relevance_weight * 0.7 + best_score * 0.3))

                # Track matched tokens
                c_data = self._query.get_construct_by_id(best_id)
                if c_data:
                    c_tags = set(c_data.get("tags", []))
                    matched = list(tokens & c_tags)
                    branch_matched_tokens[branch] = matched
                    all_matched_tokens.extend(matched)

                partial[branch] = {
                    "x": x,
                    "y": y,
                    "weight": weight,
                    "confidence": best_score,
                }
            else:
                partial[branch] = None

        # Phase 3: Diversification — if low-relevance branches landed on the
        # same position as high-relevance ones, mark them as None so the CSP
        # can fill them with structurally appropriate alternatives.
        if max_relevance > 0:
            # Find the position chosen by the highest-relevance branch
            filled = {b: v for b, v in partial.items() if v is not None}
            if filled:
                # Count how many branches share the same position
                from collections import Counter
                pos_counts = Counter((v["x"], v["y"]) for v in filled.values())
                most_common_pos, most_common_count = pos_counts.most_common(1)[0]

                # If > 60% of branches share the same position, it's a degenerate result.
                # Null out low-relevance branches so CSP can diversify them.
                if most_common_count > len(filled) * 0.6:
                    relevance_threshold = max_relevance * 0.3
                    for branch in list(partial.keys()):
                        if partial[branch] is None:
                            continue
                        entry = partial[branch]
                        if (entry["x"], entry["y"]) == most_common_pos:
                            if branch_relevance[branch] < relevance_threshold:
                                partial[branch] = None

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
