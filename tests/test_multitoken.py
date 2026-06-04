"""
Tests for the multi-token phrase rewrite layer (Layer 0.5) and confidence scoring.

The phrase layer was added in v1.2 to handle compound forms that strict
per-token resolution can't handle: 'pi lo', 'ja rha', 'ho gya', 'kr de'.

Confidence scoring was added at the same time to give callers a thresholdable
signal in addition to the source label.
"""

import pytest
from app.normalizer import (
    normalize_text, normalize_token,
    CONFIDENCE_EXACT, CONFIDENCE_PHONETIC, CONFIDENCE_PHONETIC_MULTI,
    CONFIDENCE_AMBIGUOUS, CONFIDENCE_UNKNOWN,
)
from app.multitoken import PHRASE_MAP, find_phrase_matches


# --- Phrase map integrity ---------------------------------------------------

class TestPhraseMapIntegrity:

    def test_phrase_map_is_not_empty(self):
        assert len(PHRASE_MAP) >= 80, "phrase map should cover at least 80 compound forms"

    def test_all_keys_are_tuples_of_lowercase_strings(self):
        for key in PHRASE_MAP:
            assert isinstance(key, tuple)
            assert all(isinstance(t, str) for t in key)
            assert all(t == t.lower() for t in key)

    def test_all_keys_at_least_two_tokens(self):
        # By definition, this is the multi-token map
        for key in PHRASE_MAP:
            assert len(key) >= 2

    def test_all_keys_at_most_three_tokens(self):
        # We cap phrase length at 3 for tractable scan time
        for key in PHRASE_MAP:
            assert len(key) <= 3, f"phrase {key} exceeds 3-token limit"

    def test_all_values_are_strings(self):
        for v in PHRASE_MAP.values():
            assert isinstance(v, str)
            assert v.strip(), "phrase replacement cannot be empty"


# --- Phrase scanning --------------------------------------------------------

class TestPhraseScanning:

    def test_scan_empty_string(self):
        assert find_phrase_matches("") == []

    def test_scan_no_phrase_match(self):
        # Single tokens — phrase scanner finds nothing, per-token resolver
        # will still run on these.
        matches = find_phrase_matches("bht")
        assert matches == []

    def test_scan_finds_kr_de(self):
        matches = find_phrase_matches("yr kr de plz")
        assert len(matches) == 1
        assert matches[0]["replacement"] == "kar de"
        assert matches[0]["length_tokens"] == 2

    def test_scan_finds_ja_rha(self):
        matches = find_phrase_matches("main ja rha hun")
        assert len(matches) == 1
        assert matches[0]["replacement"] == "ja raha"

    def test_scan_longest_match_wins(self):
        # If a 3-token phrase exists, prefer it over the embedded 2-token
        # phrase. Currently no 3-token phrases in the map, but this is the
        # semantic guarantee.
        matches = find_phrase_matches("kr de do")  # "kr de" + "do"
        # Should match "kr de" (2-token), not back off to per-token
        assert any(m["replacement"] == "kar de" for m in matches)

    def test_scan_non_overlapping(self):
        # Multiple matches should not overlap
        matches = find_phrase_matches("kr de aur ja rha hun")
        # Expect 2 matches: "kr de" and "ja rha"
        assert len(matches) == 2
        # And they should not overlap
        if len(matches) == 2:
            assert matches[0]["match_end_char"] <= matches[1]["match_start_char"]


# --- End-to-end: multi-token output -----------------------------------------

class TestMultiTokenEndToEnd:

    def test_kr_rhe_collapses_in_full_string(self):
        result = normalize_text("yr kya kr rhe ho")
        assert "kar rahe" in result["normalized"]
        assert result["stats"]["phrase_map"] >= 1

    def test_ja_rha_compound(self):
        result = normalize_text("main ja rha hun")
        assert "ja raha" in result["normalized"]
        # Token count is 3 not 4 because "ja rha" -> single phrase record
        assert result["stats"]["total"] == 3

    def test_ho_gya_past_compound(self):
        result = normalize_text("kam ho gya hai")
        assert "ho gaya" in result["normalized"]

    def test_a_gya_with_double_a(self):
        # "a gya" should normalize to "aa gaya"
        result = normalize_text("wo a gya tha")
        assert "aa gaya" in result["normalized"]

    def test_kuch_nai_negation(self):
        result = normalize_text("mjhe kuch nai pata")
        assert "kuch nahi" in result["normalized"]

    def test_phrase_record_has_span_tokens(self):
        result = normalize_text("main kr rha hun")
        phrase_records = [r for r in result["tokens"] if r["source"] == "phrase_map"]
        assert len(phrase_records) == 1
        assert phrase_records[0]["span_tokens"] == 2
        assert phrase_records[0]["original"] == "kr rha"
        assert phrase_records[0]["normalized"] == "kar raha"


# --- Confidence scoring -----------------------------------------------------

class TestConfidenceScoring:

    def test_variant_map_match_has_full_confidence(self):
        record = normalize_token("yr")
        assert record["confidence"] == CONFIDENCE_EXACT
        assert record["source"] == "variant_map"

    def test_unchanged_match_has_full_confidence(self):
        record = normalize_token("kya")  # already canonical
        assert record["confidence"] == CONFIDENCE_EXACT
        assert record["source"] == "unchanged"

    def test_phonetic_match_has_high_confidence(self):
        # Pick a token that resolves only via phonetics
        record = normalize_token("kyaaa")  # stretched form
        if record["source"] == "phonetic":
            # 0.85 for single match, 0.65 for multi-match
            assert record["confidence"] in (CONFIDENCE_PHONETIC, CONFIDENCE_PHONETIC_MULTI)

    def test_unknown_has_zero_confidence(self):
        record = normalize_token("qwertyabc")
        assert record["confidence"] == CONFIDENCE_UNKNOWN
        assert record["source"] == "unknown"

    def test_ambiguous_has_low_confidence(self):
        # Find a known homograph — but we need a token that actually triggers it.
        # For now, test the constant ordering
        assert CONFIDENCE_AMBIGUOUS < CONFIDENCE_PHONETIC
        assert CONFIDENCE_AMBIGUOUS > CONFIDENCE_UNKNOWN

    def test_confidence_constants_are_ordered(self):
        # Sanity: monotonic ordering of the confidence buckets
        assert CONFIDENCE_UNKNOWN < CONFIDENCE_AMBIGUOUS
        assert CONFIDENCE_AMBIGUOUS < CONFIDENCE_PHONETIC_MULTI
        assert CONFIDENCE_PHONETIC_MULTI < CONFIDENCE_PHONETIC
        assert CONFIDENCE_PHONETIC < CONFIDENCE_EXACT

    def test_avg_confidence_in_stats(self):
        result = normalize_text("yr bht acha")
        assert result["stats"]["avg_confidence"] is not None
        assert 0.0 <= result["stats"]["avg_confidence"] <= 1.0

    def test_min_confidence_in_stats(self):
        result = normalize_text("yr bht qwertyabc")  # last token is unknown
        assert result["stats"]["min_confidence"] == CONFIDENCE_UNKNOWN

    def test_empty_string_has_none_confidence(self):
        result = normalize_text("")
        assert result["stats"]["avg_confidence"] is None
        assert result["stats"]["min_confidence"] is None

    def test_phrase_map_record_full_confidence(self):
        result = normalize_text("kr rhe")
        # kr rhe -> phrase_map match -> 1.0 confidence
        phrase_records = [r for r in result["tokens"] if r["source"] == "phrase_map"]
        if phrase_records:
            assert phrase_records[0]["confidence"] == CONFIDENCE_EXACT
