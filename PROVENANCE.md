# PROVENANCE

Cryptographic file manifest for **Roman Urdu Normalizer v1.2.1**.

This document is generated from the working tree by hashing every tracked file with SHA-256 and combining the results into an aggregate fingerprint. It is tamper-evident in the sense that any change to any file changes the fingerprint, and reproducible in the sense that anyone with the source can recompute the same number.

## Identity

| Field | Value |
| --- | --- |
| Project | roman-urdu-normalizer |
| Version | **v1.2.1** |
| Author | Mughirah Nasir |
| Email | mnasir.bee25seecs@seecs.edu.pk |
| Institution | NUST SEECS, Rawalpindi, Pakistan |
| GitHub | https://github.com/Mughirah-Nasir |
| Repository | https://github.com/Mughirah-Nasir/roman-urdu-normalizer |
| Generated at packaging time | 2026-06-07T17:00:00+05:00 |
| File count | 64 |

## Aggregate fingerprint

```
c57ee94edc3e00308880fa0a7db29f8a1b8bc37030b7ef38eba80f6f77ce3398
```

This is the SHA-256 of the concatenation of (relative path + file SHA-256) for every tracked file, computed in sorted-by-path order. Any single-byte change to any tracked file changes this value.

To verify locally:

```bash
python - <<'PY'
import hashlib
from pathlib import Path
EX_PARTS = {'.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'node_modules'}
EX_NAMES = {'PROVENANCE.md', 'CERTIFICATE.html', '.DS_Store'}
files = sorted(p for p in Path('.').rglob('*')
               if p.is_file()
               and not any(x in p.parts for x in EX_PARTS)
               and p.name not in EX_NAMES)
agg = hashlib.sha256()
for p in files:
    agg.update(str(p.relative_to('.')).replace('\\','/').encode())
    agg.update(hashlib.sha256(p.read_bytes()).hexdigest().encode())
print(agg.hexdigest())
PY
```

## File manifest

| Path | SHA-256 (first 16 / last 8 chars) | Size (bytes) |
| --- | --- | ---: |
| `.dockerignore` | `e41ebd5a01d7f610...390ef6d9` | 286 |
| `.github/workflows/tests.yml` | `a984815af9ae0668...b55eb981` | 1,203 |
| `.gitignore` | `adddf39af130c3c0...26d110a3` | 349 |
| `AUTHENTICITY.md` | `74a7dff8d1ac8656...8fd8d149` | 9,599 |
| `CHANGELOG.md` | `b1d718c28a119e48...337c3a98` | 14,547 |
| `CONTRIBUTING.md` | `a64cbe0e328e756c...a2c90b38` | 3,065 |
| `DESIGN.md` | `f5c1ba6862f9e866...4f89ffce` | 11,213 |
| `Dockerfile` | `2e2d716e819bcccb...5be4d24d` | 1,918 |
| `FINAL-CHECKLIST.md` | `449c569c82245845...ffa887d9` | 5,841 |
| `LICENSE` | `4a96b2c3829c1aa7...5ffb45e2` | 1,071 |
| `README.md` | `39c79d61e94647ff...9df81f81` | 10,446 |
| `app/__init__.py` | `bfd21a033ccf1f05...1877b995` | 85 |
| `app/cli.py` | `4d85e3d8c89b5529...29b78ecc` | 2,810 |
| `app/data.py` | `97f0ccf9dbccf260...dc6c6f4f` | 21,289 |
| `app/exceptions.py` | `dc73b23ba992db48...1e9011ea` | 1,577 |
| `app/main.py` | `b0579b397d4af827...5e5e7769` | 11,911 |
| `app/models.py` | `be8cebf066fbc414...6758096c` | 2,641 |
| `app/multitoken.py` | `4f041d5333400cbb...8d51a2c7` | 9,799 |
| `app/normalizer.py` | `6c198135fcee5a1b...9ef99f28` | 10,415 |
| `app/phonetic.py` | `bf9e2b099b9347d1...9e2a9fb7` | 3,832 |
| `benchmark/__init__.py` | `88c693f811b1ebd3...e00a3d7e` | 172 |
| `benchmark/comparison.py` | `e6a520d9c3ecbc72...933d8044` | 10,242 |
| `benchmark/generate_adversarial.py` | `a411d27754967218...7267d14c` | 7,804 |
| `benchmark/gold_standard.jsonl` | `cb22b8ba7da589e5...4070a6ed` | 37,130 |
| `benchmark/gold_standard_adversarial.jsonl` | `74b65dd407b0729d...aeb99126` | 65,058 |
| `benchmark/heldout.jsonl` | `beb561e5d27417ae...0d19c6ae` | 21,975 |
| `benchmark/latency.py` | `f94e910e4d0690aa...c019ecc9` | 5,422 |
| `benchmark/render_charts.py` | `e05988ae2269c270...1e20989a` | 5,144 |
| `benchmark/results.md` | `2efeda501f2a24f5...c7af2493` | 5,345 |
| `benchmark/run_benchmark.py` | `8ba62a1fb52ac134...299097ca` | 11,522 |
| `client/__init__.py` | `5ba266224a23d163...d33fc7df` | 788 |
| `client/normalizer_client.py` | `ca4bb7015fc4426f...71c8cbc4` | 5,559 |
| `docs/architecture.png` | `3dceb217013cc543...c9c0deec` | 193,933 |
| `docs/architecture.svg` | `cb7dcdbbe3806a56...12181ae2` | 7,680 |
| `docs/benchmark_by_category.png` | `bb268cb72e4cb332...10bf7351` | 271,635 |
| `docs/benchmark_vs_baselines.png` | `b7bffce5c0713b28...2b3c0363` | 48,265 |
| `docs/corpus.md` | `d4dfc7f682b99963...d1c39814` | 8,185 |
| `docs/demo-screenshot.png` | `8637be7c814ec087...625a9a55` | 161,075 |
| `docs/demo-screenshot.svg` | `2b56f6cf37c31c4a...43abdd07` | 7,292 |
| `docs/deployment.md` | `d56e0f04b22e88c5...fa8be3d6` | 7,495 |
| `docs/downstream.md` | `ead4f5fd3e0113fe...fb5e6633` | 6,824 |
| `docs/limitations.md` | `a063793aae531ead...3e5ba871` | 7,817 |
| `examples/README.md` | `f094e6c9ac778f65...8f1de7cb` | 1,389 |
| `examples/minimal_example.py` | `6ddaee7f6c68cbfa...7612c1ac` | 1,121 |
| `examples/normalize_csv.py` | `3b1eb9405610ee5a...89da98f7` | 3,208 |
| `examples/normalize_whatsapp.py` | `47fa0b6a1e2b2641...06ea6f5f` | 3,405 |
| `examples/search_recall_demo.py` | `99735a026f09420f...473fcec8` | 5,543 |
| `pyproject.toml` | `61b0dca001ea5ad4...577a38fc` | 1,843 |
| `render.yaml` | `92953bba00e30571...e970ea3f` | 1,378 |
| `requirements-dev.txt` | `f6435de409791690...6e2fab2a` | 421 |
| `requirements.txt` | `1afbb079464ee276...fa7df446` | 60 |
| `run.sh` | `da2fb7ba9873cee8...d6ae7b70` | 532 |
| `scripts/__init__.py` | `760327dfd1583157...60f30e6a` | 200 |
| `scripts/review_unknowns.py` | `28931b0bf8e6c805...dce14bfb` | 9,999 |
| `static/index.html` | `abaf601cb0cc200e...98eb6069` | 19,990 |
| `tests/__init__.py` | `e3b0c44298fc1c14...7852b855` | 0 |
| `tests/test_adversarial.py` | `bab7d9aff4c9e983...06a2a294` | 9,894 |
| `tests/test_api.py` | `aaf6120e44365d7d...e9285130` | 3,799 |
| `tests/test_client.py` | `4ae2e8f0a5a9b8ac...cc04e96d` | 4,825 |
| `tests/test_data.py` | `b156f756ee7b4748...fea73085` | 3,943 |
| `tests/test_multitoken.py` | `f86ad0c99e706f52...f2310064` | 7,450 |
| `tests/test_normalizer.py` | `a65c6bc3bdbd273a...004be2a5` | 5,858 |
| `tests/test_phonetic.py` | `e3fa2fda98f07ee8...ba3d7a45` | 4,274 |
| `tests/test_regressions.py` | `4563d9d52c7afedb...8e23143b` | 4,929 |

## What this proves and what it does not

**Proves:** the files in this repository, with these exact contents, existed at the timestamp above. Combined with the dated git history (visible in `git log --format='%H %an %ad %s' --date=iso`), the temporal sequence can be inspected.

**Does not prove:** that the contents are original in the sense of never written before by anyone. Originality is a claim made in `AUTHENTICITY.md` and is supported by the dated commit history and curated content, not by this hash alone.

It also does not prove that no AI assistance was used. AI assistance is acknowledged in `AUTHENTICITY.md`. The hashes are over the final artifacts as the author approved and committed them.

---

**Maintainer:** Mughirah Nasir · mnasir.bee25seecs@seecs.edu.pk · NUST SEECS, Pakistan
