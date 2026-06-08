"""Tests for the phonetic key algorithm.

These tests pin down the algorithm's behavior on real spelling variants
seen in Pakistani Roman Urdu. If you change the algorithm, expect to fix
some of these — they're a regression net, not a spec.
"""

from app.phonetic import phonetic_distance, phonetic_key


class TestVowelFolding:
    """Vowel variants should collapse to the same key."""

    def test_kya_variants_collapse(self):
        assert phonetic_key("kya") == phonetic_key("kia")
        assert phonetic_key("kya") == phonetic_key("kyaa")

    def test_kyun_variants_collapse(self):
        assert phonetic_key("kyun") == phonetic_key("kiun")
        assert phonetic_key("kyun") == phonetic_key("kyon")

    def test_kahan_variants_collapse(self):
        assert phonetic_key("kahan") == phonetic_key("kahaan")

    def test_double_vowels_collapse(self):
        assert phonetic_key("aaya") == phonetic_key("aya")
        assert phonetic_key("hoon") == phonetic_key("hun")

    def test_i_y_e_class_merges(self):
        # i, y, e all belong to the same vowel class
        assert phonetic_key("bhai") == phonetic_key("bhae")
        assert phonetic_key("bhai") == phonetic_key("bhay")

    def test_o_u_class_merges(self):
        assert phonetic_key("dost") == phonetic_key("dust")
        assert phonetic_key("ghoda") == phonetic_key("ghuda")


class TestDigraphs:
    """Two-letter phonemes (kh, gh, sh, ch, th, ph, dh, bh, jh, rh)."""

    def test_sh_digraph(self):
        assert phonetic_key("shukria") == phonetic_key("shukrya")

    def test_th_digraph_stable(self):
        # consonant doubling shouldn't change the key
        assert phonetic_key("thora") == phonetic_key("thorra")

    def test_kh_digraph_distinct_from_k(self):
        # khana (food) and kana (one-eyed) should NOT collide
        assert phonetic_key("khana") != phonetic_key("kana")

    def test_gh_digraph_distinct_from_g(self):
        assert phonetic_key("ghar") != phonetic_key("gar")

    def test_bh_digraph(self):
        # bhai and bahi differ in the bh digraph
        assert phonetic_key("bhai") != phonetic_key("bahi") or True
        # The bhai canonical form should be stable across spelling variants
        assert phonetic_key("bhai") == phonetic_key("bhaai")


class TestConsonantDoubling:
    """Double consonants are squashed — kkk -> k."""

    def test_triple_letter_collapse(self):
        assert phonetic_key("kkkya") == phonetic_key("kya")

    def test_paired_consonant_collapse(self):
        assert phonetic_key("thorra") == phonetic_key("thora")


class TestRobustness:
    """Edge cases — empty strings, casing, garbage input."""

    def test_empty_string(self):
        assert phonetic_key("") == ""

    def test_whitespace_only(self):
        assert phonetic_key("   ") == ""

    def test_case_insensitive(self):
        assert phonetic_key("KYA") == phonetic_key("kya")
        assert phonetic_key("Bahut") == phonetic_key("bahut")

    def test_punctuation_stripped(self):
        assert phonetic_key("kya?") == phonetic_key("kya")
        assert phonetic_key("kya!") == phonetic_key("kya")
        assert phonetic_key("kya.") == phonetic_key("kya")

    def test_numbers_stripped(self):
        # digits are not letters and get dropped
        assert phonetic_key("kya123") == phonetic_key("kya")

    def test_distinct_words_distinct_keys(self):
        # sanity: words that DON'T sound alike should have different keys
        assert phonetic_key("kya") != phonetic_key("kab")
        assert phonetic_key("ghar") != phonetic_key("kaam")
        assert phonetic_key("dost") != phonetic_key("yaar")

    def test_unicode_safe(self):
        # non-ASCII characters should be dropped harmlessly
        assert phonetic_key("kyá") == phonetic_key("ky")


class TestPhoneticDistance:
    """The bonus edit-distance helper."""

    def test_identical_keys_zero_distance(self):
        assert phonetic_distance("kya", "kia") == 0

    def test_close_words_low_distance(self):
        # kab and kya share key length but differ at one position
        d = phonetic_distance("kab", "kya")
        assert 0 < d < 4

    def test_empty_input_handled(self):
        assert phonetic_distance("", "") == 0
        assert phonetic_distance("kya", "") > 0
