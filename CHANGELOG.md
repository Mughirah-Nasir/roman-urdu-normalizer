# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Per-category resolution stats in the API response (which POS each unknown word likely was)
- Optional fuzzy fallback layer with confidence score for partial matches
- Multi-script output (Roman ↔ Nastaliq Urdu conversion)
