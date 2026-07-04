"""Regression tests for bugs that were caught during live demo of v0.

These exist precisely because they were not caught by the original test
suite — they emerged when feeding the normalizer real-world Roman Urdu
text. Each one is now a permanent guard so the bug cannot return silently.

If you find yourself tempted to delete or weaken any of these, read the
comment block above the test first.
"""

from app.normalizer import normalize_token


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

    def test_short_b_does_not_resolve_via_phonetic(self):
        # general guard: single letters should not be resolved by the PHONETIC
        # layer (the source of the original bug). Explicit variant map entries
        # for short tokens are fine and intentional ("h"->"hai", "b"->"bhi").
        result = normalize_token("b")
        assert result["source"] != "phonetic", (
            "short token resolved via phonetic layer — this is the bug class "
            "we are guarding against"
        )


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


class TestVariantMapShadowedByLexiconBug:
    """
    BUG (v1.2.1): 9 variant-map entries were dead code because the canonical
    lexicon was checked BEFORE the variant map in normalize_token, and those
    9 variant spellings also (incorrectly) appeared in the lexicon. Verified
    live: normalize_text("bohat") returned "bohat" even though the README's
    own example table promises "bohat" -> "bahut".

    Fix: non-identity variant-map remaps now win over the lexicon, and the
    9 shadowed spellings were removed from CANONICAL_LEXICON (a matching
    data-integrity test lives in tests/test_data.py).
    """

    FORMERLY_DEAD_ENTRIES = {
        "abh":   "abhi",
        "aya":   "aaya",
        "bohat": "bahut",
        "hi":    "hai",
        "kam":   "kaam",
        "ki":    "koi",
        "kiya":  "kya",
        "mein":  "main",
        "tu":    "tum",
    }

    def test_formerly_dead_variant_entries_resolve(self):
        for variant, canonical in self.FORMERLY_DEAD_ENTRIES.items():
            result = normalize_token(variant)
            assert result["normalized"] == canonical, (
                f"{variant!r} -> {result['normalized']!r}, expected "
                f"{canonical!r} — variant map entry is dead again"
            )
            assert result["source"] == "variant_map"
            assert result["confidence"] == 1.0

    def test_readme_example_bohat_becomes_bahut(self):
        # The exact claim from the README's example table.
        from app.normalizer import normalize_text
        assert normalize_text("bohat")["normalized"] == "bahut"

    def test_identity_variant_entries_still_report_unchanged(self):
        # Words that are both canonical AND identity-mapped in the variant
        # map ("kya" -> "kya") must keep reporting source="unchanged".
        result = normalize_token("kya")
        assert result["normalized"] == "kya"
        assert result["source"] == "unchanged"


class TestPhraseLayerAtePunctuationBug:
    """
    BUG (v1.2.1): the phrase layer matched word tokens regardless of what
    sat between them, so "ho. gya" -> "ho gaya" (sentence boundary deleted)
    and "kr, de" -> "kar de" (comma deleted). Silently destroying
    punctuation violates the project's "never silently guess" contract.

    Fix: phrase tokens must be separated by whitespace only.
    """

    def test_full_stop_between_phrase_tokens_is_preserved(self):
        from app.normalizer import normalize_text
        result = normalize_text("ho. gya")
        assert result["normalized"] == "ho. gaya"
        assert result["stats"]["phrase_map"] == 0

    def test_comma_between_phrase_tokens_is_preserved(self):
        from app.normalizer import normalize_text
        result = normalize_text("kr, de")
        assert result["normalized"].startswith("kar,")
        assert "," in result["normalized"]
        assert result["stats"]["phrase_map"] == 0

    def test_phrase_still_matches_across_a_single_space(self):
        from app.normalizer import normalize_text
        result = normalize_text("ho gya")
        assert result["normalized"] == "ho gaya"
        assert result["stats"]["phrase_map"] == 1

    def test_phrase_still_matches_across_multiple_spaces(self):
        from app.normalizer import normalize_text
        result = normalize_text("ho  gya")
        assert result["stats"]["phrase_map"] == 1

    def test_sentence_boundary_case_from_report(self):
        from app.normalizer import normalize_text
        result = normalize_text("kaam ho gya. ab tk kuch nai")
        assert ". " in result["normalized"]
        assert result["normalized"] == "kaam ho gaya. ab tak kuch nahi"


class TestWindowsConsoleEncodingBug:
    """
    BUG (v1.2.1): benchmark/run_benchmark.py printed box-drawing characters
    that crash with UnicodeEncodeError on legacy Windows consoles (cp1252) —
    ironic for a tool aimed at Pakistan, where Windows dominates.

    Fix: app.console.ensure_utf8_stdout() reconfigures stdout/stderr to
    UTF-8 at every console entry point (benchmark, comparison, latency,
    CLI, review_unknowns).
    """

    def _cp1252_stdout(self):
        import io
        buf = io.BytesIO()
        return buf, io.TextIOWrapper(buf, encoding="cp1252")

    def test_print_human_survives_cp1252_stdout(self, monkeypatch):
        import sys

        from app.console import ensure_utf8_stdout
        from benchmark.run_benchmark import print_human

        report = {
            "dataset": "unit-test",
            "examples": 1,
            "sentence_accuracy": 0.0,
            "token_precision": 0.5,
            "token_recall": 0.5,
            "token_f1": 0.5,
            "by_category": {
                "misc": {"examples": 1, "exact_match": 0,
                         "sentence_accuracy": 0.0,
                         "precision": 0.5, "recall": 0.5, "f1": 0.5},
            },
            # An error record with an emoji — pass-through user text must
            # not crash the report printer either.
            "errors": [{
                "id": "t1", "category": "misc", "exact": False,
                "input": "kya haal hai 🏃", "expected": "kya haal hai 🏃",
                "predicted": "kya haal hai", "notes": "unit test",
            }],
        }

        buf, fake_stdout = self._cp1252_stdout()
        monkeypatch.setattr(sys, "stdout", fake_stdout)
        ensure_utf8_stdout()   # the fix under test
        print_human(report)    # crashed with UnicodeEncodeError before fix
        sys.stdout.flush()
        assert "BENCHMARK RESULTS" in buf.getvalue().decode("utf-8")

    def test_ensure_utf8_stdout_is_safe_on_plain_streams(self, monkeypatch):
        # Streams without .reconfigure (e.g. wrapped/captured) must not raise.
        import sys

        from app.console import ensure_utf8_stdout

        class Plain:
            def write(self, s):
                return len(s)

        monkeypatch.setattr(sys, "stdout", Plain())
        ensure_utf8_stdout()  # must be a silent no-op
