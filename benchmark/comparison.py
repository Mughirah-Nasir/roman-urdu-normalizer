"""
Baseline comparison study.

Compares the four-layer Roman Urdu Normalizer against three simpler baselines:

    Baseline A — naive_replace
        Iterate the variant map; for each (key, value) do a global string
        replace on the input. This is what someone might write in 20 minutes.

    Baseline B — levenshtein_nearest
        For each token, find the canonical word with the smallest edit
        distance and resolve to it (ties broken alphabetically). This is
        what someone might write in an afternoon if they wanted "fuzzy
        matching" without understanding phonetics.

    Baseline C — tfidf_char_ngram (ML, NEW in v1.2)
        For each token, vectorize as character bigrams + trigrams + 4-grams
        (TF-IDF), find the canonical word with highest cosine similarity,
        resolve to it if similarity > threshold. This is a real ML baseline
        — the kind of thing a senior engineer would actually try before
        writing custom rules. Trained on the canonical lexicon only (no
        external data).

The comparison is on the same 100-example gold-standard dataset used by
the main benchmark. Reporting precision/recall/F1 for each.

Result we expect (and report in the README):
    - Naive replace is fast but FN-heavy (misses anything not exactly in the map)
    - Levenshtein nearest is recall-happy but precision-poor (silently
      rewrites correct words to lexicon neighbors)
    - TF-IDF char n-gram is the strongest baseline but still gets blocked
      by Roman Urdu's spelling chaos — chars alone don't capture phonology
    - Our four-layer pipeline beats all three on F1 — and crucially
      preserves the "never silently guess" contract that none of them can.

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

from app.data import CANONICAL_LEXICON, VARIANT_MAP
from app.normalizer import normalize_text
from benchmark.run_benchmark import load_gold_standard, precision_recall_f1, score_pair

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


# --- ML baseline: TF-IDF over character n-grams ---------------------------

_TFIDF_MODEL = None  # lazy-built singleton

def _build_tfidf_model():
    """Lazy-build the TF-IDF model on first call. Uses char-bigram through
    4-gram features over the canonical lexicon."""
    global _TFIDF_MODEL
    if _TFIDF_MODEL is not None:
        return _TFIDF_MODEL
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError as e:
        raise RuntimeError(
            "scikit-learn is required for the ML baseline. "
            "Install with: pip install scikit-learn"
        ) from e
    vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
    canonical_words = _LEXICON_LIST
    canonical_matrix = vectorizer.fit_transform(canonical_words)
    _TFIDF_MODEL = (vectorizer, canonical_matrix, canonical_words)
    return _TFIDF_MODEL


def tfidf_char_ngram(text: str, threshold: float = 0.45) -> str:
    """
    ML baseline: for each token, find the canonical word with the highest
    TF-IDF cosine similarity. Replace if similarity > threshold; otherwise
    pass through.

    This is a real trained model — vectorizer fit on the canonical lexicon
    with character bigrams through 4-grams. The threshold is conservative
    (0.45) to avoid the precision collapse that plagues Levenshtein.
    """
    from sklearn.metrics.pairwise import cosine_similarity
    vectorizer, canonical_matrix, canonical_words = _build_tfidf_model()

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
        tok_vec = vectorizer.transform([token])
        sims = cosine_similarity(tok_vec, canonical_matrix).flatten()
        best_idx = sims.argmax()
        if sims[best_idx] >= threshold:
            out.append(canonical_words[best_idx])
        else:
            out.append(token)
    return "".join(out)


def four_layer(text: str) -> str:
    return normalize_text(text)["normalized"]


# --- scoring loop ---------------------------------------------------------

def score_strategy(name: str, fn, gold: list[dict]) -> dict:
    tp = fp = fn_ = 0
    exact = 0
    for rec in gold:
        predicted = fn(rec["input"])
        score = score_pair(predicted, rec["expected"])
        tp += score["tp"]
        fp += score["fp"]
        fn_ += score["fn"]
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
    parser.add_argument("--dataset", default="combined",
                        help="benchmark dataset to score against. Use 'combined' "
                             "(default) for hand-curated + adversarial, or a "
                             "specific filename like 'gold_standard.jsonl'.")
    args = parser.parse_args(argv)

    bench_dir = Path(__file__).parent
    if args.dataset == "combined":
        gold = load_gold_standard(bench_dir / "gold_standard.jsonl")
        gold += load_gold_standard(bench_dir / "gold_standard_adversarial.jsonl")
        dataset_label = "combined (hand-curated + adversarial)"
    else:
        gold = load_gold_standard(bench_dir / args.dataset)
        dataset_label = args.dataset

    results = [
        score_strategy("Baseline A · naive_replace",       naive_replace,        gold),
        score_strategy("Baseline B · levenshtein",         levenshtein_nearest,  gold),
        score_strategy("Baseline C · tfidf_char_ngram",    tfidf_char_ngram,     gold),
        score_strategy("Ours · four_layer",                four_layer,           gold),
    ]

    if args.json:
        print(json.dumps(results, indent=2))
        return 0

    def pct(x):
        return f"{x*100:5.1f}%"
    print()
    print("┌──────────────────────────────────────────────────────────────────────┐")
    print("│        ROMAN URDU NORMALIZER — BASELINE COMPARISON STUDY             │")
    print(f"│        Dataset: {dataset_label:<55s}│")
    print("├──────────────────────────────────────────────────────────────────────┤")
    print(f"│ {'strategy':<32s} {'exact':>7} {'P':>7} {'R':>7} {'F1':>7} │")
    print("├──────────────────────────────────────────────────────────────────────┤")
    for r in results:
        print(f"│ {r['strategy']:<32s} {pct(r['sentence_accuracy']):>7} "
              f"{pct(r['precision']):>7} {pct(r['recall']):>7} {pct(r['f1']):>7} │")
    print("└──────────────────────────────────────────────────────────────────────┘")
    print()
    print("Reading the table:")
    print("  - naive_replace is order-dependent and over-substitutes")
    print("  - levenshtein has no phonetics — silently rewrites correct words")
    print("  - tfidf_char_ngram is a real ML baseline (TF-IDF + cosine similarity)")
    print("    but character similarity ≠ phonetic similarity for Roman Urdu")
    print("  - four_layer preserves 'never silently guess' — unknowns pass through")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
