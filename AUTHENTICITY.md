# AUTHENTICITY

## This project was originated, designed, and built by Mughirah Nasir.

---

## Originator

| Field        | Value                                            |
| ------------ | ------------------------------------------------ |
| Name         | **Mughirah Nasir**                               |
| Email        | mnasir.bee25seecs@seecs.edu.pk                   |
| Institution  | NUST SEECS, Rawalpindi, Pakistan                 |
| GitHub       | https://github.com/MughirahNasir                 |
| Project      | Roman Urdu Normalizer (portfolio piece B1 of 8)  |
| Built        | May 19 – June 5, 2026                            |
| Stable tag   | v1.2.1                                           |

---

## Formal statement

I, **Mughirah Nasir**, am the originator and sole author of this project. I conceived the problem framing, designed the architecture, curated all language data, wrote the algorithm, wrote the tests, debugged the live demo, designed the frontend, and produced every piece of documentation in this repository.

Specifically, the following are my work:

### Core system (v1.0 — historical baseline)
> The original architecture, preserved here for the historical record. v1.2 evolved this into a four-layer pipeline by adding the multi-token phrase rewrite layer; see the "Phrase-layer and confidence additions (v1.2)" section below for the current shape.

- The **problem framing** — that Pakistani Roman Urdu spelling chaos needs a *predictable, fast, refuses-to-silently-guess* preprocessing layer that sits under (not inside) LLM-based downstream systems.
- The **original three-layer resolution pipeline** (variant map → phonetic key → unknown), including the priority order and the rationale for each layer. (Now four layers after v1.2; see below.)
- The **phonetic key algorithm** in `app/phonetic.py`: every digraph rule (kh, gh, sh, ch, th, ph, dh, bh, jh, rh), every vowel class (a/aa; i/y/e/ee/ii; o/u/oo/uu), and the consonant-doubling collapse step. Each rule was chosen for **Pakistani Roman Urdu specifically** — not generic Urdu, not Hindi-Urdu generic Romanization.
- The **curated lexicon** — 655 canonical words across 13 part-of-speech categories. Native-speaker sourced.
- The **variant map** — ~430 SMS shorthand entries. Drawn from real Pakistani WhatsApp / Twitter usage I observed and recognize.
- The **homograph guard** — 6 registered groups and the policy decision that the normalizer flags `ambiguous: true` rather than silently picking one.
- The **"never silently guess" rule** — the explicit design choice that unknown tokens pass through unchanged.
- The **two regression-test bugs** in `tests/test_regressions.py` — found by me feeding the running demo realistic Pakistani Roman Urdu.
- All **87 v1.0 test cases** (later expanded to 162 by v1.2) across `tests/`.
- The **API contract** (endpoint shapes, error responses, batch semantics, the 100-item limit).
- The **dark editorial frontend** (typography: Fraunces, Hanken Grotesk, JetBrains Mono; saffron/jade/rust color tokens for resolution sources; offline-capable in-browser fallback).

### Evaluation and hardening additions (v1.1)
- The **250-example hand-curated benchmark dataset** in `benchmark/gold_standard.jsonl` — every example is real Pakistani Roman Urdu I wrote or recognized, with hand-curated expected outputs.
- The **adversarial perturbation generator** in `benchmark/generate_adversarial.py` — six transformations (emoji insert, vowel repeat, punct excess, hashtag suffix, casing chaos, whitespace stress) that produce 242 more examples with lockstep-perturbed expected outputs.
- The **benchmark scoring harness** (`run_benchmark.py`), **latency suite** (`latency.py`), and **baseline comparison study** (`comparison.py`).
- The **chart rendering** (`render_charts.py`) — both PNGs.
- The **Python client SDK** in `client/` — zero-dep, retries with exponential backoff, batch chunking, custom exception hierarchy.
- The **production hardening** in `app/main.py` — env-var-driven CORS allowlist, request-size limit, optional rate limiter, `/metrics` endpoint with top unresolved tokens.
- All four new docs: `docs/limitations.md`, `docs/corpus.md`, `docs/deployment.md`, `docs/downstream.md`.
- `DESIGN.md` — the design-decisions essay.
- The **restructured README** following the problem → demo → results → architecture → run order.
- The **example scripts** in `examples/` — CSV pipeline, WhatsApp export parser, minimal example.

### Documentation
- This file, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `PROVENANCE.md`, `CERTIFICATE.html`, `PUSH-NOW.md`, `DESIGN.md`, and the four `docs/` markdown files.

### Phrase-layer and confidence additions (v1.2)
- The **multi-token phrase rewrite layer** (`app/multitoken.py`) — 125+ hand-curated compound forms covering progressive aspect, past tense, verb+particle, negation pairs, and idioms. The longest-match scanning algorithm.
- **Per-token confidence scoring** — every resolution carries a 0.0–1.0 score plus `avg_confidence` and `min_confidence` in the response stats.
- The **TF-IDF char n-gram ML baseline** in `benchmark/comparison.py` — using `sklearn` TfidfVectorizer with char-wb 2-4-grams against the canonical lexicon, cosine-similarity nearest neighbor with a 0.45 threshold.
- 27 new tests in `tests/test_multitoken.py` covering phrase map integrity, scanning behavior, end-to-end multi-token resolution, and confidence-scoring invariants.
- The **`render.yaml`** Render.com Blueprint for one-click deployment.
- The **`examples/search_recall_demo.py`** integration showcase — a 25-review corpus with 8 queries demonstrating measurable recall lift on Pakistani Roman Urdu search.

---

## On AI assistance

I used Claude (Anthropic) as a coding partner during the build. To be precise about what that means here:

**AI assisted with:**
- Scaffolding boilerplate (Pydantic model field definitions, FastAPI route signatures, standard pytest setup, CSS spacing tweaks).
- Reviewing my code for obvious errors and suggesting alternatives where I asked for them.
- Drafting prose for documentation that I then edited.
- Generating the SHA-256 manifest and the visual certificate file (these are mechanical to produce given the file list I had assembled).

**AI did NOT:**
- Originate the problem framing, the design, or the architecture.
- Curate any language data. All variant-map entries and lexicon words were chosen by me as a native Urdu speaker.
- Find either of the two regression-test bugs. Both were discovered by me feeding the running demo realistic text.
- Decide the "never silently guess" rule or the homograph-guard policy.

This is the same standard I apply to the rest of my 8-piece portfolio: AI is a velocity multiplier, never a substitute for understanding what's in the repo. If you ask me about any line in this codebase I can explain why it's there and what would break if it weren't.

---

## Cryptographic evidence of authorship

This authorship claim is backed by four independent pieces of evidence:

1. **Git commit history.** Every commit in `.git/` is authored as `Mughirah Nasir <mnasir.bee25seecs@seecs.edu.pk>`. Run `git log --format="%h %an <%ae> %ad %s" --date=iso` in this repo to verify. Commit timestamps span May 19 – May 27, 2026, telling a real story (feat → test → bug discovery → fix), not one dump.

2. **Per-file SHA-256 manifest.** See `PROVENANCE.md`. Every file in this repo has its content hash recorded. If a single byte of any file changes, the corresponding hash changes and the top-level project fingerprint changes.

3. **Project fingerprint.** A single SHA-256 over the manifest. Recording this fingerprint elsewhere (a tweet, a blog post, a commit message on another repo) timestamps the existence of this exact project state on that date.

4. **Optional Bitcoin blockchain anchor.** The fingerprint can be stamped via OpenTimestamps (`ots stamp PROVENANCE.md`) which proves "this exact content existed by date X" without requiring trust in any single party. Instructions are in `PROVENANCE.md`.

5. **Visual certificate.** `CERTIFICATE.html` is a human-readable, browser-renderable summary of all of the above.

---

## How to verify any specific claim

| Claim                                                 | How to verify                                                  |
| ----------------------------------------------------- | -------------------------------------------------------------- |
| "This file is exactly the one Mughirah committed."    | `sha256sum path/to/file` and match against `PROVENANCE.md`     |
| "Mughirah authored this commit."                      | `git log --format="%H %an <%ae>" path/to/file`                 |
| "This project state existed by date X."               | Check the OpenTimestamps `.ots` proof for `PROVENANCE.md`      |
| "The tests pass."                                     | `pip install -r requirements.txt -r requirements-dev.txt && python -m pytest tests/ -v` (expect 87 passing) |
| "The lexicon is what the docs say it is."             | `python -m app.cli --stats`                                    |

---

## Signed

> **Mughirah Nasir**
> mnasir.bee25seecs@seecs.edu.pk
> NUST SEECS, Rawalpindi, Pakistan
> 2026-05-27 (build complete) · 2026-06-03 (rebuilt from clean source)

*This statement is also published in plain text as part of every commit's history in this repository. It cannot be removed retroactively without breaking the project fingerprint, which is itself recorded outside this repo.*
