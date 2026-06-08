"""
Render the benchmark results into a chart for the README.

Produces two PNGs in docs/:
    docs/benchmark_by_category.png  — F1 by category, sorted descending
    docs/benchmark_vs_baselines.png — F1 comparison vs naive_replace and levenshtein

Run this after updating the gold-standard dataset or any normalizer code:
    python -m benchmark.render_charts

Dev-time only — matplotlib is in requirements-dev.txt, not in runtime deps.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from benchmark.run_benchmark import load_gold_standard, run_benchmark

# Brand palette (matches the frontend + docs)
SAFFRON = "#e8a33d"
JADE    = "#5fb39a"
RUST    = "#c97a4c"
BG      = "#0f0e0c"
PANEL   = "#181613"
INK     = "#f5efe3"
MUTE    = "#b8b0a1"
DIM     = "#6e685c"
BORDER  = "#2a261f"


def _apply_dark_theme(fig, ax):
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for spine_pos in ("left", "bottom"):
        ax.spines[spine_pos].set_color(BORDER)
    for spine_pos in ("top", "right"):
        ax.spines[spine_pos].set_visible(False)
    ax.tick_params(colors=DIM)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_color(INK)
    ax.yaxis.label.set_color(MUTE)
    ax.xaxis.label.set_color(MUTE)
    ax.title.set_color(INK)
    ax.grid(axis="y", color=BORDER, linewidth=0.5, alpha=0.5)
    ax.set_axisbelow(True)


def render_by_category(out_path: Path) -> None:
    report = run_benchmark()
    items = sorted(report["by_category"].items(), key=lambda x: -x[1]["f1"])
    # Drop edge_empty — F1 is 0% by token-metric definition (no tokens), misleading on chart
    items = [(c, m) for c, m in items if c != "edge_empty"]
    categories = [c for c, _ in items]
    f1s = [m["f1"] * 100 for _, m in items]

    fig, ax = plt.subplots(figsize=(12, 7))
    _apply_dark_theme(fig, ax)

    bars = ax.bar(categories, f1s, color=SAFFRON, edgecolor=BORDER, linewidth=0.5)
    # Color bars by tier
    for bar, f1 in zip(bars, f1s, strict=False):
        if f1 >= 90:
            bar.set_color(JADE)
        elif f1 >= 75:
            bar.set_color(SAFFRON)
        else:
            bar.set_color(RUST)

    ax.set_ylim(0, 105)
    ax.set_ylabel("F1 (%)", fontsize=11)
    ax.set_title("Token-level F1 by category — gold-standard dataset (100 examples)",
                 fontsize=13, pad=18, loc="left")
    plt.setp(ax.get_xticklabels(), rotation=40, ha="right", fontsize=9)

    # Add value labels on bars
    for bar, f1 in zip(bars, f1s, strict=False):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{f1:.0f}", ha="center", va="bottom", color=DIM, fontsize=8)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor=BG)
    plt.close(fig)
    print(f"wrote {out_path}")


def render_vs_baselines(out_path: Path) -> None:
    gold_path = Path(__file__).parent / "gold_standard.jsonl"
    gold = load_gold_standard(gold_path)
    from benchmark.comparison import (
        four_layer,
        levenshtein_nearest,
        naive_replace,
        score_strategy,
        tfidf_char_ngram,
    )
    results = [
        score_strategy("naive_replace",   naive_replace,        gold),
        score_strategy("levenshtein",     levenshtein_nearest,  gold),
        score_strategy("tfidf (ML)",      tfidf_char_ngram,     gold),
        score_strategy("four_layer",      four_layer,           gold),
    ]
    labels = [r["strategy"] for r in results]
    sentence_acc = [r["sentence_accuracy"] * 100 for r in results]
    f1 = [r["f1"] * 100 for r in results]

    fig, ax = plt.subplots(figsize=(10, 6))
    _apply_dark_theme(fig, ax)

    x = range(len(labels))
    width = 0.35
    b1 = ax.bar([i - width / 2 for i in x], sentence_acc,
                width, label="Sentence accuracy", color=SAFFRON, edgecolor=BORDER, linewidth=0.5)
    b2 = ax.bar([i + width / 2 for i in x], f1,
                width, label="Token F1", color=JADE, edgecolor=BORDER, linewidth=0.5)

    ax.set_ylim(0, 105)
    ax.set_ylabel("Score (%)", fontsize=11)
    ax.set_title("Baseline comparison — incl. TF-IDF char n-gram ML baseline",
                 fontsize=13, pad=18, loc="left")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, color=INK, fontsize=10)
    legend = ax.legend(facecolor=PANEL, edgecolor=BORDER, labelcolor=INK)
    legend.get_frame().set_alpha(0.9)

    for bars in (b1, b2):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                    f"{bar.get_height():.1f}", ha="center", va="bottom",
                    color=DIM, fontsize=9)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor=BG)
    plt.close(fig)
    print(f"wrote {out_path}")


def main() -> int:
    docs_dir = Path(__file__).parent.parent / "docs"
    docs_dir.mkdir(exist_ok=True)
    render_by_category(docs_dir / "benchmark_by_category.png")
    render_vs_baselines(docs_dir / "benchmark_vs_baselines.png")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
