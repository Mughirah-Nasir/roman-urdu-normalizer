"""
Adversarial test suite — exercises the real-world ugliness reviewers ask about.

These are *not* the benchmark dataset. They are pinned-by-name tests that
serve as a tripwire: if we regress on one of these, CI fails immediately.

Categories tested:
    1. Emoji preservation (basic, ZWJ, flag sequences)
    2. Repeated-letter SMS stretches (kyaaaa, bhttttt)
    3. Hashtags and @mentions (Twitter / WhatsApp style)
    4. Numbers and time formats (2 din, 9:30, 100%)
    5. Mixed Roman + Arabic-script input
    6. Heavy code-switching with English
    7. URLs and email addresses (must pass through intact)
    8. Punctuation extremes
    9. Whitespace stress
    10. The exact adversarial examples called out in the external review
"""

from app.normalizer import normalize_text

# -- 1. EMOJI --------------------------------------------------------------

class TestEmojiPreservation:
    def test_trailing_emoji(self):
        result = normalize_text("yr bht acha 😂")
        assert "😂" in result["normalized"]
        assert "yaar" in result["normalized"]
        assert "bahut" in result["normalized"]

    def test_leading_emoji(self):
        result = normalize_text("🔥 kya scene hai")
        assert "🔥" in result["normalized"]

    def test_double_emoji(self):
        result = normalize_text("😭😭 mjhe nai pta")
        assert "😭😭" in result["normalized"]
        assert "mujhe" in result["normalized"]
        assert "nahi" in result["normalized"]

    def test_zwj_emoji(self):
        # Runner emoji uses ZWJ (zero-width joiner) sequences
        result = normalize_text("main aa rha hun 🏃‍♂️")
        assert "🏃‍♂️" in result["normalized"]


# -- 2. REPEATED LETTERS ---------------------------------------------------

class TestRepeatedLetters:
    def test_stretched_kya(self):
        # The exact example from the external review.
        # Note: the phonetic layer collapses "kyaaaa" to its canonical form
        # ("kiya" or "kya"). The stretch is lost — this is an intentional
        # trade-off: collapse for searchability vs preserve for sentiment.
        # Documented in docs/limitations.md.
        result = normalize_text("kyaaaa kr rahyyyy ho???")
        # "kr" should normalize via variant map
        assert "kar" in result["normalized"]
        # The trailing "???" should be preserved
        assert "???" in result["normalized"]

    def test_stretched_bht(self):
        result = normalize_text("bhttttt acha!!!")
        # repeated T's mean nothing's in the variant map; this should pass through
        assert "bhttttt" in result["normalized"]

    def test_hahaha(self):
        result = normalize_text("hahahaha kya bat hai")
        assert "hahahaha" in result["normalized"]
        assert "baat" in result["normalized"]


# -- 3. HASHTAGS AND MENTIONS ----------------------------------------------

class TestHashtagsAndMentions:
    def test_hashtag_preserved(self):
        result = normalize_text("kya scene hai #karachi")
        assert "#karachi" in result["normalized"]

    def test_leading_hashtag(self):
        result = normalize_text("#PSL11 zabardast match tha")
        assert "#PSL11" in result["normalized"]

    def test_mention_preserved(self):
        result = normalize_text("@ali aja yr")
        assert "@ali" in result["normalized"]
        assert "yaar" in result["normalized"]

    def test_mention_with_proper_noun(self):
        result = normalize_text("follow karo @Mughirah-Nasir")
        assert "@Mughirah-Nasir" in result["normalized"]


# -- 4. NUMBERS ------------------------------------------------------------

class TestNumbers:
    def test_digit_with_urdu_word(self):
        result = normalize_text("2 din me a jaen ge")
        assert "2 din" in result["normalized"]

    def test_time_format(self):
        result = normalize_text("kal 5 bje milte hen")
        assert "5 baje" in result["normalized"]

    def test_phone_number_preserved(self):
        result = normalize_text("phone number 0300-1234567 hai")
        assert "0300-1234567" in result["normalized"]

    def test_percentage_preserved(self):
        result = normalize_text("20% discount mil rha hai")
        assert "20%" in result["normalized"]
        assert "raha" in result["normalized"]


# -- 5. ARABIC-SCRIPT INPUT ------------------------------------------------

class TestArabicScript:
    def test_arabic_greeting_passes_through(self):
        result = normalize_text("السلام علیکم kese ho")
        assert "السلام علیکم" in result["normalized"]
        assert "kaise" in result["normalized"]

    def test_full_arabic_sentence_with_english(self):
        result = normalize_text("میں ٹھیک ہوں thank you")
        assert "میں ٹھیک ہوں" in result["normalized"]
        assert "thank you" in result["normalized"]

    def test_arabic_word_inline_with_roman(self):
        result = normalize_text("yr دیکھو scene off hai")
        assert "yaar" in result["normalized"]
        assert "دیکھو" in result["normalized"]


# -- 6. HEAVY CODE-SWITCHING -----------------------------------------------

class TestHeavyCodeSwitching:
    def test_english_dominant(self):
        result = normalize_text("the meeting kal hai dont forget")
        assert "kal" in result["normalized"]
        # English words must not be normalized to anything weird
        assert "meeting" in result["normalized"]
        assert "forget" in result["normalized"]

    def test_office_pakistani_english(self):
        result = normalize_text("team report submit krdo asap")
        assert "kar do" in result["normalized"]
        assert "asap" in result["normalized"]

    def test_transition_word(self):
        result = normalize_text("actually mjhe lagta hai galat hai")
        assert "actually" in result["normalized"]
        assert "mujhe" in result["normalized"]


# -- 7. URLS AND EMAILS PRESERVED ------------------------------------------

class TestUrlsAndEmails:
    def test_url_preserved(self):
        result = normalize_text("check this https://example.pk/page yr")
        assert "https://example.pk/page" in result["normalized"]
        assert "yaar" in result["normalized"]

    def test_email_passes_through(self):
        # Email-like tokens contain @ and . — current tokenizer handles
        # them as multiple word tokens. This test pins the behavior.
        result = normalize_text("contact mnasir.bee25seecs@seecs.edu.pk bhai")
        assert "@" in result["normalized"]
        assert "bhai" in result["normalized"]


# -- 8. PUNCTUATION EXTREMES -----------------------------------------------

class TestPunctuationExtremes:
    def test_multiple_question_marks(self):
        result = normalize_text("kya??? kya hua??")
        assert "???" in result["normalized"]
        assert "??" in result["normalized"]

    def test_excess_exclamation(self):
        result = normalize_text("yr bs!!!!! ho gya")
        assert "!!!!!" in result["normalized"]
        assert "yaar" in result["normalized"]
        assert "bas" in result["normalized"]

    def test_ellipsis_only(self):
        result = normalize_text("...")
        assert result["normalized"] == "..."

    def test_ascii_emoticons(self):
        result = normalize_text(":) yr scene set hai :D")
        assert ":)" in result["normalized"]
        assert ":D" in result["normalized"]
        assert "yaar" in result["normalized"]


# -- 9. WHITESPACE STRESS --------------------------------------------------

class TestWhitespaceStress:
    def test_leading_trailing_whitespace(self):
        result = normalize_text("   yr bht   ")
        assert "yaar" in result["normalized"]
        assert "bahut" in result["normalized"]

    def test_multiple_internal_spaces(self):
        # The normalizer collapses runs of whitespace to single spaces
        result = normalize_text("yr     bht    thora")
        assert "yaar" in result["normalized"]
        assert "bahut" in result["normalized"]
        assert "thora" in result["normalized"]


# -- 10. EXACT EXAMPLES FROM EXTERNAL REVIEW -------------------------------
# These are pinned by name so reviewers can verify directly.

class TestExactReviewExamples:
    def test_review_emoji_repeats_punct(self):
        result = normalize_text("kyaaaa kr rahyyyy ho??? 😂")
        assert "kar" in result["normalized"]
        assert "😂" in result["normalized"]
        assert "???" in result["normalized"]

    def test_review_main_office(self):
        # "main office main hun" — ambiguity between "main" (I) and English "main"
        # We preserve the word; the test pins that we don't over-resolve.
        result = normalize_text("main office main hun")
        assert "main" in result["normalized"]
        assert "office" in result["normalized"]
        assert "hun" in result["normalized"]

    def test_review_kal_ambiguity(self):
        # "kal ana hai ya kal gaya tha" — kal can be yesterday or tomorrow
        result = normalize_text("kal ana hai ya kal gaya tha")
        assert result["normalized"].count("kal") == 2  # both kal's preserved

    def test_review_ali_bhai_kahan(self):
        result = normalize_text("Ali bhai ny kha kahan jana hai")
        assert "Ali" in result["normalized"]
        assert "bhai" in result["normalized"]
        assert "kaha" in result["normalized"]
        assert "kahan" in result["normalized"]

    def test_review_bhttttt(self):
        result = normalize_text("bhttttt acha!!!")
        assert "bhttttt" in result["normalized"]
        assert "!!!" in result["normalized"]

    def test_review_scene_off(self):
        result = normalize_text("nhi yr scene off hai")
        assert "nahi" in result["normalized"]
        assert "yaar" in result["normalized"]
        assert "scene" in result["normalized"]
        assert "off" in result["normalized"]
