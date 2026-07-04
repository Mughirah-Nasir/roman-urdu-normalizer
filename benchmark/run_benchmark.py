"""
Benchmark the Roman Urdu Normalizer against a hand-curated gold-standard
dataset of 100 real Pakistani Roman Urdu sentences.

Reports:
    - Sentence-level accuracy (exact match of normalized output)
    - Token-level precision / recall / F1
    - Per-category breakdown (greetings, family, food, ...)
    - Error analysis (which categories the normalizer fails on)

Usage:
    python -m benchmark.run_benchmark
    python -m benchmark.run_benchmark --json > results.json
    python -m benchmark.run_benchmark --verbose       # show every example

The gold-standard dataset (benchmark/gold_standard.jsonl) was curated by
Mughirah Nasir from real Pakistani WhatsApp / Twitter / SMS usage. Each
record has:
    id        — stable identifier
    category  — semantic category for per-bucket scoring
    input     — raw text as a Pakistani user would type it
    expected  — the correct normalized form
    notes     — human comment for traceability
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.console import ensure_utf8_stdout
from app.normalizer import normalize_text

# --------------------------------------------------------------------------
# Scoring primitives
# --------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


def _tokens(s: str) -> list[str]:
    """Lowercase word tokens — what we score on."""
    return [t.lower() for t in _TOKEN_RE.findall(s)]


def score_pair(predicted: str, expected: str) -> dict[str, Any]:
    """
    Score one prediction against one expected output.

    Token-level scoring:
        TP = tokens that are both in predicted and expected at the same position
        FP = tokens that appear in predicted but not at the matching expected position
        FN = tokens in expected that the prediction didn't produce at that position

    Sentence-level:
        exact = predicted == expected (case-insensitive, whitespace-normalized)
    """
    p_tokens = _tokens(predicted)
    e_tokens = _tokens(expected)

    # Sentence-level exact match
    def norm(s):
        return " ".join(s.split()).lower()
    exact = norm(predicted) == norm(expected)

    # Token-level positional matching — we align by index, which is fair for
    # a normalizer that should not change word order or token count.
    tp = sum(1 for p, e in zip(p_tokens, e_tokens, strict=False) if p == e)
    # Mismatches and missing alignment positions
    aligned_len = min(len(p_tokens), len(e_tokens))
    extra_predicted = max(0, len(p_tokens) - aligned_len)
    missing_predicted = max(0, len(e_tokens) - aligned_len)
    fp = (aligned_len - tp) + extra_predicted
    fn = (aligned_len - tp) + missing_predicted

    return {
        "exact": exact,
        "tp": tp, "fp": fp, "fn": fn,
        "predicted_tokens": p_tokens,
        "expected_tokens": e_tokens,
    }


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall    = tp / (tp + fn) if (tp + fn) else 0.0
    f1        = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1


# --------------------------------------------------------------------------
# Dataset loading
# --------------------------------------------------------------------------

def load_gold_standard(path: Path) -> list[dict[str, Any]]:
    records = []
    with open(path, encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"malformed line {line_no} in {path}: {e}") from e
    return records


# --------------------------------------------------------------------------
# Main loop
# --------------------------------------------------------------------------

def run_benchmark(verbose: bool = False, dataset_name: str = "gold_standard.jsonl") -> dict[str, Any]:
    gold_path = Path(__file__).parent / dataset_name
    gold = load_gold_standard(gold_path)

    overall = {"tp": 0, "fp": 0, "fn": 0, "exact": 0, "total": 0}
    by_category: dict[str, dict[str, int]] = defaultdict(
        lambda: {"tp": 0, "fp": 0, "fn": 0, "exact": 0, "total": 0}
    )
    errors: list[dict[str, Any]] = []

    for rec in gold:
        result = normalize_text(rec["input"])
        predicted = result["normalized"]
        score = score_pair(predicted, rec["expected"])

        cat = rec.get("category", "uncategorized")
        bucket = by_category[cat]
        for k in ("tp", "fp", "fn"):
            overall[k] += score[k]
            bucket[k] += score[k]
        overall["exact"] += int(score["exact"])
        bucket["exact"] += int(score["exact"])
        overall["total"] += 1
        bucket["total"] += 1

        if verbose or not score["exact"]:
            errors.append({
                "id": rec["id"],
                "category": cat,
                "input": rec["input"],
                "expected": rec["expected"],
                "predicted": predicted,
                "exact": score["exact"],
                "tp": score["tp"], "fp": score["fp"], "fn": score["fn"],
                "notes": rec.get("notes", ""),
            })

    p, r, f1 = precision_recall_f1(overall["tp"], overall["fp"], overall["fn"])
    summary = {
        "dataset": str(gold_path.name),
        "examples": overall["total"],
        "sentence_accuracy": overall["exact"] / overall["total"] if overall["total"] else 0.0,
        "token_precision": p,
        "token_recall": r,
        "token_f1": f1,
        "tp": overall["tp"], "fp": overall["fp"], "fn": overall["fn"],
        "by_category": {},
        "errors": errors,
    }
    for cat, b in sorted(by_category.items()):
        cp, cr, cf1 = precision_recall_f1(b["tp"], b["fp"], b["fn"])
        summary["by_category"][cat] = {
            "examples": b["total"],
            "exact_match": b["exact"],
            "sentence_accuracy": b["exact"] / b["total"] if b["total"] else 0.0,
            "precision": cp, "recall": cr, "f1": cf1,
        }
    return summary


# --------------------------------------------------------------------------
# Pretty printer
# --------------------------------------------------------------------------

def print_human(report: dict[str, Any]) -> None:
    def pct(x):
        return f"{x*100:5.1f}%"
    print()
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│           ROMAN URDU NORMALIZER — BENCHMARK RESULTS         │")
    print("├─────────────────────────────────────────────────────────────┤")
    print(f"│ Dataset:                {report['dataset']:<36s}│")
    print(f"│ Examples evaluated:     {report['examples']:<36d}│")
    print("├─────────────────────────────────────────────────────────────┤")
    print(f"│ Sentence-level accuracy:        {pct(report['sentence_accuracy']):<28s}│")
    print(f"│ Token-level precision:          {pct(report['token_precision']):<28s}│")
    print(f"│ Token-level recall:             {pct(report['token_recall']):<28s}│")
    print(f"│ Token-level F1:                 {pct(report['token_f1']):<28s}│")
    print("└─────────────────────────────────────────────────────────────┘")
    print()
    print("Per-category breakdown:")
    print(f"{'category':<22} {'N':>4} {'exact':>8} {'P':>7} {'R':>7} {'F1':>7}")
    print("─" * 62)
    for cat, m in sorted(report["by_category"].items(), key=lambda x: -x[1]["f1"]):
        print(f"{cat:<22} {m['examples']:>4d} {m['exact_match']:>8d} "
              f"{pct(m['precision']):>7} {pct(m['recall']):>7} {pct(m['f1']):>7}")
    print()

    misses = [e for e in report["errors"] if not e["exact"]]
    if misses:
        print(f"Errors: {len(misses)} / {report['examples']} sentences")
        print()
        for e in misses[:10]:
            print(f"  [{e['id']}] {e['category']}")
            print(f"    input:      {e['input']!r}")
            print(f"    expected:   {e['expected']!r}")
            print(f"    predicted:  {e['predicted']!r}")
            if e["notes"]:
                print(f"    note:       {e['notes']}")
            print()
        if len(misses) > 10:
            print(f"  ... and {len(misses) - 10} more (run with --json to see all)")


def main(argv: list[str] | None = None) -> int:
    ensure_utf8_stdout()  # box-drawing output crashes cp1252 consoles otherwise
    parser = argparse.ArgumentParser(prog="run_benchmark")
    parser.add_argument("--json", action="store_true",
                        help="emit full results as JSON to stdout")
    parser.add_argument("--verbose", action="store_true",
                        help="include every example (not just errors) in the report")
    parser.add_argument("--dataset", default="gold_standard.jsonl",
                        help="benchmark dataset filename inside benchmark/ "
                             "(default: gold_standard.jsonl; use "
                             "'gold_standard_adversarial.jsonl' for the perturbation set, "
                             "or 'combined' to evaluate both)")
    args = parser.parse_args(argv)

    if args.dataset == "combined":
        # Evaluate both base and adversarial, then merge
        base = run_benchmark(verbose=args.verbose, dataset_name="gold_standard.jsonl")
        adv  = run_benchmark(verbose=args.verbose, dataset_name="gold_standard_adversarial.jsonl")
        # Aggregate totals
        tp = base["tp"] + adv["tp"]
        fp = base["fp"] + adv["fp"]
        fn = base["fn"] + adv["fn"]
        exact = round(base["sentence_accuracy"] * base["examples"]) + round(adv["sentence_accuracy"] * adv["examples"])
        total = base["examples"] + adv["examples"]
        from benchmark.run_benchmark import precision_recall_f1
        p, r, f1 = precision_recall_f1(tp, fp, fn)
        report = {
            "dataset": "combined (hand-curated + adversarial)",
            "examples": total,
            "sentence_accuracy": exact / total if total else 0.0,
            "token_precision": p, "token_recall": r, "token_f1": f1,
            "tp": tp, "fp": fp, "fn": fn,
            "subsets": {
                "hand_curated": {"examples": base["examples"], "f1": base["token_f1"], "sentence_accuracy": base["sentence_accuracy"]},
                "adversarial":  {"examples": adv["examples"],  "f1": adv["token_f1"],  "sentence_accuracy": adv["sentence_accuracy"]},
            },
            "by_category": {**base["by_category"], **adv["by_category"]},
            "errors": (base["errors"] + adv["errors"])[:50],
        }
    else:
        report = run_benchmark(verbose=args.verbose, dataset_name=args.dataset)

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_human(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
