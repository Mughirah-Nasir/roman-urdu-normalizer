"""
Integration showcase #1 — search recall before vs after normalization.

This script demonstrates a concrete downstream win from normalizing
Roman Urdu: a Pakistani e-commerce site searching customer reviews.

It builds a small corpus of realistic Pakistani Roman Urdu reviews
(mixing spelling variants), then runs the same set of queries against
both the raw corpus and the normalized corpus. The recall difference
is the value proposition of this entire project, made measurable.

Run (the API must be running at http://localhost:8000):

    python examples/search_recall_demo.py

Output: a side-by-side comparison table for each query, plus a
summary row showing the average recall lift.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client import RomanUrduNormalizerClient


# --------------------------------------------------------------------------
# A realistic Pakistani e-commerce review corpus.
# Mix of spellings deliberate. Every review is something a Pakistani user
# could plausibly type.
# --------------------------------------------------------------------------
REVIEWS = [
    "shipping nai aya time pe yr",
    "quality nahin acha tha bilkul",
    "main satisfied nahi hun is product se",
    "kahan se kharida nai pta yad nahi",
    "kch bhi nai aya box me empty tha",
    "delivery bohat late hai ye to",
    "yaar mera order abhi tk nahi mila",
    "product theek hai but late delivery ki bnaa pe issue hua",
    "warranty card nai mila order ke saath",
    "bht acha product hai recommended",
    "bohat acha hai bndy seller",
    "bahut acha quality ka cheez hai",
    "scene off hai yr delivery wala bnda",
    "main bht khush hun is purchase se",
    "wo packaging bilkul kharab thi",
    "kuch bhi expected jaisa nai hai",
    "shukria seller ki taraf se",
    "kal mil gaya finally",
    "abhi tk koi response nahi mila support se",
    "ami ne kha k dobara nahi lena yahan se",
    "battery jaldi khatam ho jati hai bohat",
    "wifi nahi chal raha after update",
    "screen pe error a rha hai abhi b",
    "boss ne meeting bulai hai kal subah",
    "bhai chill kr ye to common issue hai",
]


# --------------------------------------------------------------------------
# Queries — canonical forms a normal search would expect.
# --------------------------------------------------------------------------
QUERIES = [
    ("nahi",       "negation — common in complaints"),
    ("bahut",      "intensifier — common in 'very good/bad' reviews"),
    ("nahin",      "alternate negation spelling"),
    ("delivery",   "English noun — should work either way"),
    ("kuch",       "indefinite pronoun"),
    ("acha",       "common adjective 'good'"),
    ("abhi",       "'now' / 'still'"),
    ("ammi",       "'mom' — Pakistani specific"),
]


def search_naive(corpus: list[str], query: str) -> list[int]:
    """Substring match on raw corpus. Returns list of indices that match."""
    q = query.lower()
    return [i for i, doc in enumerate(corpus) if q in doc.lower()]


def main() -> int:
    client = RomanUrduNormalizerClient("http://localhost:8000")

    # Verify the API is up
    try:
        health = client.health()
        print(f"API status: {health['status']}, lexicon size: {health['lexicon_size']}\n")
    except Exception as e:
        print(f"ERROR: could not reach the API. Is `uvicorn app.main:app` running?\n{e}")
        return 1

    # Normalize the corpus through the API
    print(f"Normalizing {len(REVIEWS)} reviews...")
    normalized_reviews = client.normalize_chunks(REVIEWS)
    normalized_corpus = [r["normalized"] for r in normalized_reviews]
    print("Done.\n")

    # Run every query against both corpora
    print("=" * 78)
    print(f"{'QUERY':<14} {'note':<38} {'before':>8} {'after':>8} {'lift':>8}")
    print("=" * 78)

    total_before = 0
    total_after = 0
    for query, note in QUERIES:
        before = search_naive(REVIEWS, query)
        after = search_naive(normalized_corpus, query)
        lift = len(after) - len(before)
        lift_str = f"+{lift}" if lift > 0 else str(lift)
        total_before += len(before)
        total_after += len(after)
        print(f"{query:<14} {note:<38} {len(before):>8} {len(after):>8} {lift_str:>8}")

    print("=" * 78)
    print(f"{'TOTAL':<14} {'(sum of matches across all queries)':<38} "
          f"{total_before:>8} {total_after:>8} {total_after - total_before:+d}")
    print()

    if total_before > 0:
        lift_pct = ((total_after / total_before) - 1.0) * 100
        print(f"Recall lift across all queries: {lift_pct:+.1f}% "
              f"({total_before} -> {total_after} hits)")
    else:
        print(f"Recall lift: {total_before} -> {total_after} hits "
              f"(infinite multiplier — every match came from normalization)")

    print()
    print("Reading the table:")
    print("  - 'before' = naive substring match against raw reviews")
    print("  - 'after'  = same search after every review went through the normalizer")
    print("  - The lift on 'nahi' (negation) is the headline:")
    print("    spelling variants (nai, nahin, nahi, nahee) collapse to one.")
    print()
    print("This is the same pattern that fires for: deduplication,")
    print("classification preprocessing, LLM prompt cleaning, BI analytics.")
    print("Normalization is the cheap preprocessing step that makes downstream work.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
