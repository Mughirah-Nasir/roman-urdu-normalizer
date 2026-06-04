"""
Roman Urdu normalizer — four-layer resolution pipeline with confidence scoring.

Resolution order (longest match wins at each layer):

  Layer 0.5 — Multi-token phrase map        (NEW in v1.2)
      Scan input left-to-right for known compound forms — "kr de", "ja rha",
      "ho gya". Longest match wins. Matched spans skip the per-token layers.

  Layer 1 — Already canonical
      If the lowercased token is a canonical lexicon word, return it.

  Layer 2 — Exact variant map
      O(1) dict lookup against VARIANT_MAP. Catches SMS shorthand that the
      phonetic algorithm can't reach (e.g. "bht" -> "bahut", "nhi" -> "nahi").

  Layer 3 — Phonetic key match
      Compute the phonetic key of the input; look up canonical words sharing
      that key in a pre-built phonetic index. Multiple matches in a known
      homograph group -> ambiguous. Otherwise pick deterministically and
      surface alternatives.

  Layer 4 — Unknown
      Nothing matched. Pass through unchanged with confidence 0.0 and
      source="unknown". Loudness > silent guessing.

Confidence scoring (new in v1.2):
  - variant_map  : 1.0    (explicit human curation)
  - phrase_map   : 1.0    (explicit multi-token curation)
  - unchanged    : 1.0    (already canonical)
  - phonetic     : 0.85   (algorithm match, single canonical word)
  - phonetic     : 0.65   (multiple canonical words, picked deterministically)
  - phonetic     : 0.40   (registered homograph — ambiguous flag set)
  - unknown      : 0.00   (no resolution attempted)

Callers can threshold on confidence. Anything < 0.7 should be treated as
"may want human review" by downstream systems. The "never silently guess"
contract is preserved at confidence 0.0 (unknown) and 0.4 (ambiguous).

Short-token guard: tokens whose phonetic key is < 2 chars are never
resolved via the phonetic layer (too many collisions).
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from app.data import (
    VARIANT_MAP,
    CANONICAL_LEXICON,
    HOMOGRAPH_GROUPS,
    all_canonical_words,
)
from app.phonetic import phonetic_key
from app.exceptions import BatchSizeError, InvalidInputError
from app.multitoken import find_phrase_matches, PHRASE_MAP


MAX_BATCH_SIZE = 100


# --- Confidence constants ---------------------------------------------------

CONFIDENCE_EXACT       = 1.00  # variant_map, phrase_map, unchanged
CONFIDENCE_PHONETIC    = 0.85  # phonetic single match
CONFIDENCE_PHONETIC_MULTI = 0.65  # phonetic with deterministic pick
CONFIDENCE_AMBIGUOUS   = 0.40  # known homograph collision
CONFIDENCE_UNKNOWN     = 0.00  # no resolution


# ============================================================
# Phonetic index — built once at import time
# ============================================================
def _build_phonetic_index() -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for word in all_canonical_words():
        key = phonetic_key(word)
        if len(key) < 2:
            continue
        index[key].append(word)
    for k in index:
        index[k].sort()
    return dict(index)


_PHONETIC_INDEX = _build_phonetic_index()


def _is_known_homograph(words: set) -> bool:
    word_set = set(words)
    return any(word_set <= group for group in HOMOGRAPH_GROUPS)


# ============================================================
# Token-level resolution (Layer 1-4)
# ============================================================

def normalize_token(token: str) -> dict[str, Any]:
    """Resolve a single token in isolation. Returns a record dict."""
    if not token or not token.strip():
        return {
            "original": token, "normalized": token,
            "source": "unchanged", "confidence": CONFIDENCE_EXACT,
            "ambiguous": False, "candidates": [],
        }

    raw = token
    lower = token.lower().strip()

    if lower in CANONICAL_LEXICON:
        return {
            "original": raw, "normalized": lower,
            "source": "unchanged", "confidence": CONFIDENCE_EXACT,
            "ambiguous": False, "candidates": [],
        }

    if lower in VARIANT_MAP:
        return {
            "original": raw, "normalized": VARIANT_MAP[lower],
            "source": "variant_map", "confidence": CONFIDENCE_EXACT,
            "ambiguous": False, "candidates": [],
        }

    if len(lower) >= 2:
        key = phonetic_key(lower)
        if len(key) >= 2:
            candidates = _PHONETIC_INDEX.get(key, [])
            if len(candidates) == 1:
                return {
                    "original": raw, "normalized": candidates[0],
                    "source": "phonetic", "confidence": CONFIDENCE_PHONETIC,
                    "ambiguous": False, "candidates": [],
                }
            if len(candidates) > 1:
                if _is_known_homograph(set(candidates)):
                    return {
                        "original": raw, "normalized": raw,
                        "source": "phonetic", "confidence": CONFIDENCE_AMBIGUOUS,
                        "ambiguous": True, "candidates": candidates,
                    }
                # Non-homograph collision: pick deterministically with lower confidence
                return {
                    "original": raw, "normalized": candidates[0],
                    "source": "phonetic", "confidence": CONFIDENCE_PHONETIC_MULTI,
                    "ambiguous": False, "candidates": candidates,
                }

    return {
        "original": raw, "normalized": raw,
        "source": "unknown", "confidence": CONFIDENCE_UNKNOWN,
        "ambiguous": False, "candidates": [],
    }


# ============================================================
# String-level normalization with multi-token Layer 0.5
# ============================================================

_TOKEN_RE = re.compile(r"(\w+|\W+)", re.UNICODE)


def normalize_text(text: str) -> dict[str, Any]:
    """
    Normalize a full string of Roman Urdu text.

    Pipeline:
      1. Scan the input for known multi-token phrases (longest match)
      2. Replace matched spans with phrase_map records
      3. Run per-token resolver on everything that wasn't matched
      4. Reassemble preserving whitespace, punctuation, casing structure

    Returns a record with input, normalized output, token-level resolutions,
    summary stats, and the average/minimum confidence across all word tokens.
    """
    if text is None:
        raise InvalidInputError("text cannot be None")

    if not text:
        return {
            "input": text, "normalized": text, "tokens": [],
            "stats": {"total": 0, "variant_map": 0, "phonetic": 0,
                      "phrase_map": 0, "unchanged": 0, "unknown": 0,
                      "ambiguous": 0, "avg_confidence": None,
                      "min_confidence": None},
        }

    # ---- Layer 0.5: multi-token phrase scan ----
    phrase_matches = find_phrase_matches(text)

    # Build a fast-lookup map: char_offset -> phrase_match
    phrase_starts = {m["match_start_char"]: m for m in phrase_matches}
    # Set of char ranges (start, end) that are consumed by phrase matches
    consumed_ranges = [(m["match_start_char"], m["match_end_char"]) for m in phrase_matches]

    def _is_in_consumed_range(start: int, end: int) -> bool:
        for c_start, c_end in consumed_ranges:
            if start >= c_start and end <= c_end:
                return True
        return False

    # ---- Build output ----
    out_pieces: list[str] = []
    token_records: list[dict[str, Any]] = []
    stats = {"total": 0, "variant_map": 0, "phonetic": 0, "phrase_map": 0,
             "unchanged": 0, "unknown": 0, "ambiguous": 0}

    cursor = 0
    seen_phrase_at: set[int] = set()
    pieces_with_offsets: list[tuple[int, int, str]] = []
    for m in _TOKEN_RE.finditer(text):
        pieces_with_offsets.append((m.start(), m.end(), m.group()))

    for start, end, piece in pieces_with_offsets:
        # Did a phrase match start at exactly this position?
        if start in phrase_starts and start not in seen_phrase_at:
            match = phrase_starts[start]
            # Emit one phrase_map record covering the whole span
            record = {
                "original":   match["original"],
                "normalized": match["replacement"],
                "source":     "phrase_map",
                "confidence": CONFIDENCE_EXACT,
                "ambiguous":  False,
                "candidates": [],
                "span_tokens": match["length_tokens"],
            }
            token_records.append(record)
            out_pieces.append(match["replacement"])
            stats["total"] += 1
            stats["phrase_map"] += 1
            seen_phrase_at.add(start)
            continue

        # Is this piece consumed by a phrase that started earlier?
        if _is_in_consumed_range(start, end):
            continue

        # Regular token / punctuation handling
        if piece.isalpha() or any(c.isalnum() for c in piece):
            record = normalize_token(piece)
            out_pieces.append(record["normalized"])
            token_records.append(record)
            stats["total"] += 1
            stats[record["source"]] = stats.get(record["source"], 0) + 1
            if record["ambiguous"]:
                stats["ambiguous"] += 1
        else:
            out_pieces.append(piece)

    # Confidence aggregates across word-bearing tokens only
    confidences = [t["confidence"] for t in token_records]
    avg_conf = sum(confidences) / len(confidences) if confidences else None
    min_conf = min(confidences) if confidences else None

    stats["avg_confidence"] = round(avg_conf, 3) if avg_conf is not None else None
    stats["min_confidence"] = round(min_conf, 3) if min_conf is not None else None

    return {
        "input": text,
        "normalized": "".join(out_pieces),
        "tokens": token_records,
        "stats": stats,
    }


# ============================================================
# Batch
# ============================================================

def normalize_batch(texts: list[str]) -> list[dict[str, Any]]:
    if texts is None:
        raise InvalidInputError("batch list cannot be None")
    if len(texts) > MAX_BATCH_SIZE:
        raise BatchSizeError(len(texts), MAX_BATCH_SIZE)
    return [normalize_text(t) for t in texts]
