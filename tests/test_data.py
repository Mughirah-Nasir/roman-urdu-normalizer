"""Tests for dictionary integrity.

The data layer (variant map + canonical lexicon + homograph groups) needs
its own tests because it's the part of the system most likely to develop
inconsistencies during expansion. Catch the integrity bugs here, not in
production.
"""

from app.data import (
    CANONICAL_LEXICON,
    HOMOGRAPH_GROUPS,
    LEXICON_BY_CATEGORY,
    VARIANT_MAP,
    all_canonical_words,
    lexicon_stats,
)


class TestVariantMapIntegrity:

    def test_variant_map_is_dict(self):
        assert isinstance(VARIANT_MAP, dict)

    def test_variant_map_no_empty_keys(self):
        for k in VARIANT_MAP:
            assert k.strip(), "empty variant map key"

    def test_variant_map_no_empty_values(self):
        for v in VARIANT_MAP.values():
            assert v.strip(), "empty variant map value"

    def test_variant_map_is_substantial(self):
        # we want a real dictionary, not a toy
        assert len(VARIANT_MAP) >= 300

    def test_variant_map_values_are_canonical(self):
        """Every value in the variant map should either be in the canonical
        lexicon OR be a hyphenated compound (which we treat as canonical).
        """
        canon = all_canonical_words()
        for k, v in VARIANT_MAP.items():
            # values can be hyphenated compounds (e.g. "khuda-hafiz")
            if "-" in v or " " in v:
                continue
            assert v in canon, f"variant_map[{k!r}]={v!r} not in canonical lexicon"


class TestLexiconIntegrity:

    def test_lexicon_is_substantial(self):
        # production-grade dictionary, not a toy
        assert len(CANONICAL_LEXICON) >= 500

    def test_lexicon_no_empty_entries(self):
        for w in CANONICAL_LEXICON:
            assert w and w.strip()

    def test_lexicon_categories_disjoint_or_documented(self):
        """Categories may overlap (some words are noun+verb), but every
        word in CANONICAL_LEXICON should appear in at least one category."""
        union = set()
        for cat_words in LEXICON_BY_CATEGORY.values():
            union |= cat_words
        # Every canonical word should be reachable via at least one category
        missing = CANONICAL_LEXICON - union
        assert not missing, f"words in lexicon but no category: {missing}"

    def test_no_lexicon_word_starts_or_ends_with_space(self):
        for w in CANONICAL_LEXICON:
            assert w == w.strip()


class TestHomographIntegrity:

    def test_homograph_groups_is_list_of_sets(self):
        assert isinstance(HOMOGRAPH_GROUPS, list)
        for g in HOMOGRAPH_GROUPS:
            assert isinstance(g, set)

    def test_homograph_members_in_lexicon(self):
        """Every word in a homograph group must be in the canonical lexicon —
        otherwise the phonetic index won't index it and the guard does nothing.
        """
        for group in HOMOGRAPH_GROUPS:
            for word in group:
                assert word in CANONICAL_LEXICON, (
                    f"homograph member {word!r} missing from lexicon"
                )

    def test_homograph_groups_have_multiple_members(self):
        # a group of one isn't a homograph
        for group in HOMOGRAPH_GROUPS:
            assert len(group) >= 2, f"singleton homograph group: {group}"

    def test_no_duplicate_homograph_groups(self):
        seen = []
        for g in HOMOGRAPH_GROUPS:
            assert g not in seen, f"duplicate homograph group: {g}"
            seen.append(g)


class TestLexiconStats:

    def test_stats_returns_dict(self):
        s = lexicon_stats()
        assert isinstance(s, dict)
        assert "variant_map_entries" in s
        assert "canonical_total" in s
        assert "by_category" in s

    def test_stats_numbers_consistent(self):
        s = lexicon_stats()
        assert s["variant_map_entries"] == len(VARIANT_MAP)
        assert s["canonical_total"] == len(CANONICAL_LEXICON)
        assert s["homograph_groups"] == len(HOMOGRAPH_GROUPS)
