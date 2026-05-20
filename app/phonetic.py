"""
Phonetic key algorithm for Roman Urdu.

The idea: many Roman Urdu spelling variants differ only in vowel choice or
in whether a long vowel is doubled. "kya" / "kia" / "kyaa" all encode the
same sound. If we reduce each word to a phonetic skeleton, all three
collapse to the same key and can be resolved together.

This is a Soundex/Caverphone-style algorithm tuned for Urdu phonology:

  1. lowercase, strip diacritics, drop non-letter chars
  2. normalize digraphs ("kh", "gh", "sh", "ch", "th", "ph", "dh") to single tokens
  3. collapse repeated letters ("kyaa" -> "kya")
  4. fold vowel classes — y/i/e/ee/ii merge, a/aa merge, o/u/oo/uu merge
  5. emit the resulting skeleton as the phonetic key

Caveats: this is rule-based, not learned. It WILL collide on short words
(2–3 letters) — we guard against that in the resolver, not here.
Homograph collisions (e.g. kaha/kahan) are also handled in the resolver
via the registered HOMOGRAPH_GROUPS.
"""

import re

# Digraphs that map to a single phoneme. Order matters: longer first.
# We use uppercase single-letter placeholders so subsequent steps don't
# accidentally break a digraph apart.
_DIGRAPHS = [
    ("kh", "K"),
    ("gh", "G"),
    ("sh", "S"),
    ("ch", "C"),
    ("th", "T"),
    ("ph", "F"),
    ("dh", "D"),
    ("bh", "B"),
    ("jh", "J"),
    ("rh", "R"),
]

# Vowel classes — all members of a class collapse to the class representative.
# This is the step doing the real normalization work.
_VOWEL_CLASSES = {
    "a": "a", "aa": "a",
    "e": "i", "i": "i", "y": "i", "ee": "i", "ii": "i",
    "o": "u", "u": "u", "oo": "u", "uu": "u",
}


def _collapse_doubles(s: str) -> str:
    """yaa -> ya, kkk -> k. Keeps a single repeat at most."""
    return re.sub(r"(.)\1+", r"\1", s)


def _strip_non_letters(s: str) -> str:
    """Drop everything that isn't a-z (after lowercasing)."""
    return re.sub(r"[^a-z]", "", s.lower())


def phonetic_key(word: str) -> str:
    """
    Compute a phonetic key for a Roman Urdu word.

    The key is a lossy representation: two different words may share a key
    if they sound similar enough. That's intentional — we want spelling
    variants to map together. The downstream resolver decides what to do
    with collisions (silent merge vs ambiguous flag).
    """
    if not word:
        return ""

    s = _strip_non_letters(word)
    if not s:
        return ""

    # Step 1: digraph substitution
    for digraph, placeholder in _DIGRAPHS:
        s = s.replace(digraph, placeholder)

    # Step 2: vowel-class normalization. Greedy 2-char first, then 1-char.
    out = []
    i = 0
    while i < len(s):
        # Try two-character vowel first (aa, ee, oo, ii, uu)
        if i + 1 < len(s) and s[i:i+2] in _VOWEL_CLASSES:
            out.append(_VOWEL_CLASSES[s[i:i+2]])
            i += 2
            continue
        ch = s[i]
        if ch in _VOWEL_CLASSES:
            out.append(_VOWEL_CLASSES[ch])
        else:
            out.append(ch)
        i += 1
    s = "".join(out)

    # Step 3: collapse consecutive duplicates one more time
    s = _collapse_doubles(s)

    return s


def phonetic_distance(a: str, b: str) -> int:
    """
    Bonus: simple edit distance between two phonetic keys. Useful for
    "did you mean?" suggestions — not used by the core resolver.
    """
    ka, kb = phonetic_key(a), phonetic_key(b)
    if not ka or not kb:
        return max(len(ka), len(kb))
    if ka == kb:
        return 0
    # Levenshtein
    m, n = len(ka), len(kb)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(m+1): dp[i][0] = i
    for j in range(n+1): dp[0][j] = j
    for i in range(1, m+1):
        for j in range(1, n+1):
            cost = 0 if ka[i-1] == kb[j-1] else 1
            dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost)
    return dp[m][n]
