"""Tests for the three-layer normalizer.

Each layer (variant map, phonetic, unknown) gets its own class, plus
end-to-end string-normalization tests and batch tests.
"""

import pytest

from app.normalizer import normalize_token, normalize_text, normalize_batch, MAX_BATCH_SIZE
from app.exceptions import BatchSizeError, InvalidInputError


class TestVariantMapLayer:
    """Layer 1 — exact-match SMS shorthand."""

    def test_sms_shorthand_resolved(self):
        result = normalize_token("bht")
        assert result["normalized"] == "bahut"
        assert result["source"] == "variant_map"

    def test_negation_shorthand(self):
        assert normalize_token("nhi")["normalized"] == "nahi"
        assert normalize_token("nahin")["normalized"] == "nahi"
        assert normalize_token("nai")["normalized"] == "nahi"

    def test_yaar_shorthand(self):
        assert normalize_token("yr")["normalized"] == "yaar"

    def test_kar_family(self):
        assert normalize_token("kr")["normalized"] == "kar"
        assert normalize_token("krna")["normalized"] == "karna"
        assert normalize_token("krta")["normalized"] == "karta"

    def test_greeting_typos(self):
        assert normalize_token("aslam")["normalized"] == "salam"


class TestPhoneticLayer:
    """Layer 2 — phonetic key resolution."""

    def test_kya_variants_all_resolve(self):
        # canonical itself stays
        assert normalize_token("kya")["normalized"] == "kya"
        # phonetic variant collapses
        result = normalize_token("kyaa")
        assert result["normalized"] == "kya"

    def test_long_form_kahan_resolves(self):
        # 'kahaan' is also in variant map; this still passes either way
        result = normalize_token("kahaan")
        assert result["normalized"] == "kahan"


class TestUnknownLayer:
    """Layer 3 — unknown tokens are passed through, never silently guessed."""

    def test_unknown_word_flagged(self):
        result = normalize_token("xyzqwerty")
        assert result["source"] == "unknown"
        assert result["normalized"] == "xyzqwerty"

    def test_unknown_preserves_original_casing(self):
        result = normalize_token("XYZ123")
        # Casing of the original is preserved on unknown tokens
        assert result["normalized"] == "XYZ123"

    def test_random_string_not_silently_rewritten(self):
        # silent rewriting is the failure mode this whole project guards against
        result = normalize_token("blargh")
        assert result["normalized"] == "blargh"


class TestFullStringNormalization:
    """End-to-end: realistic mixed sentences."""

    def test_typical_sms_sentence(self):
        text = "yr bht thora kch kya kr rhe ho"
        result = normalize_text(text)
        # Should change substantially
        assert result["normalized"] != text
        assert "yaar" in result["normalized"]
        assert "bahut" in result["normalized"]
        assert result["stats"]["total"] == 8

    def test_whitespace_preserved(self):
        result = normalize_text("kya  haal   hai")
        assert "  " in result["normalized"]

    def test_punctuation_preserved(self):
        result = normalize_text("kya?")
        assert result["normalized"].endswith("?")

    def test_multiple_punctuation(self):
        result = normalize_text("kya?! aap kese ho...")
        # punctuation should survive the round trip
        assert "?!" in result["normalized"]
        assert "..." in result["normalized"]

    def test_empty_input(self):
        result = normalize_text("")
        assert result["normalized"] == ""
        assert result["stats"]["total"] == 0

    def test_none_input_raises(self):
        with pytest.raises(InvalidInputError):
            normalize_text(None)

    def test_stats_sum_consistency(self):
        result = normalize_text("kya bht xyz nahi")
        s = result["stats"]
        assert s["variant_map"] + s["phonetic"] + s["unchanged"] + s["unknown"] == s["total"]

    def test_ambiguous_counter_tracked(self):
        # not all sentences will trip the ambiguous flag, but the field exists
        result = normalize_text("kya hai")
        assert "ambiguous" in result["stats"]


class TestBatchProcessing:
    """The batch endpoint backend."""

    def test_batch_basic(self):
        results = normalize_batch(["yr", "bht thora", "kch kya"])
        assert len(results) == 3
        assert results[0]["normalized"] == "yaar"

    def test_batch_preserves_order(self):
        inputs = ["bht", "kya", "nhi", "yr"]
        results = normalize_batch(inputs)
        assert len(results) == 4
        assert results[0]["input"] == "bht"
        assert results[3]["input"] == "yr"

    def test_batch_size_limit_enforced(self):
        oversized = ["test"] * (MAX_BATCH_SIZE + 1)
        with pytest.raises(BatchSizeError) as exc:
            normalize_batch(oversized)
        assert exc.value.n == MAX_BATCH_SIZE + 1
        assert exc.value.limit == MAX_BATCH_SIZE

    def test_batch_none_raises(self):
        with pytest.raises(InvalidInputError):
            normalize_batch(None)

    def test_batch_empty_list_allowed(self):
        # an empty batch is valid (no work to do, no error)
        results = normalize_batch([])
        assert results == []

    def test_batch_at_exact_limit(self):
        # exactly MAX_BATCH_SIZE should NOT raise
        inputs = ["kya"] * MAX_BATCH_SIZE
        results = normalize_batch(inputs)
        assert len(results) == MAX_BATCH_SIZE
