# Contributing

Thanks for the interest. This is a personal portfolio project, but PRs that fit its philosophy are welcome.

## Scope

This project is a **focused, single-purpose Roman Urdu normalizer**. It is **not** trying to become:

- a full Urdu morphological analyzer
- an Urdu ↔ English machine translation system
- a generic NLP toolkit

If a PR moves the project toward those things, it'll probably be rejected — not because the work isn't valuable, but because it belongs in a different repo.

## Things I'll happily merge

1. **New entries in the variant map** — SMS shorthand that the phonetic algorithm can't reach. Add to `app/data.py` under `VARIANT_MAP`, prove with a test in `tests/test_normalizer.py`.
2. **New canonical lexicon words** — under the appropriate category in `app/data.py`. Native-speaker sourced; please cite usage if it's regional.
3. **New homograph groups** — pairs/triples of canonical words sharing a phonetic key that should NOT silently collapse. Register under `HOMOGRAPH_GROUPS` and add an integrity test.
4. **Regression tests for bugs you find** — even if you don't have a fix, the test alone is valuable.
5. **Frontend polish** that respects the dark editorial aesthetic and the "works offline" guarantee.

## Things I'll probably push back on

- **PRs that disable the "never silently guess" rule.** This rule is the entire point. The unknown layer must never rewrite a token without flagging it. If you have a reason to change this, open an issue first.
- **Reduce-the-lexicon PRs.** This project is the lexicon. Pruning rarely helps.
- **Heavy ML dependencies** (transformers, torch, etc.). The normalizer is meant to be the small, fast, predictable preprocessing layer that sits *under* an LLM, not another LLM call. Keep it lean.

## Dev setup

```bash
git clone https://github.com/Mughirah-Nasir/roman-urdu-normalizer.git
cd roman-urdu-normalizer
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

## Running tests

```bash
python -m pytest tests/ -v
```

Expected: **162 / 162 passing.** Faster than 1 second.

## Style

- **Code:** PEP 8, but Black-formatted is fine too.
- **Docstrings:** module-level docstrings are required for `app/*.py`. They should explain *why* the file exists, not just summarize the code.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`). Tense: imperative ("add tests", not "added tests"). Subject under 72 chars. If you need more, drop a blank line and write a body.
- **Tests:** every behavior change comes with a test. Untested PRs get held until tests show up.

## Reporting issues

If the normalizer rewrites a word wrong — that's the most important kind of bug for this project. Open an issue with:

1. The input string
2. The output you got
3. The output you expected
4. (Bonus) a one-line pytest case demonstrating the bug

These almost always land as new entries in `tests/test_regressions.py`.

## Contact

Mughirah Nasir · mnasir.bee25seecs@seecs.edu.pk · NUST SEECS
