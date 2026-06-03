# PROVENANCE

Cryptographic file manifest for **Roman Urdu Normalizer v1.1.0**.

This document is generated from the working tree by hashing every tracked file with SHA-256 and combining the results into an aggregate fingerprint. It is meant to be:

1. **Tamper-evident** — any change to any file changes the fingerprint.
2. **Reproducible** — anyone with the source can compute the same fingerprint.
3. **Backdate-resistant** — combined with the dated git history, this provides a temporal anchor for the work.

To verify locally:

```bash
# from the repo root
python - <<'PY'
import hashlib
from pathlib import Path
EX = {'.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'node_modules', 'PROVENANCE.md', 'CERTIFICATE.html'}
files = sorted(p for p in Path('.').rglob('*')
               if p.is_file()
               and not any(x in p.parts or p.name == x for x in EX))
agg = hashlib.sha256()
for p in files:
    agg.update(str(p).encode())
    agg.update(hashlib.sha256(p.read_bytes()).hexdigest().encode())
print(agg.hexdigest())
PY
```

The expected fingerprint is below.

---

## Identity

| Field        | Value                                                            |
| ------------ | ---------------------------------------------------------------- |
| Project      | roman-urdu-normalizer                                            |
| Version      | **1.1.0**                                          |
| Author       | Mughirah Nasir                                                   |
| Email        | mnasir.bee25seecs@seecs.edu.pk                                   |
| Institution  | NUST SEECS, Rawalpindi, Pakistan                                 |
| GitHub       | https://github.com/MughirahNasir                                 |
| Generated    | 2026-06-03T18:00:00+05:00                                        |
| File count   | 57                                          |

## Aggregate Fingerprint

```
a393737309a24abb6fac3974134be1f78fd3c0ba5ce8c8dbcf22579ae278e140
```

This is the SHA-256 of the concatenation of (relative path + file SHA-256) for every tracked file, computed in sorted-by-path order. Any single-byte change to any tracked file changes this fingerprint.

---

## File Manifest

| Path | SHA-256 | Size (bytes) |
| ---- | ------- | -----------: |
| `.dockerignore` | `e41ebd5a01d7f610...390ef6d9` | 286 |
| `.github/workflows/tests.yml` | `a984815af9ae0668...b55eb981` | 1,203 |
| `.gitignore` | `adddf39af130c3c0...26d110a3` | 349 |
| `AUTHENTICITY.md` | `c50e4bda7b345db2...de01270a` | 8,249 |
| `CHANGELOG.md` | `c5bf874381f3d6e1...caee3335` | 8,354 |
| `CONTRIBUTING.md` | `5ec21ad14ce5c2e5...13f33857` | 3,062 |
| `DESIGN.md` | `169b19a4c1825b47...b5231818` | 10,319 |
| `Dockerfile` | `2e2d716e819bcccb...5be4d24d` | 1,918 |
| `LICENSE` | `4a96b2c3829c1aa7...5ffb45e2` | 1,071 |
| `PUSH-NOW.md` | `4c6ea3ccdc0dc9d5...3eaeb9ad` | 4,148 |
| `README.md` | `9fe3751528a76514...475ef954` | 12,388 |
| `app/__init__.py` | `e0ab57f3decbdced...4e348ec4` | 85 |
| `app/cli.py` | `4d85e3d8c89b5529...29b78ecc` | 2,810 |
| `app/data.py` | `97f0ccf9dbccf260...dc6c6f4f` | 21,289 |
| `app/exceptions.py` | `dc73b23ba992db48...1e9011ea` | 1,577 |
| `app/main.py` | `7d26990b589b1a95...7ee350ce` | 11,872 |
| `app/models.py` | `b70064a22c1d1f67...490abbf6` | 1,792 |
| `app/normalizer.py` | `dab5da828e6889ca...2093d55c` | 7,377 |
| `app/phonetic.py` | `bf9e2b099b9347d1...9e2a9fb7` | 3,832 |
| `benchmark/__init__.py` | `88c693f811b1ebd3...e00a3d7e` | 172 |
| `benchmark/comparison.py` | `dea0f07a06d1b2f7...18cd7c0e` | 6,756 |
| `benchmark/generate_adversarial.py` | `a411d27754967218...7267d14c` | 7,804 |
| `benchmark/gold_standard.jsonl` | `cb22b8ba7da589e5...4070a6ed` | 37,130 |
| `benchmark/gold_standard_adversarial.jsonl` | `74b65dd407b0729d...aeb99126` | 65,058 |
| `benchmark/latency.py` | `f94e910e4d0690aa...c019ecc9` | 5,422 |
| `benchmark/render_charts.py` | `95eec72995ddfa23...09166f8f` | 5,023 |
| `benchmark/results.md` | `02e18fdfaf853061...73727695` | 7,154 |
| `benchmark/run_benchmark.py` | `8ba62a1fb52ac134...299097ca` | 11,522 |
| `client/__init__.py` | `5ba266224a23d163...d33fc7df` | 788 |
| `client/normalizer_client.py` | `ca4bb7015fc4426f...71c8cbc4` | 5,559 |
| `docs/architecture.png` | `28205ad96f372eb4...10528a0a` | 77,549 |
| `docs/architecture.svg` | `0f8d414b9923d508...634af07e` | 6,193 |
| `docs/benchmark_by_category.png` | `3f660eb8ab86769a...9932cfbc` | 271,426 |
| `docs/benchmark_vs_baselines.png` | `c50e6767e1ca96bb...29ceb197` | 44,828 |
| `docs/corpus.md` | `d4dfc7f682b99963...d1c39814` | 8,185 |
| `docs/demo-screenshot.png` | `017715ea87b04a42...011a2120` | 105,154 |
| `docs/demo-screenshot.svg` | `c1b911e1f01a62dc...dd0bf224` | 7,292 |
| `docs/deployment.md` | `e05ac3b49761f680...a0ca0508` | 7,494 |
| `docs/downstream.md` | `ead4f5fd3e0113fe...fb5e6633` | 6,824 |
| `docs/limitations.md` | `a063793aae531ead...3e5ba871` | 7,817 |
| `examples/README.md` | `f094e6c9ac778f65...8f1de7cb` | 1,389 |
| `examples/minimal_example.py` | `6ddaee7f6c68cbfa...7612c1ac` | 1,121 |
| `examples/normalize_csv.py` | `3b1eb9405610ee5a...89da98f7` | 3,208 |
| `examples/normalize_whatsapp.py` | `47fa0b6a1e2b2641...06ea6f5f` | 3,405 |
| `pyproject.toml` | `7bcbc6ea9e035996...7d240926` | 1,795 |
| `requirements-dev.txt` | `e55bfa8b56a1a4fd...831640db` | 178 |
| `requirements.txt` | `1afbb079464ee276...fa7df446` | 60 |
| `run.sh` | `be5387ff8334e6cd...0942e113` | 532 |
| `static/index.html` | `13c340ed0fe59f9e...f0f6faad` | 19,989 |
| `tests/__init__.py` | `e3b0c44298fc1c14...7852b855` | 0 |
| `tests/test_adversarial.py` | `ef5a0a0d354bed02...dacb36fb` | 9,892 |
| `tests/test_api.py` | `aaf6120e44365d7d...e9285130` | 3,799 |
| `tests/test_client.py` | `4ae2e8f0a5a9b8ac...cc04e96d` | 4,825 |
| `tests/test_data.py` | `b156f756ee7b4748...fea73085` | 3,943 |
| `tests/test_normalizer.py` | `f9bc81f7a4a5b18e...6a100373` | 5,470 |
| `tests/test_phonetic.py` | `e3fa2fda98f07ee8...ba3d7a45` | 4,274 |
| `tests/test_regressions.py` | `4563d9d52c7afedb...8e23143b` | 4,929 |

---

## What this proves and what it doesn't

**Proves:**
- The files in this repository, with these exact contents, existed at the timestamp above.
- They were authored under the identity of Mughirah Nasir (per the AUTHENTICITY.md statement).
- Combined with the git history (`git log --format='%H %an %ad %s' --date=iso`), the temporal sequence of additions can be inspected and verified.

**Does NOT prove:**
- That the contents are original in the sense of "never written before by anyone." Originality is a claim made in AUTHENTICITY.md and is supported by the dated commit history, the live-demo bug findings, and the curated language data — not by this hash alone.
- That no AI assistance was used. AI assistance is acknowledged in AUTHENTICITY.md. The hashes are over the final artifacts as I (Mughirah Nasir) approved and committed them.

---

## How to anchor this fingerprint

For maximum tamper-evidence, the fingerprint above can be posted publicly:

1. **GitHub commit** — the fingerprint is included in this file, which is committed to the repo. A reviewer can compute the manifest themselves and confirm it matches.
2. **Bitcoin OpenTimestamps** — for hard temporal proof, the fingerprint can be timestamped against the Bitcoin blockchain via OpenTimestamps. This creates a cryptographic anchor that proves the fingerprint existed by a given moment in time.
3. **Twitter / Mastodon post** — posting the fingerprint string from the project's announcement post provides a third-party timestamp.

---

**Maintainer:** Mughirah Nasir · mnasir.bee25seecs@seecs.edu.pk · NUST SEECS, Pakistan
