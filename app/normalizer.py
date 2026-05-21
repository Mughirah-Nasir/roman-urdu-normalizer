"""
Three-layer Roman Urdu normalizer.

Resolution order for each token:

  Layer 1 — Exact variant map
      O(1) dict lookup against VARIANT_MAP. Catches SMS shorthand that the
      phonetic algorithm can't reach because it drops too many vowels
      (e.g. "bht" -> "bahut", "nhi" -> "nahi").

  Layer 2 — Phonetic key match
      Compute the phonetic key of the input; look up canonical words sharing
      that key in a pre-built phonetic index. If exactly one match, resolve
      to it. If multiple matches AND the group is a known homograph, mark
      ambiguous. If multiple matches and NOT a homograph, pick the first
      deterministically AND surface alternatives so the caller can override.

  Layer 3 — Unknown
      Nothing matched. Pass the token through unchanged and flag it.
      Silent guessing would poison every downstream system that depends on
      us. Loudness > cleverness.

Short-token guard: tokens whose phonetic key is < 2 chars are never
resolved via the phonetic layer (too many collisions). They go through
the variant map only.
"""

from collections import defaultdict
from typing import List, Dict, Any

from app.data import (
    VARIANT_MAP,
    CANONICAL_LEXICON,
    HOMOGRAPH_GROUPS,
    all_canonical_words,
)
from app.phonetic import phonetic_key
from app.exceptions import BatchSizeError, InvalidInputError


# Configurable batch ceiling — also enforced at the API layer.
MAX_BATCH_SIZE = 100


# ============================================================
# Phonetic index — built once at import time
# ============================================================
# NOTE: keys of length < 2 are intentionally excluded from the phonetic
# index — see tests/test_regressions.py::TestShortKeyCollisionBug.

def _build_phonetic_index() -> Dict[str, List[str]]:
    """Map phonetic_key -> [canonical words sharing that key]."""
    index = defaultdict(list)
    for word in all_canonical_words():
        key = phonetic_key(word)
        if len(key) < 2:
            # Too short — would collide with almost anything. Skip.
            continue
        index[key].append(word)
    # Sort each bucket so resolution is deterministic across runs.
    for key in index:
        index[key].sort()
    return dict(index)


_PHONETIC_INDEX = _build_phonetic_index()


def _is_known_homograph(words: set) -> bool:
    """Are these words members of the same known-ambiguous group?"""
    word_set = set(words)
    return any(word_set <= group for group in HOMOGRAPH_GROUPS)


# ============================================================
# Token-level resolution
# ============================================================

def normalize_token(token: str) -> Dict[str, Any]:
    """
    Resolve a single token. Returns a dict with:
      - original    : the input as given
      - normalized  : the canonical form (or original if unknown)
      - source      : "variant_map" | "phonetic" | "unchanged" | "unknown"
      - ambiguous   : bool — true if multiple homograph candidates
      - candidates  : list of candidates when ambiguous, else empty
    """
    if not token or not token.strip():
        return {
            "original": token, "normalized": token,
            "source": "unchanged", "ambiguous": False, "candidates": [],
        }

    raw = token
    lower = token.lower().strip()

    # Layer 0 — already canonical?
    if lower in CANONICAL_LEXICON:
        return {
            "original": raw, "normalized": lower,
            "source": "unchanged", "ambiguous": False, "candidates": [],
        }

    # Layer 1 — exact variant map
    if lower in VARIANT_MAP:
        return {
            "original": raw, "normalized": VARIANT_MAP[lower],
            "source": "variant_map", "ambiguous": False, "candidates": [],
        }

    # Layer 2 — phonetic key (only for tokens long enough to have a 2+ key)
    if len(lower) >= 2:
        key = phonetic_key(lower)
        if len(key) >= 2:
            candidates = _PHONETIC_INDEX.get(key, [])
            if len(candidates) == 1:
                return {
                    "original": raw, "normalized": candidates[0],
                    "source": "phonetic", "ambiguous": False, "candidates": [],
                }
            if len(candidates) > 1:
                if _is_known_homograph(set(candidates)):
                    return {
                        "original": raw, "normalized": raw,
                        "source": "phonetic", "ambiguous": True,
                        "candidates": candidates,
                    }
                # Non-homograph collision: pick the first deterministically and
                # surface the alternatives so the caller can override if needed.
                return {
                    "original": raw, "normalized": candidates[0],
                    "source": "phonetic", "ambiguous": False,
                    "candidates": candidates,
                }

    # Layer 3 — unknown
    return {
        "original": raw, "normalized": raw,
        "source": "unknown", "ambiguous": False, "candidates": [],
    }


# ============================================================
# String-level normalization
# ============================================================

import re
_TOKEN_RE = re.compile(r"(\w+|\W+)", re.UNICODE)


def normalize_text(text: str) -> Dict[str, Any]:
    """
    Normalize a full string. Preserves whitespace and punctuation; only
    word tokens are rewritten.
    """
    if text is None:
        raise InvalidInputError("text cannot be None")

    if not text:
        return {
            "input": text, "normalized": text, "tokens": [],
            "stats": {"total": 0, "variant_map": 0, "phonetic": 0,
                      "unchanged": 0, "unknown": 0, "ambiguous": 0},
        }

    pieces = _TOKEN_RE.findall(text)
    out_pieces = []
    token_records = []
    stats = {"total": 0, "variant_map": 0, "phonetic": 0,
             "unchanged": 0, "unknown": 0, "ambiguous": 0}

    for piece in pieces:
        if piece.isalpha() or any(c.isalnum() for c in piece):
            record = normalize_token(piece)
            out_pieces.append(record["normalized"])
            token_records.append(record)
            stats["total"] += 1
            stats[record["source"]] = stats.get(record["source"], 0) + 1
            if record["ambiguous"]:
                stats["ambiguous"] += 1
        else:
            # whitespace / punctuation — keep as-is
            out_pieces.append(piece)

    return {
        "input": text,
        "normalized": "".join(out_pieces),
        "tokens": token_records,
        "stats": stats,
    }


# ============================================================
# Batch processing
# ============================================================

def normalize_batch(texts: List[str]) -> List[Dict[str, Any]]:
    """
    Normalize a list of strings in one call. Cheaper than N HTTP round
    trips when the caller has many short strings to process.

    Raises BatchSizeError if the batch exceeds MAX_BATCH_SIZE — split and
    retry rather than blowing memory on a 10k-item dump.
    """
    if texts is None:
        raise InvalidInputError("batch list cannot be None")
    if len(texts) > MAX_BATCH_SIZE:
        raise BatchSizeError(len(texts), MAX_BATCH_SIZE)
    return [normalize_text(t) for t in texts]
