# Roman Urdu Normalizer

**A three-layer phonetic normalizer that turns Pakistani Roman Urdu spelling chaos — "kya / kia / kyaa", "bht / bohat / bahut", "nhi / nahin / nai" — into one canonical form, with a strict "never silently guess" rule.**

[![tests](https://img.shields.io/badge/tests-87%2F87%20passing-5fb39a)]() [![python](https://img.shields.io/badge/python-3.10%2B-e8a33d)]() [![framework](https://img.shields.io/badge/FastAPI-0.118-c97a4c)]() [![license](https://img.shields.io/badge/license-MIT-b8b0a1)]()

---

## Demo

Run locally (see *Run it* below) and open `http://localhost:8000`. The page has a live demo with shuffleable examples and per-token resolution shown inline.

![demo screenshot](docs/demo-screenshot.png)

---

## Problem

Roman Urdu — Urdu written in Latin script — has no standardized spelling. The word *kya* ("what") shows up online as `kya`, `kia`, `kyaa`. *Bahut* ("very") shows up as `bht`, `bohat`, `bhot`. SMS shorthand like `nhi`, `tk`, `bht`, `kch` drops vowels entirely. Any downstream NLP system that searches, classifies, or aggregates Roman Urdu text breaks immediately on this variation.

This service normalizes incoming text against a curated lexicon — but with one rule it refuses to break: **if it can't confidently resolve a word, it passes the word through unchanged and flags it.** Silent guessing is the failure mode this project guards against.

## Features

- **Three-layer resolution pipeline** — exact variant map, then phonetic key match, then unknown-flagging
- **655 canonical words** across 13 part-of-speech categories (pronouns, interrogatives, verbs, nouns, adjectives, adverbs, conjunctions, greetings, time words, days, numbers, plus homograph members)
- **344 SMS shorthand entries** in the variant map, sourced from real Pakistani WhatsApp / Twitter usage
- **Phonetic key algorithm** — digraph folding (`kh`, `gh`, `sh`, `ch`, `th`, `ph`, `dh`, `bh`, `jh`, `rh`), vowel class collapse (`a`/`aa`, `i`/`y`/`e`, `o`/`u`/`oo`), repeat squashing
- **6 registered homograph groups** (e.g. *kaha* "said" vs *kahan* "where") return `ambiguous: true` with candidates rather than picking one silently
- **Batch endpoint** for normalizing up to 100 strings in a single round trip
- **`/stats` endpoint** exposing per-category lexicon counts
- **CLI tool** with stdin, JSON, and `--stats` modes for shell pipelines
- **Request logging middleware** — one structured line per request
- **Custom exception hierarchy** with proper HTTP status mapping (400, 413, 500)
- **87 tests across 5 files**, including 2 regression tests for bugs found during live demo
- **Docker image** (multi-stage, non-root, healthcheck) and **GitHub Actions CI** (Python 3.10 / 3.11 / 3.12 matrix)

## Architecture

![architecture diagram](docs/architecture.png)

The three-layer design isn't accidental. Each layer exists because the layer above it can't catch a specific failure mode:

1. **Exact variant map (Layer 1)** — handles SMS shorthand like `bht` and `nhi` that the phonetic algorithm cannot reach because it drops too many vowels. O(1) dict lookup, highest priority.

2. **Phonetic key (Layer 2)** — reduces each word to a sound-skeleton and looks it up in a pre-built index over the canonical lexicon. The vowel-class collapse step is the one doing the real work: it turns `kya / kia / kyaa` into the same key.

3. **Unknown (Layer 3)** — nothing matched. The token passes through unchanged with `source: "unknown"`. This is intentional. A normalizer that silently rewrites unknown words is worse than no normalizer: downstream systems trust it and propagate the error.

**Why not just LLMs?** A model call per token is overkill, slow, expensive, and non-deterministic. The whole point is to be a fast, predictable preprocessing step that an LLM-based system sits *on top of*.

**Why FastAPI over Django?** This is a stateless, high-throughput, single-purpose API. Django's ORM and admin would be dead weight; FastAPI gives me auto-generated OpenAPI docs and async support out of the box.

## Tech stack

| Layer    | Choice                                            |
| -------- | ------------------------------------------------- |
| API      | FastAPI 0.118 (auto OpenAPI docs at `/docs`)      |
| Models   | Pydantic v2                                       |
| Server   | Uvicorn                                           |
| CLI      | argparse + stdin pipeline                         |
| Frontend | Vanilla HTML/CSS/JS — no build step               |
| Tests    | pytest + httpx (for fastapi.testclient)           |
| Build    | Docker (multi-stage, non-root), pyproject.toml    |
| CI       | GitHub Actions, Python 3.10 / 3.11 / 3.12 matrix  |

## Run it

Requirements: Python 3.10 or newer.

```bash
# 1. Clone
git clone https://github.com/MughirahNasir/roman-urdu-normalizer.git
cd roman-urdu-normalizer

# 2. Install
python -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Run the server
python -m uvicorn app.main:app --reload

# 4. Open the demo
#    http://localhost:8000              <-- live demo
#    http://localhost:8000/docs         <-- interactive API explorer
#    http://localhost:8000/stats        <-- lexicon stats per category
```

## Run with Docker

```bash
docker build -t roman-urdu-normalizer .
docker run -p 8000:8000 roman-urdu-normalizer
```

## Run the tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

Expected: **87 passed in ~0.6s.**

## Use the CLI

```bash
# pipe input
echo "yr bht thora kch kya kr rhe ho" | python -m app.cli
# → yaar bahut thora kuch kya kar rahe ho

# inline argument
python -m app.cli "kese ho?"
# → kaise ho?

# full JSON output (per-token records and stats)
python -m app.cli --json "yr bht thora"

# print dictionary stats
python -m app.cli --stats
```

## API

### `POST /normalize`

```json
{ "text": "yr bht thora kch kya kr rhe ho" }
```

returns

```json
{
  "input": "yr bht thora kch kya kr rhe ho",
  "normalized": "yaar bahut thora kuch kya kar rahe ho",
  "tokens": [
    { "original": "yr",    "normalized": "yaar",  "source": "variant_map", "ambiguous": false, "candidates": [] },
    { "original": "bht",   "normalized": "bahut", "source": "variant_map", "ambiguous": false, "candidates": [] }
  ],
  "stats": { "total": 8, "variant_map": 6, "phonetic": 1, "unchanged": 1, "unknown": 0, "ambiguous": 0 }
}
```

### `POST /normalize/batch`

Process up to **100 strings** in a single request:

```json
{ "texts": ["yr bht thora", "kese ho?", "kya hai"] }
```

returns

```json
{
  "count": 3,
  "results": [ {"input": "...", "normalized": "...", "tokens": [...], "stats": {...}}, ... ]
}
```

### `GET /stats`

Returns per-category dictionary counts. Useful for debugging or showing in the demo UI.

### `GET /health`

Returns dictionary sizes — useful as a readiness probe.

## What I built myself

- The three-layer resolution logic (`app/normalizer.py`)
- The phonetic key algorithm (`app/phonetic.py`) — every digraph rule and vowel class is hand-picked for Pakistani Roman Urdu
- The curated variant map (344 entries) and canonical lexicon (655 entries across 13 categories) — sourced from real Pakistani WhatsApp / Twitter usage I observed and recognize as a native Urdu speaker
- The homograph guard (6 registered groups)
- All 87 tests, including the two regression tests for bugs caught during live demo
- The custom exception hierarchy, exception handlers, and request logging middleware
- The CLI tool with stdin/JSON/--stats modes
- The dark editorial frontend, including the in-browser fallback so the demo never appears broken
- The Dockerfile, GitHub Actions workflow, and pyproject.toml metadata

## AI assistance

I used Claude as a coding partner during the build. AI scaffolded boilerplate (Pydantic model field definitions, FastAPI route stubs, standard pytest setup). All language data (variant map entries, lexicon words, homograph groups, phonetic rules) was curated by me — I'm a native Urdu speaker, the model is not. Every line was reviewed; the two regression-test bugs were found by me running the live demo with realistic input, not by automated fuzzing.

For the full statement on what AI did and didn't contribute, see [`AUTHENTICITY.md`](AUTHENTICITY.md).

## Bugs I caught and fixed

These are documented as permanent regression tests in `tests/test_regressions.py`:

1. **Short-key collision** — any stray `k` was resolving to `kyun`. Root cause: single-letter canonical entries leaked into the phonetic index, and short tokens collided into the alphabetically-first K-word. Fix: the index now excludes any key of length < 2.

2. **kaha / kahan homograph** — *kaha* ("he/she said") was being silently rewritten to *kahan* ("where") because of a bad variant map entry. Fix: removed the entry, registered `{kaha, kahan}` as a known homograph group, and the normalizer now returns `ambiguous: true` when their phonetic keys collide.

## Project layout

```
.
├── app/                          # the package
│   ├── data.py                   # variant map + 655-word lexicon + homograph groups
│   ├── phonetic.py               # phonetic key algorithm
│   ├── normalizer.py             # three-layer resolver + batch
│   ├── exceptions.py             # custom exception hierarchy
│   ├── models.py                 # Pydantic request/response models
│   ├── main.py                   # FastAPI surface + middleware
│   └── cli.py                    # command-line tool
├── static/index.html             # dark editorial demo frontend
├── tests/                        # 87 tests across 5 files
├── docs/                         # screenshots + architecture diagram
├── .github/workflows/tests.yml   # CI: matrix across Python 3.10/3.11/3.12
├── Dockerfile                    # multi-stage, non-root, healthcheck
├── pyproject.toml                # modern Python project metadata
├── LICENSE                       # MIT
├── CHANGELOG.md                  # Keep a Changelog format
├── CONTRIBUTING.md               # PR guidelines
├── AUTHENTICITY.md               # formal originality statement
├── PROVENANCE.md                 # SHA-256 manifest
├── CERTIFICATE.html              # visual originality certificate
└── PUSH-NOW.md                   # one-shot GitHub publish instructions
```

---

## Originality

This project is part of an 8-piece portfolio I'm building over summer 2026. See [`AUTHENTICITY.md`](AUTHENTICITY.md) for the formal authorship statement, [`PROVENANCE.md`](PROVENANCE.md) for the cryptographic file manifest, and [`CERTIFICATE.html`](CERTIFICATE.html) for a visual summary.

**Author:** Mughirah Nasir · mnasir.bee25seecs@seecs.edu.pk · NUST SEECS, Pakistan
