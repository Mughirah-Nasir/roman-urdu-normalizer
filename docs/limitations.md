# Known Limitations

This document is the honest answer to "where does it break?" Every project has limitations; pretending otherwise is the actual red flag. These are mine.

The list is ordered roughly by severity. Items at the top hurt actual users; items at the bottom are edge cases I've accepted.

---

## 1. The normalizer is context-free

The system resolves each token independently. It does not look at neighboring tokens, sentence structure, or document context. This means:

| Word | Possible meanings | What we do |
|------|-------------------|------------|
| `kal` | yesterday OR tomorrow | Preserve unchanged — the word itself is correct, just ambiguous |
| `main` | "I" (Urdu pronoun) OR English "main" (adjective) | Preserve unchanged |
| `nai` | "no" (negation) OR "nayi" (new, feminine) | Variant map resolves to `nahi` by frequency — this is sometimes wrong |
| `ye` | demonstrative "this" OR English "ye" (archaic plural "you") | Preserve unchanged |
| `bhi` | "also" OR a name | Variant map resolves to `bhi` — fine in 99% of cases |
| `or` | "and" (Urdu `aur`) OR English "or" | Variant map resolves to `aur` — wrong when input is English |

**Why we don't fix this in v1:** the right fix is a context-aware n-gram model or an LLM scoring pass. Both add infrastructure complexity (>1 ms latency, external model dependency) for a marginal gain. The architectural slot is reserved — see `DESIGN.md` § "What's deliberately not built" — but it's deferred to v1.1.

**Workaround for callers:** the API returns `ambiguous: true` with `candidates` for known homograph pairs (currently 6 groups). For other ambiguities, look at `source: "variant_map"` vs `source: "unchanged"` — variant-map resolutions on commonly-ambiguous words like `or`, `bhi`, `nai` are the suspect ones.

---

## 2. Multi-token rewrites are not supported

The resolver is strictly per-token. Pakistani Roman Urdu has compound forms that span multiple tokens:

| Input | What we'd ideally produce | What we actually produce |
|---|---|---|
| `pi lo` | `pee lo` (drink) | `pi lo` — first token mis-normalized, particle untouched |
| `kha lo` | `kha lo` (eat) | `kha lo` — accidentally correct, but `kha → kaha` mapping makes this brittle |
| `kr de` | `kar de` (do it) | `kar de` — works because variant map has `kr → kar` and `krde → kar de` |
| `ho ja` | `ho ja` (be it) | `ho ja` — works by accident |

**Why:** an n-gram pass with longest-match would solve this. Architecturally easy. Hasn't shipped because per-token resolution covers the 80% case and gold-standard data on multi-token forms is thin.

---

## 3. Vowel-stretch SMS (`kyaaaa`, `bhttttt`) collapses to canonical form

When a Pakistani user types `kyaaaa`, they usually mean emphatic "kya" — the stretch carries emotional content (frustration, surprise). Our phonetic layer collapses it to `kiya` (canonical), losing the emphasis.

**Trade-off:** collapsing is *correct* for downstream search/classification/aggregation use cases — `kyaaaa` and `kya` should count as the same word for a sentiment dashboard. It's *wrong* for downstream stylometric analysis where the stretch itself is signal.

**Workaround for callers:** if you need to preserve stretches, run normalization on the canonical form *and* keep the original separately. The output includes `tokens[i].original`, so this is one field access away.

---

## 4. The lexicon is small relative to the language

655 canonical words and ~430 variant entries are enough for a portfolio piece. They are **not** enough to cover the full surface of daily Pakistani Roman Urdu, which has:

- Regional dialects (Karachi Urdu vs Lahore Urdu vs Punjabi-flavored Urdu)
- Newer slang ("scene off", "set hai", "tota off", "bhai chill")
- Emerging code-switching patterns (e.g. tech vocabulary used in Urdu syntax)
- Names of people, cities, places, brands (no lexicon will ever cover all of these)
- Profanity and informal register

**Coverage:** the `/metrics` endpoint exposes the top unresolved tokens from live traffic. The intended growth loop is: deploy → watch `/metrics` → batch-add the top 50 unresolved tokens to the variant map → ship. See `docs/corpus.md` for the curation methodology.

---

## 5. Frequency-based homograph resolution is sometimes wrong

For words *not* in our 6 registered homograph groups, the variant map picks the most common Roman Urdu meaning. This is:

- **Right ~99% of the time** for common SMS shorthand
- **Wrong ~1% of the time** when the input was actually English or a less-common Urdu sense

Example: someone writing `or` in English ("would you like X *or* Y?") gets it silently changed to `aur`. The fix is to expand the homograph group registry to cover more cases — but every addition shifts behavior in subtle ways, so it requires testing.

---

## 6. Roman → Nastaliq (Urdu script) conversion is not supported

This service normalizes Roman Urdu (Latin script with Urdu phonology). Converting to Nastaliq (the proper Urdu script) is a separate, harder problem and out of scope for v1. Mixed-script input (Roman + Nastaliq in the same sentence) **is** supported — Nastaliq tokens pass through unchanged.

---

## 7. Performance characteristics

- **Single-thread throughput:** ~105,000 calls/sec in-process. Excellent.
- **Memory footprint:** ~2 MB for the loaded lexicon and phonetic indices. Fine.
- **Cold-start latency:** first call after process start takes 50-100 ms due to lazy index construction. Subsequent calls are 1–10 µs.
- **Concurrency:** the resolver is stateless and thread-safe; FastAPI's worker model handles concurrency. No internal locks.

**What we don't have:**
- Distributed deployment / horizontal scaling beyond uvicorn workers
- A streaming endpoint for inputs over the batch limit
- GPU acceleration (and we wouldn't benefit from it — this is CPU-bound regex/dict lookups)

---

## 8. Adversarial / safety

The system has no content filtering. Profanity passes through normalized (e.g. `bht ghatiya` → `bahut ghatiya`). This is intentional — the normalizer's job is spelling normalization, not content moderation. If you need profanity filtering, layer it on top.

The `/metrics` endpoint exposes `top_unknown_tokens` from live traffic. If you process user-generated content, the raw text in this list **could include PII or sensitive content typed by users**. Treat the metrics output as sensitive. For production use, consider hashing or aggregating unknown-token counts rather than exposing raw strings.

---

## 9. What's tested vs what's claimed

- **Tested:** the 87 unit tests, 13 client SDK tests, 35 adversarial tests cover the resolver, phonetic algorithm, variant map integrity, batch handling, error responses, edge cases, and the explicit adversarial examples flagged by external review.
- **Benchmarked:** 492 examples (250 hand-curated + 242 adversarial perturbations) with token F1, sentence accuracy, latency, and baseline comparison.
- **Not tested at scale:** real production traffic. Numbers from a 492-example dataset are directional, not definitive — F1 on a million-message corpus would likely be 3-5 points lower.

---

## 10. Future work

In rough priority order:

1. **Multi-token rewrites** via n-gram longest-match (single-digit F1 improvement)
2. **Context-aware homograph resolution** via a small n-gram model or LLM scoring pass
3. **Lexicon growth** via the `/metrics` → curation → release loop
4. **Confidence scores** per token (currently boolean)
5. **WebSocket streaming endpoint** for inputs over the batch limit
6. **Per-region dialect packs** (Karachi vs Lahore vs Punjabi-flavored variant maps)

See `CHANGELOG.md` `[Unreleased]` for tracked items.

---

**Maintainer:** Mughirah Nasir · mnasir.bee25seecs@seecs.edu.pk · NUST SEECS, Pakistan
