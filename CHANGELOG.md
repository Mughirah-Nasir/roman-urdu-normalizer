# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] — 2026-06-04

Architectural upgrade in response to a second external technical review.
Focus: phrase-aware rewrites, confidence scoring, ML baseline, hosted-demo
parity.

### Added
- **Multi-token phrase rewrite layer** (`app/multitoken.py`) — new Layer 0.5 of the pipeline. Scans input left-to-right for known compound forms with longest-match semantics. 125+ curated phrases covering compound verbs (`kr de`, `kr lo`, `kha lo`, `pi lo`), progressive aspect (`ja rha`, `ho rha`, `kar rha`), past tense compounds (`ho gya`, `a gya`), negation pairs (`kuch nai`, `nai aya`), time compounds (`abhi tk`, `ab tak`), intensifiers (`bht zyada`, `thora sa`), and common idioms (`kese ho`, `scene off`).
- **Per-token confidence scores** (0.0–1.0) on every resolution record. Scale: 1.0 for explicit map matches (variant, phrase, unchanged), 0.85 for phonetic single match, 0.65 for phonetic non-homograph collision, 0.40 for known homograph (ambiguous), 0.00 for unknown.
- **`avg_confidence` and `min_confidence`** in the response `stats` block — aggregates across all word tokens. Callers can threshold either at the per-token level or at the response level.
- **TF-IDF char n-gram ML baseline** in `benchmark/comparison.py` — a real trained model using `sklearn`'s TfidfVectorizer with char-wb 2-4-grams, cosine similarity against the canonical lexicon, threshold 0.45. Result: F1 61.0% — substantially better than the trivial baselines but still 30 F1 points below the four-layer pipeline.
- **One-click deploy spec** (`render.yaml`) — Render.com Blueprint config. A reviewer can fork, click Deploy, and have a live URL in ~2 minutes with sane production defaults (CORS open, rate limit 60/min, body cap 1 MB).
- **Search recall integration demo** (`examples/search_recall_demo.py`) — a self-contained script that builds a 25-review Pakistani e-commerce corpus, runs 8 queries against both raw and normalized versions, and prints a measurable recall lift table. Concrete proof of the downstream value claim.
- **27 new tests** in `tests/test_multitoken.py`:
  - phrase map integrity (size, casing, token-count bounds)
  - phrase scanning (empty input, no match, longest match wins, non-overlapping)
  - multi-token end-to-end (kr rhe → kar rahe, ja rha → ja raha, ho gya → ho gaya)
  - confidence scoring (variant map 1.0, phonetic 0.85, unknown 0.0, ordering invariants)

### Changed
- **Pipeline diagram** in README and DESIGN.md updated to reflect 4 layers (phrase_map prepended).
- **API response schema**: `TokenRecord` now includes `confidence: float` (required) and `span_tokens: int` (default 1, >1 for phrase matches). `Stats` gains `phrase_map: int`, `avg_confidence: float?`, `min_confidence: float?`. Existing callers won't break — new fields have defaults — but they're worth using.
- **Source enum** extended from `{variant_map, phonetic, unchanged, unknown}` to include `phrase_map`.
- **Benchmark numbers improved** on combined dataset: F1 88.8% → **90.1%**, sentence accuracy 58.9% → **63.2%** — the phrase layer is the cause.
- **Latency increased** due to the phrase scan: p50 7.83 µs → 29.93 µs, p99 36 µs → 99 µs, throughput 105K → 29K calls/sec. Still well under 100 µs at p99; documented honestly in `docs/limitations.md`.

### Notes
- 162 tests passing (was 135). 4-layer pipeline. Total commits 38.
- Pipeline architectural shape: explicit n-gram pre-pass + per-token resolver + confidence-aware unknown fallback. Reachable from the original 3-layer design without breaking existing API consumers.

---

## [1.1.0] — 2026-06-03

Major upgrade in response to external technical review. Focus: empirical
measurement, production hardening, honest documentation.

### Added
- **Benchmark harness** (`benchmark/`) with 492-example dataset:
  - 250 hand-curated examples across 50+ categories of real Pakistani Roman Urdu
  - 242 programmatic adversarial perturbations (emoji, vowel repeats, hashtags, casing chaos, whitespace stress, punctuation excess) via `benchmark/generate_adversarial.py`
  - `run_benchmark.py` scoring P/R/F1, sentence accuracy, per-category breakdown
  - `latency.py` measuring p50/p95/p99 + throughput (in-process, no HTTP)
  - `comparison.py` against `naive_replace` and `levenshtein_nearest` baselines
  - `render_charts.py` producing two dark-editorial PNG charts
  - `results.md` documenting headline numbers and error analysis
- **Headline numbers**: F1 **88.8%** on combined dataset, sentence accuracy 58.9%, p50 latency 7.83 µs, throughput 105,061 calls/sec. Pipeline beats naive_replace by 55 F1 points and Levenshtein by 42 F1 points.
- **`/metrics` endpoint** exposing tokens processed, request counts, top 20 unknown tokens, top 10 ambiguous tokens, lexicon sizes, runtime config — the feedback loop for lexicon growth.
- **Production hardening** in `app/main.py`:
  - `ALLOWED_ORIGINS` env var — CORS closed by default (localhost only)
  - `MAX_REQUEST_BYTES` env var — 1 MB default, returns 413 on overrun
  - `RATE_LIMIT_PER_MIN` env var — optional per-IP sliding-window limiter, returns 429 + Retry-After
- **Python client SDK** (`client/`) — zero third-party deps, uses only stdlib `urllib.request`. Retries with exponential backoff, 4xx fail-fast, custom exception hierarchy, `normalize_chunks()` auto-batches over the 100-item API limit.
- **Examples** (`examples/`):
  - `minimal_example.py` — smallest program calling the API
  - `normalize_csv.py` — normalize a CSV column with auto-batching
  - `normalize_whatsapp.py` — parse WhatsApp chat exports into structured JSONL
- **35 adversarial tests** (`tests/test_adversarial.py`) — emoji preservation (incl. ZWJ), repeated letters, hashtags, mentions, numbers, Arabic-script, code-switching, URLs, punctuation extremes, whitespace stress, and the exact examples called out in the external review.
- **13 client SDK tests** (`tests/test_client.py`) covering happy paths, batch chunking, 4xx non-retry, version exposure.
- **Four new docs**:
  - `docs/limitations.md` — 10-section honest map of where the system breaks (context-free resolution, multi-token rewrites, vowel-stretch collapse, lexicon size, frequency-based homograph errors, Roman→Nastaliq scope, performance characteristics, safety/PII, what's tested vs claimed, future work)
  - `docs/corpus.md` — provenance of language data (sources, what was excluded, gold-standard construction methodology, perturbation methodology, extension guidelines)
  - `docs/deployment.md` — Render / Fly.io / Docker Compose guides, env var reference, nginx reverse-proxy with X-Forwarded-For, production checklist, scaling notes
  - `docs/downstream.md` — five concrete before/after demos showing value (search recall 20%→100%, dedup, sentiment, LLM prompt cleaning, analytics)
- **`DESIGN.md`** — design-decisions essay (why three layers, why curated, why FastAPI, what changed mid-build, what's deliberately not built)
- **Restructured README** — leads with problem → demo → results → architecture → run; authenticity moved to bottom per review feedback.

### Changed
- **Variant map fixes** discovered via benchmark loop: `tk` is now `tak` (not `theek`); added `bs → bas`, `krdo → kar do`, `krde → kar de`, `krlo → kar lo`, `mt → mat`, `b → bhi`, `mjhe → mujhe`, `subh → subah`, `bnai → banai`, `pta → pata`, `chla → chala`, `lge → lage`, `wese → waise`, `bat → baat`, plus pronoun/temporal/verb-progressive expansions. Total variant entries now ~430.
- **Digit-to-Urdu-word mappings removed** — `5` no longer becomes `panch`. Digits pass through unchanged (which is what Pakistani users actually want).
- `kha` now maps to `kaha` (he said) instead of `keh` — more contextually correct in 99% of cases.
- Single-letter regression test (`test_short_b`) tightened to specifically guard against phonetic-layer over-resolution while allowing intentional variant-map entries for short tokens like `h → hai` and `b → bhi`.

### Fixed
- **Digit normalization bug** — Found by `tests/test_adversarial.py::TestNumbers::test_time_format`. Digits `1`–`9` were being silently rewritten to Urdu number words via variant map entries. Removed; digits now pass through.
- `bs` (the SMS shorthand for `bas`) was being marked `unknown` instead of resolving via variant map. Added explicit entry.

### Security
- CORS is now restrictive by default. Existing deployments that relied on permissive CORS must set `ALLOWED_ORIGINS='*'` explicitly.
- Request bodies capped at 1 MB by default; configurable via `MAX_REQUEST_BYTES`.

### Notes
- 87 + 35 + 13 = **135 tests** passing.
- Total commits: 33, all authored by Mughirah Nasir.

---

## [1.0.0] — 2026-05-27

First stable release. The core three-layer normalizer has been live-demoed
against real Pakistani Roman Urdu and two regression-test bugs have been
caught and fixed.

### Added
- Three-layer resolution pipeline: exact variant map → phonetic key → unknown
- Phonetic key algorithm with digraph folding (kh, gh, sh, ch, th, ph, dh, bh, jh, rh) and vowel class collapse
- Curated lexicon: 655 canonical Roman Urdu words across 13 part-of-speech categories
- Curated variant map: 344 SMS-shorthand entries (bht, nhi, kch, yr, ...)
- 6 registered homograph groups (kaha/kahan, jana/janna, sona/sonna, mara/maara, baal/bal, sher/sheer)
- FastAPI HTTP surface: `/normalize`, `/normalize/batch`, `/health`, `/stats`, auto OpenAPI docs at `/docs`
- Batch endpoint accepting up to 100 strings per request
- Stats endpoint exposing per-category lexicon counts
- Custom exception hierarchy (`NormalizerError`, `InvalidInputError`, `DictionaryIntegrityError`, `BatchSizeError`)
- HTTP exception handlers mapping internal errors to proper status codes (400, 413, 500)
- Request logging middleware (one structured line per request)
- CLI tool (`python -m app.cli`) with stdin / JSON / `--stats` modes
- Dark editorial demo frontend with in-browser fallback (works offline)
- 87 tests across five files (phonetic algorithm, normalizer, regressions, API, data integrity)
- Dockerfile (multi-stage, non-root user, healthcheck)
- GitHub Actions CI workflow with Python 3.10 / 3.11 / 3.12 matrix
- MIT License, CONTRIBUTING guide, full README with architecture rationale
- Cryptographic originality artifacts: `AUTHENTICITY.md`, `PROVENANCE.md`, `CERTIFICATE.html`

### Fixed (regression-tested permanently)
- **Short-key collision** — single-letter tokens were resolving to "kyun" because length-1 phonetic keys leaked into the index. The index now excludes any key shorter than 2 characters. `tests/test_regressions.py::TestShortKeyCollisionBug`
- **kaha / kahan silent rewrite** — "kaha" (he/she said) was being silently rewritten to "kahan" (where) because of a bad variant map entry. The entry is gone; the words are now registered as a homograph group and the normalizer returns `ambiguous: true` on the collision. `tests/test_regressions.py::TestKahaKahanHomographBug`

### Security
- CORS is intentionally permissive for the demo. Production deployments should tighten `allow_origins`.

---

## [Unreleased]

### Planned
- **Multi-token n-gram rewrites** for compound forms (`pi lo`, `kha lo`, `kr de`) via longest-match
- **Context-aware homograph resolution** using a small n-gram model or LLM scoring pass for `kal`, `main`, `nai`, `or` ambiguities
- **Per-token confidence scores** (currently boolean source flag)
- **WebSocket streaming endpoint** for inputs above the batch limit
- **Regional dialect packs** — Karachi vs Lahore vs Punjabi-flavored variant maps
- **Roman → Nastaliq script conversion** as a sister endpoint

---
