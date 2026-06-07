# FINAL-CHECKLIST.md

A direct accounting of what is in this repo and what state it is in, so the README claims and the actual files line up.

Version: v1.2.1
Author: Mughirah Nasir
Repository: https://github.com/Mughirah-Nasir/roman-urdu-normalizer

## 1. Folders included

| Folder | Status |
| --- | --- |
| `app/` | Present. 9 files. Real implementation of the four-layer pipeline. |
| `tests/` | Present. 8 test files, 162 tests collected, all passing. |
| `benchmark/` | Present. Gold-standard, adversarial, held-out datasets, three runner scripts, comparison study, latency suite, render_charts. |
| `client/` | Present. Single-file SDK using `urllib`, with `__init__.py` exporting `RomanUrduNormalizerClient`. |
| `examples/` | Present. README plus four runnable scripts. |
| `docs/` | Present. Four markdown files plus the architecture diagram, two benchmark charts, and a demo screenshot in both PNG and SVG. |
| `scripts/` | Present. `review_unknowns.py` operator tool referenced in CHANGELOG. |
| `static/` | Present. `index.html` dashboard frontend served by FastAPI. |
| `.github/workflows/` | Present. `tests.yml` for the CI matrix. |

## 2. How to run the app

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS or Linux
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Open `http://localhost:8000` for the dashboard.

## 3. How to run tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

## 4. Actual test count

**162 tests, all passing.** Runs in roughly 0.7 seconds on the development machine.

Distribution across files:

```
tests/test_adversarial.py    — adversarial robustness
tests/test_api.py            — FastAPI endpoint tests
tests/test_client.py         — Python client SDK
tests/test_data.py           — variant map, lexicon, homograph integrity
tests/test_multitoken.py     — phrase layer + confidence scoring
tests/test_normalizer.py     — main pipeline behavior
tests/test_phonetic.py       — phonetic key algorithm
tests/test_regressions.py    — pinned regressions for past bugs
```

Verified by running `python -m pytest tests/ --collect-only -q | tail -5` immediately before packaging.

## 5. Benchmark numbers

Verified by running both benchmarks immediately before packaging.

| Dataset | Examples | Token F1 | Sentence accuracy |
| --- | ---: | ---: | ---: |
| `combined` (250 hand-curated + 242 adversarial) | 492 | 90.1% | 63.2% |
| `heldout.jsonl` (blind, never used for lexicon work) | 100 | 89.3% | 44.0% |

Comparison study against four strategies on the combined dataset (reproducible by `python -m benchmark.comparison`):

| Strategy | Sentence accuracy | Token F1 |
| --- | ---: | ---: |
| naive_replace | 3.7% | 39.4% |
| Levenshtein nearest | 10.8% | 51.9% |
| TF-IDF char n-gram (sklearn) | 16.1% | 60.5% |
| four-layer pipeline | 63.2% | 90.1% |

The sklearn TF-IDF baseline requires `scikit-learn` which is in `requirements-dev.txt`, not in `requirements.txt`.

## 6. PROVENANCE regeneration

`PROVENANCE.md` was regenerated against the final file tree at packaging time. The aggregate SHA-256 fingerprint at the top of that file matches the current state of the repo, computed over the manifest of tracked files in sorted-by-path order (excluding `.git/`, `__pycache__/`, `.pytest_cache/`, and `PROVENANCE.md` and `CERTIFICATE.html` themselves).

Reviewers can recompute it locally with the Python snippet included inside `PROVENANCE.md`.

## 7. Docker

`Dockerfile` is included. It uses a multi-stage build, runs as a non-root user, exposes port 8000, and includes a healthcheck against `/health`.

**Not tested in this packaging cycle.** It worked in earlier development cycles. The build command and run command should both work as documented, but I am being explicit: I did not run `docker build` and `docker run` as part of preparing this zip.

## 8. Render deployment

`render.yaml` is included as a Render.com Blueprint. It sets `ALLOWED_ORIGINS=*` for the demo, a rate limit of 60 requests per minute, and a 1 MB request body cap.

**Not verified end-to-end on Render in this packaging cycle.** The file is a deployment template, not proof of a hosted live demo. If you fork the repo, click Deploy on Render, and it provisions, it should be usable. I do not currently keep a live demo URL running.

## 9. Broken links or images

The README references four images. All four exist in `docs/`:

- `docs/demo-screenshot.png`
- `docs/benchmark_vs_baselines.png`
- `docs/benchmark_by_category.png` (linked from `docs/limitations.md`)
- `docs/architecture.png` (linked from `DESIGN.md`)

The badges at the top of the README are shields.io placeholders. They are not wired to a live GitHub Actions status because the repo has not been pushed yet. Once pushed, the CI workflow will run automatically on push and pull request to main.

## 10. Ready to push to GitHub

Yes, with these caveats clearly stated.

To publish:

```bash
cd roman-urdu-normalizer
git init
git add .
git commit -m "Initial commit: Roman Urdu Normalizer v1.2.1"
git branch -M main
git remote add origin https://github.com/Mughirah-Nasir/roman-urdu-normalizer.git
git push -u origin main
```

If the repo was prepared with full git history included (a `.git` folder in the zip), the commits are already dated and you can push directly.

## Things deliberately removed from this packaging

- `PUSH-NOW.md`, `PUSH-WINDOWS.ps1`, `PUSH-MAC-LINUX.sh`, and `OPEN-ME-FIRST.txt` are NOT in this zip. Those were local helper files. The instructions above are sufficient.
- Earlier zips contained these helpers. This one does not.

## Things I did not implement and removed from the docs

Nothing. Every feature the README describes is implemented. If you find a discrepancy I missed, please open an issue.
