# Design

This document explains *why* the Roman Urdu Normalizer is built the way it is. Each decision below was a real fork in the road during the build.

It's also the document I'd hand a senior engineer in an interview if they asked "walk me through your design choices."

---

## The central design constraint

> **Never silently guess.**

Every other decision flows from this. A normalizer that's right 80% of the time and silently wrong 20% is *worse* than no normalizer — downstream systems trust its output and propagate the errors invisibly. A normalizer that's right 80% of the time and *flags* the 20% it isn't sure about is something I can build on top of.

Concretely: any input token the system can't resolve with high confidence passes through unchanged with `source: "unknown"`. The output schema makes this distinction explicit, every test enforces it, and `tests/test_regressions.py::TestKahaKahanHomographBug` exists precisely because an early version violated this rule.

This is the rule the architecture is organized around. If you're tempted to add a "fuzzy fallback" layer that silently rewrites uncertain tokens, you've defeated the whole point — open an issue first, don't open a PR.

---

## Why three layers instead of one

The first version I built had one layer: a flat dictionary `{wrong_spelling: right_spelling}`. It failed within an hour of real-world testing.

The problem: there are two completely different *kinds* of misspelling, and a single map can't handle both well.

**Kind 1 — SMS vowel-dropping.** `bht`, `nhi`, `kch`, `yr`. Native Urdu speakers drop vowels aggressively in informal writing. These have no phonetic relationship to their canonical forms — you cannot recover `bahut` from `bht` with any phonetic algorithm because the algorithm has no vowels to work with. These need an **explicit dictionary**.

**Kind 2 — Spelling variation on the same sound.** `kya`/`kia`/`kyaa`/`kayya`. These all encode the same Urdu phoneme; the spellings differ only in vowel choice (the same `kaaf-yaa-alif` letter sequence). A flat dictionary scales O(n²) here — every new canonical word adds dozens of plausible misspellings. These need a **phonetic algorithm** that collapses the variation automatically.

The three-layer pipeline maps these onto the right tool:

1. **`VARIANT_MAP` (exact lookup)** — the dictionary, for Kind 1
2. **Phonetic key** — the algorithm, for Kind 2
3. **Unknown** — the honest fallback when nothing matched

Layers run in order, first match wins, no looking back. Each layer is debuggable on its own — when something goes wrong, the `source` field on the output tells you which layer rewrote it (or didn't).

---

## Why a curated lexicon and not machine learning

I considered fine-tuning a small transformer (BERT-style) to learn Roman Urdu spelling normalization end-to-end. It would have been the impressive-looking choice. I rejected it because:

1. **Auditability.** When a curated lexicon mis-resolves a word, I can point at the exact dictionary entry that did it and either fix it or document it as ambiguous. When an ML model mis-resolves a word, you cannot tell why and you cannot fix it without retraining.

2. **Native-speaker advantage.** I am a native Urdu speaker. I know that `bht` is overwhelmingly `bahut` and not `bahot` (a less-common variant), that `yr` is `yaar` and not `yar` (the latter being a different Hindi word). These intuitions are exactly what training data either doesn't capture or doesn't preserve consistently. The lexicon encodes them deterministically.

3. **Resource cost.** A 7B-parameter LLM call per token at scale would cost hundreds of dollars in API fees per day for any non-trivial input volume. The rule-based pipeline runs at 105,000+ calls/sec on a single thread.

4. **Composition.** This normalizer is meant to sit *under* an LLM-based system as a fast, deterministic preprocessing step. If the preprocessing layer is itself non-deterministic and slow, the architecture loses its main benefit.

**When ML would be the right call:** if you needed to normalize a *new* language (say Roman Punjabi or Roman Sindhi) where you don't have curation time. The architectural choice would change. For Roman Urdu specifically, curation wins.

---

## Why FastAPI and not Django

This is a stateless, single-purpose, high-throughput API. Django's strengths — ORM, admin, multi-app sessions — would be unused overhead. FastAPI gives me:

- Auto-generated OpenAPI docs (`/docs`) and ReDoc (`/redoc`) from the Pydantic models
- Async support if I ever want to add fan-out to an external service
- Pydantic validation that catches bad input before it touches the resolver
- About 2-3x the request throughput of Django on the same hardware

The trade-off: less batteries-included. If I wanted user accounts and a billing flow, I'd reach for Django. For this, FastAPI is straightforwardly the right tool.

---

## Why batch endpoint with a hard limit of 100

Two reasons:

1. **Memory.** Each `normalize_text` call allocates per-token records. At 100 reasonable-length sentences, peak memory is bounded and predictable. At 10,000 unbounded inputs from an untrusted caller, the server is one curl command away from OOM.

2. **Pagination forces caller-side discipline.** If you want to process a million records, you should write a loop that batches them in chunks of 100. The client SDK (`client.normalize_chunks`) does this automatically, so the limit costs callers almost nothing.

The number 100 is a guess based on a back-of-envelope of typical Pakistani SMB application sizes. If real usage shows it's wrong, I'd bump it — but I'd want to add a streaming endpoint before bumping it past ~1000.

---

## Why the homograph guard returns `ambiguous: true` instead of guessing

Some Roman Urdu words sound identical but mean completely different things in context:

| pair | meanings |
| --- | --- |
| `kaha` vs `kahan` | "said" vs "where" |
| `jana` vs `janna` | "to go" vs "to know" |
| `sona` vs `sonna` | "to sleep" vs "gold" |
| `mara` vs `maara` | "died" vs "hit" |
| `baal` vs `bal` | "hair" vs "strength" |
| `sher` vs `sheer` | "lion" vs "poem/verse" |

The phonetic algorithm collapses these to the same key. The original instinct is to pick one by frequency (or alphabetical order). I rejected that:

- Picking `kahan` over `kaha` is silent guessing — see the central design constraint.
- Pakistani users in different regions weight the homographs differently; a frequency-based pick that works for Karachi might be wrong for Lahore.
- Downstream LLM-based systems can disambiguate from context far better than this normalizer can. Telling them "this token is ambiguous, here are the candidates" is more useful than guessing.

So when the phonetic key resolves to two canonical words that form a registered homograph group, the normalizer returns the token unchanged with `ambiguous: true` and the candidate list. Downstream takes it from there.

---

## What changed mid-build

Three things shifted between the first design and v1.0.

### 1. The phonetic index gained a minimum-key-length guard

The original phonetic index included entries for every canonical word, including single-letter ones. Result: any stray `k` in input would phonetic-match the alphabetically-first K-word (`kyun`) and rewrite to it. This was the bug behind `tests/test_regressions.py::TestShortKeyCollisionBug`.

The fix: skip canonical words whose phonetic key is shorter than 2 characters. Single-letter tokens can only be resolved via the explicit variant map now, never via phonetics. The constraint costs nothing — short phonetic keys are noise.

### 2. The homograph guard was added late

The first version didn't have it. The bug surfaced when I demoed the normalizer to a friend by feeding it WhatsApp messages from his actual chat history. He typed `wo kha gaya` ("he ate / he went") and the normalizer turned it into `wo kahan gaya` ("where did he go"). That meant the variant map had a bad entry mapping `kha → kahan` *and* the architecture had no way to detect the ambiguity.

Two changes followed. First, removed the bad entry. Second, added the `HOMOGRAPH_GROUPS` registry and the resolver logic that flags `ambiguous: true` when phonetic keys collide. The bug is now `tests/test_regressions.py::TestKahaKahanHomographBug`.

### 3. The variant map kept growing during benchmark testing

After the gold-standard dataset and benchmark harness were in place, every benchmark run surfaced one or two missing variant entries. F1 went from 81.6% to 87.8% over a few iterations of:

1. Run benchmark
2. Look at the misses
3. Add legitimate missing variants to the map (e.g. `subh → subah`, `lge → lage`, `bnai → banai`)
4. Re-run

This is exactly the loop a benchmark harness is *for*. The lesson: until you have measurement, you don't actually know what your system does. The benchmark wasn't a vanity exercise — it directly drove ~6 F1 points of improvement.

---

## What's deliberately not built

Things I considered and chose not to include in v1.0:

- **Multi-token n-gram resolution.** `pi lo`, `kha lo`, and other compound verb-particle patterns aren't handled because the resolver is strictly per-token. Adding n-grams would require a multi-token rewriting pass and a longest-match algorithm. Worth doing in v1.1.

- **Roman ↔ Nastaliq Urdu conversion.** Going from Roman Urdu to the Perso-Arabic script is a separate, harder problem — it's transliteration, not normalization. Different toolset.

- **Confidence scores.** Each token's resolution is currently boolean ("did this layer match"). A finer-grained 0.0–1.0 score per token would be useful for thresholding in downstream pipelines. Not hard to add but didn't make v1.0.

- **A streaming / chunked input mode.** The batch endpoint maxes at 100. If real users hit that limit, the right answer is probably WebSocket streaming, not a bigger batch size.

- **Direct LLM integration.** Tempting to wire a small LLM in as a "did you mean?" fallback. Rejected: it would violate the never-silently-guess rule unless the LLM's response was explicitly surfaced as `ambiguous: true` with a `candidates` list. Doable but adds infrastructure complexity for marginal gain.

---

**Author:** Mughirah Nasir, NUST SEECS, 2026.
