# Roman Urdu Normalizer

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)]() [![tests](https://img.shields.io/badge/tests-162%20passing-success)]() [![F1](https://img.shields.io/badge/F1-90.1%25-success)]() [![License](https://img.shields.io/badge/License-MIT-yellow.svg)]() [![version](https://img.shields.io/badge/version-1.2.1-informational)]()

## In simple words

This project cleans messy Pakistani Roman Urdu spellings and converts common variations into one standard form.

A few examples:

| Input | Normalized |
| --- | --- |
| `nhi`, `nai`, `nahin` | `nahi` |
| `bht`, `bohat`, `bhot` | `bahut` |
| `yr`, `yar` | `yaar` |
| `kr rha`, `kar raha` | `kar raha` |
| `kch`, `kuch` | `kuch` |
| `ho gya` | `ho gaya` |

The goal is to make Roman Urdu text easier to search, analyze, and feed into NLP or AI systems. This is a normalizer, not a translator. It does not turn Urdu into English. It takes one informal Urdu spelling and gives you the canonical one.

## The problem

Pakistani people write Urdu using English letters all the time. WhatsApp, Twitter, Instagram, comment sections, customer reviews, freelance project briefs, all of it is full of Roman Urdu. The trouble is that there are usually four or five accepted spellings for the same word. `nahi`, `nahin`, `nhi`, `nai`, `nae`, all mean the same thing. If you try to run search, deduplication, sentiment analysis, or any kind of analytics on this text, the spelling variation kills your recall before you even start.

This project sits in front of those downstream systems and collapses the variation. After normalization, a search for `nahi` finds reviews that wrote `nhi`, and a sentiment classifier sees the same token whether the user typed `bohat` or `bht`.

## How it works

Four resolution layers in order. The first one that finds a confident answer wins. Anything that reaches the unknown layer is passed through unchanged with a flag.

1. **Phrase layer.** Looks for multi-token compound forms first, things like `kr de`, `ja rha`, `ho gya`. These cannot be resolved one token at a time because the second token's meaning depends on the first. There are about 125 curated phrases in this layer.
2. **Variant map.** A curated dictionary of around 430 SMS-style shorthand entries. `bht` to `bahut`, `nhi` to `nahi`, `yr` to `yaar`. This handles the cases where Urdu speakers drop vowels aggressively.
3. **Phonetic match.** A phonetic key algorithm collapses vowel and digraph variation, then looks the result up against the canonical lexicon of 655 words. `kya`, `kia`, `kyaa` all reduce to the same key.
4. **Unknown.** If nothing matched, the token passes through unchanged and the response marks it as unknown with confidence zero. The system never silently guesses.

Each token in the response carries a `source` field telling you which layer produced it, and a `confidence` score from 0.0 to 1.0. Downstream code can threshold on that.

The design rule that drives the whole thing is **never silently guess**. If the system isn't sure, it says so instead of pretending.

## Demo

```bash
curl -X POST http://localhost:8000/normalize \
     -H 'Content-Type: application/json' \
     -d '{"text": "yr bht thora kch kya kr rhe ho"}'
```

```json
{
  "input": "yr bht thora kch kya kr rhe ho",
  "normalized": "yaar bahut thora kuch kya kar rahe ho",
  "tokens": [
    {"original": "yr",    "normalized": "yaar",    "source": "variant_map", "confidence": 1.0,  "ambiguous": false},
    {"original": "bht",   "normalized": "bahut",   "source": "variant_map", "confidence": 1.0,  "ambiguous": false},
    {"original": "thora", "normalized": "thora",   "source": "unchanged",   "confidence": 1.0,  "ambiguous": false},
    {"original": "kch",   "normalized": "kuch",    "source": "variant_map", "confidence": 1.0,  "ambiguous": false},
    {"original": "kya",   "normalized": "kya",     "source": "unchanged",   "confidence": 1.0,  "ambiguous": false},
    {"original": "kr rhe","normalized": "kar rahe","source": "phrase_map",  "confidence": 1.0,  "ambiguous": false, "span_tokens": 2},
    {"original": "ho",    "normalized": "ho",      "source": "unchanged",   "confidence": 1.0,  "ambiguous": false}
  ],
  "stats": {
    "total": 7, "variant_map": 3, "phrase_map": 1,
    "phonetic": 0, "unchanged": 3, "unknown": 0, "ambiguous": 0,
    "avg_confidence": 1.0, "min_confidence": 1.0
  }
}
```

![Dashboard screenshot](docs/demo-screenshot.png)

## How to run

Tested on Python 3.10, 3.11, and 3.12. Clone or unzip the project, then:

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS or Linux
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open `http://localhost:8000` in a browser for the dashboard, or `http://localhost:8000/docs` for the auto-generated FastAPI documentation.

For tests:

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

You should see 162 tests pass in under two seconds.

## CLI

```bash
python -m app.cli "yr bht kch"
# yaar bahut kuch

python -m app.cli --stats "yr bht kch"
# adds a stats summary

python -m app.cli --json "yr bht kch"
# full JSON response on stdout
```

## Python client

A small SDK lives in `client/`. It has zero third-party dependencies and uses `urllib`:

```python
from client import RomanUrduNormalizerClient

c = RomanUrduNormalizerClient("http://localhost:8000")
result = c.normalize("yr bht thora kch")
print(result["normalized"])  # yaar bahut thora kuch
```

## Benchmark and tests

The benchmark dataset has 250 hand-curated examples plus 242 adversarial perturbations generated from them. Running the policy over the combined 492-example set gives F1 of 90.1 percent and sentence-level accuracy of 63.2 percent.

There is also a separate 100-example blind held-out set in `benchmark/heldout.jsonl`. This was written specifically for evaluation and was never used to inform the variant map or lexicon. Score on the blind set: F1 89.3 percent, sentence accuracy 44.0 percent. The blind number being within one F1 point of the in-sample number is the generalization signal.

Run them yourself:

```bash
python -m benchmark.run_benchmark --dataset combined
python -m benchmark.run_benchmark --dataset heldout.jsonl
python -m benchmark.comparison
python -m benchmark.latency
```

The comparison study scores four strategies on the combined 492-example dataset (hand-curated + adversarial), reproducible by `python -m benchmark.comparison`:

| Strategy | Sentence accuracy | Token F1 |
| --- | ---: | ---: |
| Baseline: naive replace | 3.7% | 39.4% |
| Baseline: Levenshtein nearest | 10.8% | 51.9% |
| Baseline: TF-IDF char n-gram, sklearn-trained | 16.1% | 60.5% |
| **Four-layer pipeline (this project)** | **63.2%** | **90.1%** |

![Benchmark vs baselines](docs/benchmark_vs_baselines.png)

The ML baseline is a real character n-gram TF-IDF nearest-neighbor classifier. The pipeline still beats it by 29 F1 points, which is the comparison story.

## Limitations

This is documented in detail in `docs/limitations.md`. The short version:

The system has no context awareness. Tokens are resolved with at most a two- or three-token look-around, and only for phrases that were curated up front. Homographs like `kaha` and `kahan` are flagged as ambiguous rather than disambiguated.

The confidence scores are currently heuristic, not statistically calibrated. They reflect which layer produced the resolution, not an observed accuracy distribution.

The lexicon is hand-curated for Pakistani Urdu. It will under-perform on Indian Hindi-Urdu and on regional dialects without lexicon expansion.

Code-switching with English works for tokens the lexicon has seen, but rare English words get flagged as unknown.

A handful of concrete failure examples are listed in `docs/limitations.md`.

## Project structure

```
roman-urdu-normalizer/
├── app/                      # the FastAPI application
│   ├── __init__.py
│   ├── main.py               # FastAPI entry point (uvicorn app.main:app)
│   ├── normalizer.py         # the four-layer pipeline
│   ├── phonetic.py           # phonetic key algorithm
│   ├── multitoken.py         # phrase-layer rewrites
│   ├── data.py               # canonical lexicon + variant map + homograph groups
│   ├── models.py             # Pydantic request/response schemas
│   ├── exceptions.py         # custom exceptions
│   └── cli.py                # command-line interface
├── tests/                    # 162 tests in 8 files
├── benchmark/                # gold-standard, adversarial, held-out, comparison study
├── client/                   # Python client SDK (zero third-party dependencies)
├── examples/                 # runnable integration scripts
├── docs/                     # design docs and benchmark charts
├── scripts/
│   └── review_unknowns.py    # operator tool: top unknowns to variant map entries
├── static/index.html         # dashboard frontend
├── .github/workflows/        # CI matrix on Python 3.10 / 3.11 / 3.12
├── Dockerfile
├── render.yaml
├── pyproject.toml
└── README.md
```

## What's in this repo and what is not

Honest about scope.

The variant map, the phonetic algorithm, the phrase map, the 250-example benchmark dataset, the adversarial generator, the four-layer pipeline, the FastAPI app, the CLI, the client SDK, all 162 tests, the dashboard frontend, the Dockerfile, and every word of documentation were all written for this project. AI assistance was used during development for editorial review and refactoring suggestions. Architectural decisions and the lexicon content are mine.

The repo does not include a hosted demo URL. The `render.yaml` is a deployment template. If you fork and click Deploy on Render.com it should provision, but I have not kept a live demo running.

The blind held-out evaluation is small at 100 examples. It supports the generalization claim but is not a substitute for evaluation on truly external user data, which I do not have.

See `AUTHENTICITY.md` for the formal statement and `PROVENANCE.md` for the SHA-256 file manifest.

## License

MIT. See `LICENSE`.

## Author

**Mughirah Nasir** · NUST SEECS, Rawalpindi, Pakistan · mnasir.bee25seecs@seecs.edu.pk

Repository: https://github.com/Mughirah-Nasir/roman-urdu-normalizer
