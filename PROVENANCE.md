# PROVENANCE

Cryptographic file manifest for **Roman Urdu Normalizer v1.2.1**.

This document records the SHA-256 hash of each tracked project file. If any tracked file changes, the aggregate fingerprint changes too.

To verify locally:

```bash
python - <<'PY'
import hashlib
from pathlib import Path
EX = {'.git', '__pycache__', '.pytest_cache', '.ruff_cache', 'venv', '.venv', 'node_modules', 'PROVENANCE.md', 'CERTIFICATE.html'}
files = sorted(p for p in Path('.').rglob('*') if p.is_file() and not any(x in p.parts or p.name == x for x in EX))
agg = hashlib.sha256()
for p in files:
    agg.update(str(p).encode())
    agg.update(hashlib.sha256(p.read_bytes()).hexdigest().encode())
print(agg.hexdigest())
PY
```

## Identity

| Field | Value |
| --- | --- |
| Project | roman-urdu-normalizer |
| Version | **1.2.1** |
| Author | Mughirah Nasir |
| Email | mnasir.bee25seecs@seecs.edu.pk |
| Institution | NUST SEECS, Pakistan |
| GitHub | https://github.com/Mughirah-Nasir |
| File count | 64 |

## Aggregate Fingerprint

```
cd5579fafbbf46f291b85dc19aa0bb83289a407c7a0059e92cfa280103e7480d
```

## File Manifest

| Path | SHA-256 | Size bytes |
| --- | --- | ---: |
| `.dockerignore` | `e41ebd5a01d7f610070bf633b8dae26069646856bfff41e5c8af5255390ef6d9` | 286 |
| `.github/workflows/tests.yml` | `a984815af9ae06689d40363a72ae982ca678a3dc161881ba920cff31b55eb981` | 1,203 |
| `.gitignore` | `adddf39af130c3c031881ffe1f1a4b77406154b36a63393d21dfe79d26d110a3` | 349 |
| `AUTHENTICITY.md` | `74a7dff8d1ac865685a787ced7cf039ed7e538858efe799fecd3ab3d8fd8d149` | 9,599 |
| `CHANGELOG.md` | `b1d718c28a119e48a93fe7760e23099e3ec0ad40222259ffa0a28239337c3a98` | 14,547 |
| `CONTRIBUTING.md` | `a64cbe0e328e756cb3e299683344cbc741e47a7c96983364a570f8bba2c90b38` | 3,065 |
| `DESIGN.md` | `f5c1ba6862f9e8663cb961b4f894822ad9483dc0f04c30b4421c5e154f89ffce` | 11,213 |
| `Dockerfile` | `2e2d716e819bcccb3103e369c86acdb07b1b7c1b4689ff72ae7c04345be4d24d` | 1,918 |
| `FINAL-CHECKLIST.md` | `449c569c8224584582bcf595b0f1caf027c022a5327b3e64b9dbbca8ffa887d9` | 5,841 |
| `LICENSE` | `4a96b2c3829c1aa7eea3dace01c2f953153e81c084021196f3340cad5ffb45e2` | 1,071 |
| `README.md` | `39c79d61e94647ffd3c59dd302a0907433d64fd4610fb0132b129c709df81f81` | 10,446 |
| `app/__init__.py` | `bfd21a033ccf1f0582fac238d9cc3f4e3a11edf5ca6069560de97be71877b995` | 85 |
| `app/cli.py` | `4d85e3d8c89b5529fd3ee0bccb46cf6c24e46b8dcdb5988c702e1e1b29b78ecc` | 2,810 |
| `app/data.py` | `3c48f14413cafb311b0fcc301d6a60c353cabad4b5c0090d9b728ac3a3b40780` | 21,150 |
| `app/exceptions.py` | `dc73b23ba992db487acb4c58515d5c2d4e17ee427baabb8d081a76b01e9011ea` | 1,577 |
| `app/main.py` | `f73feb9da6880b0ec4a72021b5a94abbc414954eb07c97ca93304d87a453190f` | 11,938 |
| `app/models.py` | `80518289e37efb3c63a23e0d0642c73a0baa8f6930903c7c6d722a6c27328a10` | 2,587 |
| `app/multitoken.py` | `36c838222d7eac5904b5bdec68d4a125e451688719ed15d51d229a70c4643710` | 9,770 |
| `app/normalizer.py` | `56161522c2eca58d8aba51866178cc1adba73c47f33c5b406e68493ccde822cc` | 10,387 |
| `app/phonetic.py` | `f95fd4f91949a9ef8c86d7107a18078612e142df64eba5652f3ea8f0cf441576` | 3,858 |
| `benchmark/__init__.py` | `88c693f811b1ebd395c5e83204fe3af3d7e809061b67a182d11b9ffde00a3d7e` | 172 |
| `benchmark/comparison.py` | `f5b7e91748d28db0c414052f113b1b76fdf66621af41cfe0d395bb36e5e9eee4` | 10,266 |
| `benchmark/generate_adversarial.py` | `26d785dfbe21cb378ec297e5f1f3cfe8c56f61b5036edbc4823cb1cd4db297ff` | 7,798 |
| `benchmark/gold_standard.jsonl` | `cb22b8ba7da589e5180b5585bfe700341cf41925b2f0841cbec787ef4070a6ed` | 37,130 |
| `benchmark/gold_standard_adversarial.jsonl` | `74b65dd407b0729d0e386b381fc6a71780387aa06bb683c6536df1f7aeb99126` | 65,058 |
| `benchmark/heldout.jsonl` | `beb561e5d27417aec8566ed7f92ff081d9fd2bde1ce619e51103ff910d19c6ae` | 21,975 |
| `benchmark/latency.py` | `0f87f0a0e776628b866ef6337e019a1d2e49baf1249c92966d88a3ac76e3a5e2` | 5,417 |
| `benchmark/render_charts.py` | `4cafc7507f4f9f9086d1a991cb9146d183716f1d291ab54d92e017cdc2bcecd0` | 5,146 |
| `benchmark/results.md` | `2efeda501f2a24f5883e15cffd6c3c1702b762b095d18778f5256d8dc7af2493` | 5,345 |
| `benchmark/run_benchmark.py` | `8b6d5983cc5f587d9b5556071e812afa2b087ca7f32c3210deca6cad99c57f5d` | 11,552 |
| `client/__init__.py` | `6e675d1a9782cb978e0458c178c9bc36a905c7029d99b81054b37caa42aabe1a` | 788 |
| `client/normalizer_client.py` | `9fafa530c373588ceac009a7803c9a8ca8516ba48fc9fa87fd6932443e26dd48` | 5,585 |
| `docs/architecture.png` | `3dceb217013cc543252396c00d453ee86de8f2269fa07eef7d3c2164c9c0deec` | 193,933 |
| `docs/architecture.svg` | `cb7dcdbbe3806a5639d8542e0dcb52ff07e1828197dcd04c125a109712181ae2` | 7,680 |
| `docs/benchmark_by_category.png` | `bb268cb72e4cb33242f43b57c71eb83d5c651ad436777b15091cf94c10bf7351` | 271,635 |
| `docs/benchmark_vs_baselines.png` | `b7bffce5c0713b2824efa08c3d9f8279943e4eb3435a21ff0f922c612b3c0363` | 48,265 |
| `docs/corpus.md` | `d4dfc7f682b99963e16679e829deea7a885f3b1bcd76906e65f9017ad1c39814` | 8,185 |
| `docs/demo-screenshot.png` | `8637be7c814ec087594da6ae0ce0ff9baaa9a99aefac2916196ac0b6625a9a55` | 161,075 |
| `docs/demo-screenshot.svg` | `2b56f6cf37c31c4afd84baa22354a7a50919d7e21e1bb5886337eb9f43abdd07` | 7,292 |
| `docs/deployment.md` | `d56e0f04b22e88c5c1342e23ef457317d833e3ad17c52599946b3cbcfa8be3d6` | 7,495 |
| `docs/downstream.md` | `ead4f5fd3e0113fe329ad29d54ed8dd5c8b9926d9335c14901adae98fb5e6633` | 6,824 |
| `docs/limitations.md` | `a063793aae531ead94c201282e5db9a887ce939b86ea402a7b0031403e5ba871` | 7,817 |
| `examples/README.md` | `f094e6c9ac778f65da4459839d574b1179150c054d59f6ed6d80ca628f1de7cb` | 1,389 |
| `examples/minimal_example.py` | `6ddaee7f6c68cbfa848d0bc6b7fd7b1aa129015577d9dbe40a9ea4167612c1ac` | 1,121 |
| `examples/normalize_csv.py` | `17154bedf3d025ea36d5566452f5c2c4a425fe4c9b47268b1e42ca1db7c970bf` | 3,231 |
| `examples/normalize_whatsapp.py` | `bb021d1518897ca38509f5d8769fb710c84411056b9a7055ff6d301da310c5ba` | 3,427 |
| `examples/search_recall_demo.py` | `01f33f7e248c7e5530c12e38d31ae2323a3905ece8dc31f3ecb75213ab432520` | 5,542 |
| `pyproject.toml` | `61b0dca001ea5ad4e5b949077c041d91fae11e5322b41594fbcb3020577a38fc` | 1,843 |
| `render.yaml` | `92953bba00e30571a630478045ea6bf55c4e587f359d65871698afd6e970ea3f` | 1,378 |
| `requirements-dev.txt` | `f6435de409791690e08780d48b85bc65029f46a4bf453685665cb87d6e2fab2a` | 421 |
| `requirements.txt` | `1afbb079464ee2765cea1e4f99fa8b8a5e945425275ca8c974c578ebfa7df446` | 60 |
| `run.sh` | `da2fb7ba9873cee88a1238077ee25b299c6fe01a320d03b95ba6d2a7d6ae7b70` | 532 |
| `scripts/__init__.py` | `760327dfd1583157688952d59a4ce3a22f1d5410b9c8bc8a49ace83260f30e6a` | 200 |
| `scripts/review_unknowns.py` | `060e760839209c1fdd4425879ac3f190d8d583889b42d309b6ebd03471f39bdf` | 10,021 |
| `static/index.html` | `abaf601cb0cc200e31719245ea457b8d86490d8e1375f567dfb0e23298eb6069` | 19,990 |
| `tests/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | 0 |
| `tests/test_adversarial.py` | `2a5e47cfe4baee64f98ea2ba284d187cdf4124a1b962a8b37e392ee370314245` | 9,893 |
| `tests/test_api.py` | `aaf6120e44365d7d688b9f963bd70feb187755f280a734873c84a098e9285130` | 3,799 |
| `tests/test_client.py` | `6674edcbed112fca4b0c8cc9c74ee7d7e39d857ec5a0cf55e7a1874b54239fa7` | 4,783 |
| `tests/test_data.py` | `7f761a1d4bde64cc473a08f46b6b70a34125ccbf79f99c67b14f03887ef8481e` | 3,959 |
| `tests/test_multitoken.py` | `3537372b1996c625c425dc3cc922ac6d31ac9f686a2a3ad949a72adc005df657` | 7,451 |
| `tests/test_normalizer.py` | `2236448f2b8c67e6e05b99e56b5a1f0a82c9315b4f7dba94c0e1a95229903196` | 5,858 |
| `tests/test_phonetic.py` | `a3867edc502308ecab0577008b9370ce37201e14bc598ed80294b8a48f75d73b` | 4,274 |
| `tests/test_regressions.py` | `1e2edf499de8aa13b16c8355625ed667a26250b423120091802a8fd976cfd9a0` | 4,913 |
