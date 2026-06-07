# Benchmark results

All numbers in this document are reproducible from the current repository. Each table is followed by the exact command that produced it. The system under test is the **four-layer pipeline** (phrase map → variant map → phonetic → unknown) at version **v1.2.1**.

## Headline numbers

| Dataset | Examples | Token F1 | Sentence accuracy |
| --- | ---: | ---: | ---: |
| `combined` (hand-curated + adversarial perturbations) | 492 | 90.1% | 63.2% |
| `gold_standard.jsonl` (hand-curated only) | 250 | 90.6% | 66.0% |
| `gold_standard_adversarial.jsonl` (adversarial only) | 242 | 89.5% | 60.3% |
| `heldout.jsonl` (blind held-out, never used to inform the lexicon) | 100 | 89.3% | 44.0% |

Reproduce:

```bash
python -m benchmark.run_benchmark --dataset combined
python -m benchmark.run_benchmark --dataset gold_standard.jsonl
python -m benchmark.run_benchmark --dataset gold_standard_adversarial.jsonl
python -m benchmark.run_benchmark --dataset heldout.jsonl
```

The blind held-out set is the most important number for honesty. It was written specifically for evaluation and never used to inform the variant map or canonical lexicon. F1 holding within one point of the in-sample combined number (89.3 vs 90.1) is the generalization signal.

## Comparison study

Four strategies scored on the combined 492-example dataset. Reproduce with `python -m benchmark.comparison`.

| Strategy | Sentence accuracy | Token precision | Token recall | Token F1 |
| --- | ---: | ---: | ---: | ---: |
| Baseline A: `naive_replace` | 3.7% | 39.3% | 39.4% | 39.4% |
| Baseline B: `levenshtein_nearest` | 10.8% | 52.1% | 51.7% | 51.9% |
| Baseline C: `tfidf_char_ngram` (sklearn) | 16.1% | 60.7% | 60.4% | 60.5% |
| **Ours: four-layer pipeline** | **63.2%** | **90.0%** | **90.1%** | **90.1%** |

**Reading the table.**

`naive_replace` iterates the variant map and does dumb `str.replace` for each entry. It over-substitutes because earlier replacements interact with later ones. This is what someone might write in twenty minutes.

`levenshtein_nearest` resolves each unknown token to the canonical lexicon word with smallest edit distance, bounded at distance 2. Recall-happy but precision-poor. It silently rewrites correct words to lexicon neighbors. This is the failure mode the "never silently guess" rule was designed against.

`tfidf_char_ngram` is a real machine-learning baseline using scikit-learn. Vectorizes tokens as character bigrams through 4-grams (TF-IDF) and finds the canonical word with highest cosine similarity, with a 0.45 threshold. This is the kind of thing a senior engineer would actually try before writing custom rules. It scores 60.5% F1, substantially better than the rule-based baselines but still 29 F1 points below the four-layer pipeline.

The **four-layer pipeline** beats the ML baseline by 29 F1 points and the trivial baselines by 38 to 51 F1 points. More importantly, it preserves the "never silently guess" contract that none of the baselines can offer.

## Latency

| Percentile | Latency |
| ---: | ---: |
| p50 | ~30 μs per call (in-process) |
| p99 | ~99 μs per call |
| Throughput | ~29,000 calls per second per thread |

Reproduce with `python -m benchmark.latency`. Hardware affects absolute numbers, but the relative shape is stable.

The phrase layer added in v1.2 increased p50 latency from roughly 7.8 μs to roughly 30 μs because of the multi-token scan. For any realistic preprocessing workload this is still fast enough that the normalizer is never the bottleneck. The trade was a measurable F1 gain (+1.3 points) for a latency cost the system has to spare.

## Per-category breakdown

The combined benchmark covers categories including: simple variants, SMS shorthand, emoji-mixed, repeated characters, code-switching with English, multi-token compound verbs, religious phrases, named entities, hashtags, Arabic-script mixing, punctuation, numbers, and long sentences.

Run `python -m benchmark.run_benchmark --dataset combined --verbose` to see the per-category F1.

Roughly:

- 100% F1 on greetings, religious phrases, basic SMS shorthand, simple variants, emoji-mixed text.
- 80 to 95% F1 on code-switching, named entities, hashtags, Arabic-script mixing, compound verbs.
- 60 to 80% F1 on the hardest categories: long sentences with multiple ambiguous tokens, regional dialect, slang the lexicon has not yet absorbed.

The honest failure cases for the 60 to 80% bracket are in `docs/limitations.md`.

## How to extend the benchmark

The benchmark is hand-curated, not generated. Each example in `gold_standard.jsonl` was written or vetted by a native Pakistani Urdu speaker. To add new examples, append JSON lines of the form:

```jsonl
{"id": "g300", "category": "new_category", "input": "your roman urdu text", "expected": "canonical form", "notes": "what this tests"}
```

Then rerun `python -m benchmark.run_benchmark --dataset combined` to see the impact on overall accuracy. If accuracy drops, either fix the variant map or document the case as a known limitation.

## Charts

The bar chart `docs/benchmark_vs_baselines.png` and the per-category chart `docs/benchmark_by_category.png` are regenerated by `python -m benchmark.render_charts`. That script needs `matplotlib`, which is in `requirements-dev.txt`.

---

**Author:** Mughirah Nasir · NUST SEECS, Pakistan
