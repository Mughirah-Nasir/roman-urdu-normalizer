"""
Baseline comparison study.

Compares the three-layer Roman Urdu Normalizer against two simpler baselines:

    Baseline A — naive_replace
        Iterate the variant map; for each (key, value) do a global string
        replace on the input. This is what someone might write in 20 minutes.

    Baseline B — levenshtein_nearest
        For each token, find the canonical word with the smallest edit
        distance and resolve to it (ties broken alphabetically). This is
        what someone might write in an afternoon if they wanted "fuzzy
        matching" without understanding phonetics.

The comparison is on the same 100-example gold-standard dataset used by
the main benchmark. Reporting precision/recall/F1 for each.

Result we expect (and report in the README):
    - Naive replace is fast but FN-heavy (misses anything not exactly in the map)
    - Levenshtein nearest is recall-happy but precision-poor (silently
      rewrites correct words to lexicon neighbors)
    - Our three-layer pipeline beats both on F1 — and crucially preserves
      the "never silently guess" contract that Levenshtein cannot.

Usage:
    python -m benchmark.comparison
    python -m benchmark.comparison --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from app.data import VARIANT_MAP, CANONICAL_LEXICON
from app.normalizer import normalize_text
from benchmark.run_benchmark import load_gold_standard, score_pair, precision_recall_f1


_TOKEN_RE = re.compile(r"(\w+|\W+)", re.UNICODE)


# --- baselines ------------------------------------------------------------

def naive_replace(text: str) -> str:
    """
    Iterate the variant map and do dumb str.replace for each entry.
    Order-sensitive (bug-by-design — this is the baseline).
    """
    out = text
    for k, v in VARIANT_MAP.items():
        out = out.replace(k, v)
    return out


def _levenshtein(a: str, b: str) -> int:
    """Edit distance, iterative DP. O(len(a) * len(b))."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(
                prev[j] + 1,                # delete
                cur[-1] + 1,                # insert
                prev[j-1] + (0 if ca == cb else 1),  # substitute
            ))
        prev = cur
    return prev[-1]


_LEXICON_LIST = sorted(CANONICAL_LEXICON)


def levenshtein_nearest(text: str, max_distance: int = 2) -> str:
    """For each word token, find the canonical word with smallest edit
    distance and replace. Punctuation/whitespace untouched.
    """
    pieces = _TOKEN_RE.findall(text)
    out: list[str] = []
    for piece in pieces:
        if not any(c.isalnum() for c in piece):
            out.append(piece)
            continue
        token = piece.lower()
        if token in CANONICAL_LEXICON:
            out.append(token)
            continue
        best_word, best_dist = token, max_distance + 1
        for w in _LEXICON_LIST:
            # Quick reject by length difference
            if abs(len(w) - len(token)) > max_distance:
                continue
            d = _levenshtein(token, w)
            if d < best_dist:
                best_word, best_dist = w, d
        out.append(best_word if best_dist <= max_distance else token)
    return "".join(out)


def three_layer(text: str) -> str:
    return normalize_text(text)["normalized"]


# --- scoring loop ---------------------------------------------------------

def score_strategy(name: str, fn, gold: list[dict]) -> dict:
    tp = fp = fn_ = 0
    exact = 0
    for rec in gold:
        predicted = fn(rec["input"])
        score = score_pair(predicted, rec["expected"])
        tp += score["tp"]; fp += score["fp"]; fn_ += score["fn"]
        exact += int(score["exact"])
    p, r, f1 = precision_recall_f1(tp, fp, fn_)
    return {
        "strategy": name,
        "examples": len(gold),
        "exact_match": exact,
        "sentence_accuracy": exact / len(gold) if gold else 0.0,
        "precision": p, "recall": r, "f1": f1,
        "tp": tp, "fp": fp, "fn": fn_,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="comparison")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    gold_path = Path(__file__).parent / "gold_standard.jsonl"
    gold = load_gold_standard(gold_path)

    results = [
        score_strategy("Baseline A · naive_replace",   naive_replace,        gold),
        score_strategy("Baseline B · levenshtein",     levenshtein_nearest,  gold),
        score_strategy("Ours · three_layer",            three_layer,          gold),
    ]

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    pct = lambda x: f"{x*100:5.1f}%"
    print()
    print("┌──────────────────────────────────────────────────────────────────────┐")
    print("│        ROMAN URDU NORMALIZER — BASELINE COMPARISON STUDY             │")
    print("│        Gold-standard dataset: 100 hand-curated examples              │")
    print("├──────────────────────────────────────────────────────────────────────┤")
    print(f"│ {'strategy':<32s} {'exact':>7} {'P':>7} {'R':>7} {'F1':>7} │")
    print("├──────────────────────────────────────────────────────────────────────┤")
    for r in results:
        print(f"│ {r['strategy']:<32s} {pct(r['sentence_accuracy']):>7} "
              f"{pct(r['precision']):>7} {pct(r['recall']):>7} {pct(r['f1']):>7} │")
    print("└──────────────────────────────────────────────────────────────────────┘")
    print()
    print("Reading the table:")
    print("  - naive_replace is order-dependent and order-fragile (over-eager substitutions)")
    print("  - levenshtein has no notion of phonetics — it silently rewrites correct words")
    print("  - three_layer preserves the 'never silently guess' contract — unknowns pass through")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
