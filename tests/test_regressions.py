"""Regression tests for bugs that were caught during live demo of v0.

These exist precisely because they were not caught by the original test
suite — they emerged when feeding the normalizer real-world Roman Urdu
text. Each one is now a permanent guard so the bug cannot return silently.

If you find yourself tempted to delete or weaken any of these, read the
comment block above the test first.
"""

from app.normalizer import normalize_token, normalize_text


class TestShortKeyCollisionBug:
    """
    BUG: any stray "k" was resolving to "kyun".

    Root cause: an early variant map had `"k": "kya"`, but worse, the
    phonetic index originally included single-letter canonical entries,
    so the phonetic key for any word starting with "k" could collide into
    that single-character bucket and pull the resolution toward whichever
    K-word was alphabetically first — which happened to be "kyun".

    Fix: the phonetic index now excludes any key of length < 2. Short
    tokens can only be resolved via the variant map, never phonetics.
    """

    def test_short_k_does_not_resolve_to_kyun(self):
        result = normalize_token("k")
        # "k" is NOT in the variant map anymore (we don't fish that hard);
        # critically, it must NOT resolve to "kyun" either.
        assert result["normalized"] != "kyun"

    def test_short_keys_excluded_from_phonetic_index(self):
        # No single-character key should ever be present in the phonetic index.
        from app.normalizer import _PHONETIC_INDEX
        for key in _PHONETIC_INDEX:
            assert len(key) >= 2, f"Short key leaked into index: {key!r}"

    def test_unrelated_k_word_does_not_become_kyun(self):
        # A different K word should not get pulled to "kyun"
        result = normalize_token("kitab")
        assert result["normalized"] != "kyun"

    def test_short_b_does_not_resolve(self):
        # general guard: any single letter should not pull a long word
        result = normalize_token("b")
        # Must not be a multi-character canonical word
        assert len(result["normalized"]) <= 2 or result["source"] == "unknown"


class TestKahaKahanHomographBug:
    """
    BUG: "kaha" (he/she said) was being silently rewritten to "kahan" (where).

    Root cause: an early version of the variant map had `"kaha": "kahan"`,
    confusing the two by Urdu/English transliteration. They are different
    words. Worse, the normalizer didn't flag the collision because the
    variant map is checked first and exits early.

    Fix: removed the bad map entry, added both to the canonical lexicon,
    registered {"kaha", "kahan"} as a known homograph group. Now when
    they collide via phonetic key, the normalizer marks the result
    ambiguous rather than silently picking one.
    """

    def test_kaha_does_not_silently_become_kahan(self):
        result = normalize_token("kaha")
        # If the algorithm rewrote it, it MUST be flagged ambiguous
        if result["normalized"] != "kaha":
            assert result["ambiguous"], (
                "kaha was silently rewritten to something else — "
                "this is the exact bug we are guarding against"
            )

    def test_kahan_does_not_silently_become_kaha(self):
        result = normalize_token("kahan")
        if result["normalized"] != "kahan":
            assert result["ambiguous"]

    def test_homograph_group_registered(self):
        from app.data import HOMOGRAPH_GROUPS
        assert any(
            {"kaha", "kahan"} <= group for group in HOMOGRAPH_GROUPS
        ), "kaha/kahan homograph group not registered"


class TestAdditionalHomographs:
    """Other homograph groups we know about — guard against silent collapse."""

    def test_jana_janna_registered(self):
        from app.data import HOMOGRAPH_GROUPS
        assert any({"jana", "janna"} <= g for g in HOMOGRAPH_GROUPS)

    def test_mara_maara_registered(self):
        from app.data import HOMOGRAPH_GROUPS
        assert any({"mara", "maara"} <= g for g in HOMOGRAPH_GROUPS)

    def test_baal_bal_registered(self):
        from app.data import HOMOGRAPH_GROUPS
        assert any({"baal", "bal"} <= g for g in HOMOGRAPH_GROUPS)

    def test_sher_sheer_registered(self):
        from app.data import HOMOGRAPH_GROUPS
        assert any({"sher", "sheer"} <= g for g in HOMOGRAPH_GROUPS)


class TestUnknownAfterRewriteIsBugged:
    """
    Meta-test: if the unknown layer ever rewrites a token, that's a bug.
    """

    def test_unknown_layer_never_rewrites(self):
        result = normalize_token("totally_unknown_word_xyzqwerty")
        assert result["source"] == "unknown"
        assert result["normalized"] == result["original"]
