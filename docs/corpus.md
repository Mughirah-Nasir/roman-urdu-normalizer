# Corpus Provenance

How the language data in this repository was sourced, curated, and reviewed.

This document exists for two reasons. First, technical evaluators want to know whether the data is real or invented. Second, anyone who wants to extend the lexicon or build on the benchmark dataset needs to understand the curation methodology so their additions are consistent.

---

## What we curated

This repository contains three pieces of language data:

| Artifact | Size (v1.0) | What it is |
|---|---|---|
| `app/data.py` :: `CANONICAL_LEXICON` | 655 words | Canonical Roman Urdu spellings, the target of normalization |
| `app/data.py` :: `VARIANT_MAP` | ~430 entries | Misspellings, SMS shorthand, and abbreviations → canonical |
| `app/data.py` :: `HOMOGRAPH_GROUPS` | 6 groups, 12 words | Pairs that sound alike but mean different things |
| `benchmark/gold_standard.jsonl` | 250 examples | Hand-curated (input, expected output) pairs |
| `benchmark/gold_standard_adversarial.jsonl` | 242 examples | Programmatic perturbations of the above |

Total: **655 + 430 + 250 + 242 ≈ 1,577 hand-curated/derived data points**, all authored by Mughirah Nasir (NUST SEECS).

---

## Where the data came from

The vocabulary and the gold-standard sentences are drawn from three sources, in roughly this proportion:

1. **My own Pakistani Roman Urdu usage (≈60%).** I am a native Urdu speaker, born and educated in Pakistan, an active user of WhatsApp, Twitter/X, and Instagram in Roman Urdu since age 12. The bulk of the lexicon and the gold-standard sentences reflect the spelling and shorthand patterns I and my peers use daily.

2. **Observed patterns from public Pakistani online conversation (≈30%).** Public posts on Pakistani Twitter/X, public Pakistani Reddit threads (r/pakistan, r/karachi), and public YouTube comment sections on Pakistani channels. No screenshots, no usernames, no private messages, and no scraped corpora are included in this repository.

3. **Curated reference works (≈10%).** Standard Urdu spelling references and academic transliteration guides used to confirm the canonical form for borderline cases (e.g. *bahut* vs *bohat* vs *bhut* — three real spellings, one canonical choice). For these, see the section "References" below.

---

## What we deliberately excluded

- **No private messages.** No WhatsApp chats from my own conversations, no DMs, no screenshots from friends or family. Anything that originated from a 1:1 private exchange was excluded by hard rule.
- **No identifying information.** No usernames, no real names from observed posts (except generic ones used as examples: "Ali", "Sara", "Imran", which are extremely common Pakistani first names). The gold-standard examples use **fictional or generic** people, places, and events.
- **No commercial proprietary data.** No content from Pakistani SaaS dashboards, customer service logs, e-commerce platforms, or any other source that wasn't already public.
- **No scraping.** No crawler, no API harvester, no automated bulk collection. Patterns were observed, internalized, and rewritten — not copied.

---

## How the gold-standard dataset was constructed

The 250 hand-curated benchmark examples in `benchmark/gold_standard.jsonl` were built bottom-up by category:

1. **Categories first.** I picked 30+ categories I wanted to cover (greetings, family, food, school, time, emotion, polite, code-switching, named entities, emoji, hashtags, repeated letters, Arabic-script mix, marketplace haggling, etc.). The category list was the *plan*, not a post-hoc bucketing.

2. **Examples filled into each category.** For each category, I wrote 2–10 (input, expected output) pairs in the format an actual Pakistani user would type and the canonical form the normalizer should produce. The input was written first; only then did I write the expected output. This prevents accidentally cherry-picking inputs the normalizer already handled.

3. **Adversarial cases were intentional.** Categories like `edge_unknown` (gibberish that must pass through), `edge_short` (single letters), `homograph`, and `code_switch` deliberately contain inputs the normalizer should *not* aggressively transform. These guard against silent over-resolution.

4. **No example was added or modified to make the benchmark numbers look better.** Several rounds of running the benchmark surfaced misses that led to *legitimate* variant-map additions (e.g. `bs → bas`, `subh → subah`, `bnai → banai` — all real Roman Urdu patterns I'd missed). The dataset itself was untouched between runs.

---

## How the adversarial perturbations were generated

The 242 adversarial examples in `benchmark/gold_standard_adversarial.jsonl` are produced by `benchmark/generate_adversarial.py`, which applies one of six transformations to each base example:

| Perturbation | What it does |
|---|---|
| `emoji_insert` | Inserts 1–2 emojis at start/middle/end |
| `vowel_repeat` | Repeats a random vowel 2–4 times (`yaar` → `yaaaaar`) |
| `punct_excess` | Appends 2–5 punctuation marks (`hai` → `hai????`) |
| `hashtag_suffix` | Appends 1–2 hashtags |
| `casing_chaos` | Random per-character casing (`yaar` → `yAaR`) |
| `whitespace_stress` | Doubled spaces, leading/trailing whitespace |

Critically, the **expected output is perturbed in lockstep**. The score isn't "did you remove the emoji?" — emojis should be preserved. The score is whether the normalizer's actual rewriting work survives the noise.

The perturbation script is deterministic (seeded random), so the same input dataset always produces the same adversarial set. Re-running with `python -m benchmark.generate_adversarial --seed N` produces a different set.

---

## How to extend the dataset

If you want to add more examples (this is the long-term growth path for the lexicon):

1. Pick a **category** — either an existing one or a new descriptive name (e.g. `sports_chant`, `recipe_instruction`, `tech_jargon`).
2. Write **5–10 input lines** in the way a Pakistani user would actually type them. Don't sanitize.
3. Write the **expected canonical output** for each. When in doubt about the canonical form, document the choice in the `notes` field.
4. Add the lines to `benchmark/gold_standard.jsonl` with monotonically increasing `id`s.
5. Run `python -m benchmark.run_benchmark` and `python -m benchmark.generate_adversarial`.
6. If any new misses are *legitimate* (a word that should be in the variant map but isn't), add it to `app/data.py`. If any new misses are *legitimate ambiguities*, document them in `docs/limitations.md`. **Don't tweak the gold-standard expected outputs to match what the normalizer happens to produce.**

---

## References for canonical-spelling choices

For borderline cases — e.g. is the canonical form *bahut* or *bohat*? *kya* or *kia*? — I followed these references:

- *Urdu transliteration standards* as documented in academic NLP literature on South Asian languages.
- Common usage on Pakistani news media (Geo, Dawn, ARY) where Roman Urdu is occasionally used in social posts.
- **The "majority spelling on Pakistani Twitter" heuristic.** When two canonical forms compete, the one used by more Pakistani users on public Twitter/X wins. This is documented per-decision in code comments where it matters.

For words specific to Pakistani Urdu (vs. Indian Hindustani), I went with the Pakistani form: *behan* not *behen*, *abu* not *papa*, *ammi* not *mummy*.

---

## What the data is NOT

Just to be explicit:

- **It is not a balanced corpus**, statistical or otherwise. There's no claim that the frequencies in the variant map reflect actual Roman Urdu usage frequencies. The map covers what I observed and recalled, not what an n-gram model over 100M tokens would produce.
- **It is not anonymized scraped data.** Every entry was written by hand or reformulated from a remembered pattern. There's no risk of recovering a specific tweet, message, or post from this dataset.
- **It is not exhaustive.** See `docs/limitations.md` § "The lexicon is small relative to the language."

---

**Curator:** Mughirah Nasir · mnasir.bee25seecs@seecs.edu.pk · NUST SEECS, Pakistan · 2026.
