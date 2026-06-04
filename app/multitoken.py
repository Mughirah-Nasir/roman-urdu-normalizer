"""
Phrase-level multi-token rewrites — Layer 0.5 of the normalizer pipeline.

Some Roman Urdu compound forms span multiple tokens and cannot be resolved
correctly by a strictly per-token resolver. Examples:

    pi lo    -> "pee lo"    (drink — particle "lo" is the imperative marker)
    ja rha   -> "ja raha"   (going — progressive aspect across two tokens)
    ho gya   -> "ho gaya"   (became — past tense across two tokens)
    kr de    -> "kar de"    (do it — verb + benefactive particle)

The per-token resolver handles each token in isolation and gets some of
these right by accident (e.g. "kr" -> "kar" still works) but cannot
guarantee correctness when tokens *interact* — the resolution of "rha"
depends on whether the preceding token was a verb stem like "ja".

This module fixes that with a longest-match scan over a curated phrase
map BEFORE the per-token resolver runs. Matched phrases produce a single
phrase_map record with source="phrase_map" and confidence=1.0. Unmatched
tokens fall through to the per-token resolver unchanged.

Architectural rules:
    - Longest match wins (greedy left-to-right scan)
    - Phrases are at most 3 tokens long (covers >95% of real cases,
      keeps the scan O(3*N) instead of O(N²))
    - The phrase map is hand-curated for Pakistani Roman Urdu; entries
      are added the same way variant map entries are added (native
      speaker review, benchmark-driven additions)
    - This layer follows the same "never silently guess" rule — only
      explicit map entries fire, never fuzzy matches

Author: Mughirah Nasir, 2026.
"""

from __future__ import annotations

import re
from typing import Iterable


# ============================================================
# Phrase map — multi-token compound forms
# ============================================================
#
# Format: tuple of lowercase tokens -> canonical replacement string.
# Tokens here are matched against tokens from the input AFTER lowering
# and stripping. The replacement is the canonical Roman Urdu form.
#
# Coverage targets (in priority order):
#   1. Compound verbs with progressive aspect (kar rha, ja rhi, etc.)
#   2. Compound past-tense forms (ho gya, ho gyi, a gya, etc.)
#   3. Verb + benefactive particle (kr de, kr lo, kr do, etc.)
#   4. Common idiomatic phrases (kuch nai, abhi tk, ho jae, etc.)
#   5. Polite/imperative compounds (suno yr, dekh lo, etc.)

PHRASE_MAP: dict[tuple[str, ...], str] = {
    # --- 1. Compound verbs with progressive aspect (token1 + rha/rhi/rhe) ---
    ("kr", "rha"):     "kar raha",
    ("kr", "rhi"):     "kar rahi",
    ("kr", "rhe"):     "kar rahe",
    ("kar", "rha"):    "kar raha",
    ("kar", "rhi"):    "kar rahi",
    ("kar", "rhe"):    "kar rahe",
    ("ja", "rha"):     "ja raha",
    ("ja", "rhi"):     "ja rahi",
    ("ja", "rhe"):     "ja rahe",
    ("a", "rha"):      "aa raha",
    ("a", "rhi"):      "aa rahi",
    ("a", "rhe"):      "aa rahe",
    ("aa", "rha"):     "aa raha",
    ("aa", "rhi"):     "aa rahi",
    ("aa", "rhe"):     "aa rahe",
    ("ho", "rha"):     "ho raha",
    ("ho", "rhi"):     "ho rahi",
    ("ho", "rhe"):     "ho rahe",
    ("so", "rha"):     "so raha",
    ("so", "rhi"):     "so rahi",
    ("so", "rhe"):     "so rahe",
    ("kha", "rha"):    "kha raha",
    ("kha", "rhi"):    "kha rahi",
    ("kha", "rhe"):    "kha rahe",
    ("pi", "rha"):     "pi raha",
    ("pi", "rhi"):     "pi rahi",
    ("pi", "rhe"):     "pi rahe",
    ("parh", "rha"):   "padh raha",
    ("parh", "rhi"):   "padh rahi",
    ("parh", "rhe"):   "padh rahe",
    ("dekh", "rha"):   "dekh raha",
    ("dekh", "rhi"):   "dekh rahi",
    ("dekh", "rhe"):   "dekh rahe",
    ("sun", "rha"):    "sun raha",
    ("sun", "rhi"):    "sun rahi",
    ("sun", "rhe"):    "sun rahe",
    ("bol", "rha"):    "bol raha",
    ("bol", "rhi"):    "bol rahi",
    ("bol", "rhe"):    "bol rahe",
    ("likh", "rha"):   "likh raha",
    ("likh", "rhi"):   "likh rahi",
    ("likh", "rhe"):   "likh rahe",
    ("soch", "rha"):   "soch raha",
    ("soch", "rhi"):   "soch rahi",
    ("soch", "rhe"):   "soch rahe",

    # --- 2. Compound past-tense forms (token1 + gya/gyi/gye) ---
    ("ho", "gya"):     "ho gaya",
    ("ho", "gyi"):     "ho gayi",
    ("ho", "gye"):     "ho gaye",
    ("a", "gya"):      "aa gaya",
    ("a", "gyi"):      "aa gayi",
    ("a", "gye"):      "aa gaye",
    ("aa", "gya"):     "aa gaya",
    ("aa", "gyi"):     "aa gayi",
    ("aa", "gye"):     "aa gaye",
    ("ja", "chuka"):   "ja chuka",
    ("ja", "chuki"):   "ja chuki",

    # --- 3. Verb + benefactive/imperative particle ---
    # "de" (give), "le" (take), "lo" (take-imperative), "do" (give-imperative)
    ("kr", "de"):      "kar de",
    ("kr", "do"):      "kar do",
    ("kr", "le"):      "kar le",
    ("kr", "lo"):      "kar lo",
    ("kar", "de"):     "kar de",
    ("kar", "do"):     "kar do",
    ("kar", "le"):     "kar le",
    ("kar", "lo"):     "kar lo",
    ("kha", "le"):     "kha le",
    ("kha", "lo"):     "kha lo",
    ("kha", "li"):     "kha li",
    ("kha", "liya"):   "kha liya",
    ("pi", "le"):      "pee le",
    ("pi", "lo"):      "pee lo",
    ("pi", "li"):      "pi li",
    ("pi", "liya"):    "pi liya",
    ("dekh", "lo"):    "dekh lo",
    ("dekh", "le"):    "dekh le",
    ("sun", "lo"):     "sun lo",
    ("sun", "le"):     "sun le",
    ("bol", "do"):     "bol do",
    ("bol", "de"):     "bol de",
    ("parh", "lo"):    "padh lo",
    ("parh", "le"):    "padh le",
    ("likh", "do"):    "likh do",
    ("likh", "de"):    "likh de",
    ("le", "lo"):      "le lo",
    ("de", "do"):      "de do",
    ("a", "ja"):       "aa ja",
    ("aa", "ja"):      "aa ja",

    # --- 4. Negation compounds ---
    ("nai", "aya"):    "nahi aaya",
    ("nai", "ayi"):    "nahi aayi",
    ("nai", "aye"):    "nahi aaye",
    ("nhi", "aya"):    "nahi aaya",
    ("nhi", "ayi"):    "nahi aayi",
    ("nhi", "aye"):    "nahi aaye",
    ("nai", "hota"):   "nahi hota",
    ("nai", "hoti"):   "nahi hoti",
    ("nai", "hote"):   "nahi hote",
    ("nhi", "hota"):   "nahi hota",
    ("nhi", "hoti"):   "nahi hoti",
    ("nhi", "hote"):   "nahi hote",
    ("kuch", "nai"):   "kuch nahi",
    ("kch", "nai"):    "kuch nahi",
    ("kch", "nhi"):    "kuch nahi",

    # --- 5. Time compounds ---
    ("abhi", "tk"):    "abhi tak",
    ("abi", "tk"):     "abhi tak",
    ("ab", "tk"):      "ab tak",
    ("ab", "tak"):     "ab tak",
    ("kal", "tk"):     "kal tak",
    ("aj", "tk"):      "aaj tak",
    ("subah", "se"):   "subah se",
    ("raat", "ko"):    "raat ko",
    ("subh", "subh"):  "subah subah",
    ("der", "se"):     "der se",

    # --- 6. Intensifier compounds ---
    ("bht", "zyada"):  "bahut zyada",
    ("bohat", "zyada"):"bahut zyada",
    ("bht", "thora"):  "bahut thora",
    ("bohat", "thora"):"bahut thora",
    ("thora", "sa"):   "thora sa",
    ("kafi", "zyada"): "kafi zyada",

    # --- 7. Common idioms ---
    ("kese", "ho"):    "kaise ho",
    ("kese", "hen"):   "kaise hain",
    ("kya", "hua"):    "kya hua",
    ("kya", "hal"):    "kya haal",
    ("kya", "haal"):   "kya haal",
    ("kya", "scene"):  "kya scene",
    ("scene", "off"):  "scene off",
    ("set", "hai"):    "set hai",
    ("set", "hen"):    "set hain",
    ("set", "ho"):     "set ho",

    # --- 8. Conditional/relative ---
    ("agr", "tm"):     "agar tum",
    ("agar", "tm"):    "agar tum",
    ("agr", "ap"):     "agar aap",
    ("agar", "ap"):    "agar aap",
    ("jo", "kch"):     "jo kuch",
    ("jo", "kuch"):    "jo kuch",
}


# ============================================================
# Tokenize for matching (lowercase word-only stream)
# ============================================================
# We need a clean lowercase token stream from the input so the phrase
# matcher can scan it. We DON'T modify the input text here — the
# normalizer will tokenize the actual input later for output assembly.

_PHRASE_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _scan_for_phrases(text: str, max_phrase_len: int = 3) -> list[dict]:
    """
    Find all longest phrase-map matches in `text`. Returns a list of
    {match_start_char, match_end_char, original, replacement, length_tokens}
    in left-to-right order, non-overlapping.

    Greedy: at each position, try the longest possible phrase first,
    then shorter. Skip ahead past any match to avoid overlap.
    """
    if not text:
        return []

    # Find word positions in the input string
    word_spans = [(m.start(), m.end(), m.group()) for m in _PHRASE_TOKEN_RE.finditer(text)]
    if not word_spans:
        return []

    matches: list[dict] = []
    i = 0
    while i < len(word_spans):
        matched = False
        # Try longest phrase first
        for span_count in range(min(max_phrase_len, len(word_spans) - i), 1, -1):
            tokens = tuple(word_spans[i + k][2].lower() for k in range(span_count))
            if tokens in PHRASE_MAP:
                start_char = word_spans[i][0]
                end_char = word_spans[i + span_count - 1][1]
                matches.append({
                    "match_start_char": start_char,
                    "match_end_char":   end_char,
                    "original":         text[start_char:end_char],
                    "replacement":      PHRASE_MAP[tokens],
                    "length_tokens":    span_count,
                })
                i += span_count
                matched = True
                break
        if not matched:
            i += 1

    return matches


def find_phrase_matches(text: str) -> list[dict]:
    """Public entry: list of phrase match records for the given text."""
    return _scan_for_phrases(text)


def phrase_map_size() -> int:
    """How many phrase entries we have. Used by /stats."""
    return len(PHRASE_MAP)
