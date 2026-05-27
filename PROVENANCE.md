# PROVENANCE

**Project:** Roman Urdu Normalizer  
**Author:** Mughirah Nasir (mnasir.bee25seecs@seecs.edu.pk)  
**Institution:** NUST SEECS, Islamabad, Pakistan  
**GitHub:** https://github.com/MughirahNasir  
**Build window:** 2026-05-19 → 2026-05-27  
**Manifest generated:** 2026-05-27

---

## Project fingerprint

```
7cf0517f6114f927fa43f3ec1cd11ef07a2c6dd91d80434715dbb207999cf095
```

This is the SHA-256 hash of the file manifest below. It uniquely
identifies the exact contents of this project at the moment
PROVENANCE.md was generated. Any change to any tracked file
(even a single character) produces a completely different fingerprint.

## Authenticity guarantees

1. **Git history**: 19 atomic commits spanning 9 days (May 19–27, 2026),
   all authored by `Mughirah Nasir <mnasir.bee25seecs@seecs.edu.pk>`.
   Run `git log --pretty=fuller` after cloning to see author/committer
   identity and timestamps on every commit.

2. **GitHub push timestamp**: Once pushed, GitHub records the exact
   push moment server-side. Combined with the in-commit timestamps,
   this forms a two-sided time anchor.

3. **Optional Bitcoin blockchain anchor**: This file can be stamped
   using OpenTimestamps to anchor its hash to the Bitcoin blockchain,
   giving you a tamper-evident proof that the file existed at a
   specific moment, independent of GitHub:

   ```bash
   pip install opentimestamps-client
   ots stamp PROVENANCE.md
   # commit PROVENANCE.md.ots and push it
   ```

## Verification commands

After cloning the repo, anyone can verify the manifest:

```bash
git log --pretty=fuller          # see all commits with author identity
git log --shortstat              # see file-change history
sha256sum -c manifest.sha256     # verify every file hash
```

## File manifest

Total files tracked: **32**

| SHA-256 | Path | Size |
|---|---|---|
| `e41ebd5a01d7f610070bf633b8dae26069646856bfff41e5c8af5255390ef6d9` | `.dockerignore` | 286 B |
| `a984815af9ae06689d40363a72ae982ca678a3dc161881ba920cff31b55eb981` | `.github/workflows/tests.yml` | 1,203 B |
| `48975eabd20eff79719334398bd4cbd6ef7aad6b3fbc0121bc82eb5920b02f16` | `.gitignore` | 277 B |
| `192ea8853e58d6fa740ee2b3b73e23eed5d58f2c0cc670d7c053fc8a403b424c` | `AUTHENTICITY.md` | 7,352 B |
| `e09df840a220cef6ac68fd521d191267bcb4bb7dbc9ececcb5234ed5b4af3632` | `CHANGELOG.md` | 2,928 B |
| `5ec21ad14ce5c2e555e3512b8526f8ea9b84c317dd2e424053327a5b13f33857` | `CONTRIBUTING.md` | 3,062 B |
| `2e2d716e819bcccb3103e369c86acdb07b1b7c1b4689ff72ae7c04345be4d24d` | `Dockerfile` | 1,918 B |
| `4a96b2c3829c1aa7eea3dace01c2f953153e81c084021196f3340cad5ffb45e2` | `LICENSE` | 1,071 B |
| `333dc81544bd0c6c51f397f5c2422f1e425364ba10745a7e051d5d850feb3fb6` | `README.md` | 10,924 B |
| `e0ab57f3decbdcedad4505e836eb555501e9c9d09ae1c12252cbd0fa4e348ec4` | `app/__init__.py` | 85 B |
| `4d85e3d8c89b5529fd3ee0bccb46cf6c24e46b8dcdb5988c702e1e1b29b78ecc` | `app/cli.py` | 2,810 B |
| `3fc53fdf201159fc3857097f46550dc5e15bff1c46bed565c4091b3733fc54af` | `app/data.py` | 19,640 B |
| `dc73b23ba992db487acb4c58515d5c2d4e17ee427baabb8d081a76b01e9011ea` | `app/exceptions.py` | 1,577 B |
| `d9db532a6e49da60eb97e03c42113882f93452a61aa755ddf1c5389a3a0a6ac5` | `app/main.py` | 7,055 B |
| `b70064a22c1d1f67594d25e94a04f6aeef9d5470911d7a8266d2568e490abbf6` | `app/models.py` | 1,792 B |
| `dab5da828e6889ca3f496d76a9e0b8100a9b48d052ff157ff19ba9bd2093d55c` | `app/normalizer.py` | 7,377 B |
| `bf9e2b099b9347d1d9820cee53deeaf61b3af464951f7f94d47420099e2a9fb7` | `app/phonetic.py` | 3,832 B |
| `28205ad96f372eb422b12d1f50916d1e6585eb2c5b86895d78ad205710528a0a` | `docs/architecture.png` | 77,549 B |
| `0f8d414b9923d5086102dcae7b99ac02462ffd266fbe54cc16286ff1634af07e` | `docs/architecture.svg` | 6,193 B |
| `017715ea87b04a42cc51b28121bf166943a301bd23f56e8d356d13cb011a2120` | `docs/demo-screenshot.png` | 105,154 B |
| `c1b911e1f01a62dc5439873317cc13bfe01127806b3fb5790309cfa9dd0bf224` | `docs/demo-screenshot.svg` | 7,292 B |
| `7bcbc6ea9e0359963d201fed3bc7481852cabffbae177d77b11b18c77d240926` | `pyproject.toml` | 1,795 B |
| `e55bfa8b56a1a4fdf051dacfe3c86b249ba584b2c4a051e21bf953d7831640db` | `requirements-dev.txt` | 178 B |
| `1afbb079464ee2765cea1e4f99fa8b8a5e945425275ca8c974c578ebfa7df446` | `requirements.txt` | 60 B |
| `be5387ff8334e6cdccab28411c344f1d9ccc25914b387244129e0c700942e113` | `run.sh` | 532 B |
| `13c340ed0fe59f9edda6485e94bdc1b7bed3e17ca939e4b487483a38f0f6faad` | `static/index.html` | 19,989 B |
| `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` | `tests/__init__.py` | 0 B |
| `aaf6120e44365d7d688b9f963bd70feb187755f280a734873c84a098e9285130` | `tests/test_api.py` | 3,799 B |
| `b156f756ee7b474848f09920c3e8755cc442a6716a92103dc08ac7b0fea73085` | `tests/test_data.py` | 3,943 B |
| `f9bc81f7a4a5b18e6ee76d7dfba19ffab7c46ff1a7611e77b71c7ba36a100373` | `tests/test_normalizer.py` | 5,470 B |
| `e3fa2fda98f07ee864e54b06543344c93f9d9e40c9703ee0cc54ee3fba3d7a45` | `tests/test_phonetic.py` | 4,274 B |
| `4728f5dee745b57be2b5bb67f62987091f908e050c1bc3f60478d56053729a62` | `tests/test_regressions.py` | 4,707 B |

## Raw sha256sum format

(copy this block into a `manifest.sha256` file and run `sha256sum -c` to verify)

```
e41ebd5a01d7f610070bf633b8dae26069646856bfff41e5c8af5255390ef6d9  .dockerignore
a984815af9ae06689d40363a72ae982ca678a3dc161881ba920cff31b55eb981  .github/workflows/tests.yml
48975eabd20eff79719334398bd4cbd6ef7aad6b3fbc0121bc82eb5920b02f16  .gitignore
192ea8853e58d6fa740ee2b3b73e23eed5d58f2c0cc670d7c053fc8a403b424c  AUTHENTICITY.md
e09df840a220cef6ac68fd521d191267bcb4bb7dbc9ececcb5234ed5b4af3632  CHANGELOG.md
5ec21ad14ce5c2e555e3512b8526f8ea9b84c317dd2e424053327a5b13f33857  CONTRIBUTING.md
2e2d716e819bcccb3103e369c86acdb07b1b7c1b4689ff72ae7c04345be4d24d  Dockerfile
4a96b2c3829c1aa7eea3dace01c2f953153e81c084021196f3340cad5ffb45e2  LICENSE
333dc81544bd0c6c51f397f5c2422f1e425364ba10745a7e051d5d850feb3fb6  README.md
e0ab57f3decbdcedad4505e836eb555501e9c9d09ae1c12252cbd0fa4e348ec4  app/__init__.py
4d85e3d8c89b5529fd3ee0bccb46cf6c24e46b8dcdb5988c702e1e1b29b78ecc  app/cli.py
3fc53fdf201159fc3857097f46550dc5e15bff1c46bed565c4091b3733fc54af  app/data.py
dc73b23ba992db487acb4c58515d5c2d4e17ee427baabb8d081a76b01e9011ea  app/exceptions.py
d9db532a6e49da60eb97e03c42113882f93452a61aa755ddf1c5389a3a0a6ac5  app/main.py
b70064a22c1d1f67594d25e94a04f6aeef9d5470911d7a8266d2568e490abbf6  app/models.py
dab5da828e6889ca3f496d76a9e0b8100a9b48d052ff157ff19ba9bd2093d55c  app/normalizer.py
bf9e2b099b9347d1d9820cee53deeaf61b3af464951f7f94d47420099e2a9fb7  app/phonetic.py
28205ad96f372eb422b12d1f50916d1e6585eb2c5b86895d78ad205710528a0a  docs/architecture.png
0f8d414b9923d5086102dcae7b99ac02462ffd266fbe54cc16286ff1634af07e  docs/architecture.svg
017715ea87b04a42cc51b28121bf166943a301bd23f56e8d356d13cb011a2120  docs/demo-screenshot.png
c1b911e1f01a62dc5439873317cc13bfe01127806b3fb5790309cfa9dd0bf224  docs/demo-screenshot.svg
7bcbc6ea9e0359963d201fed3bc7481852cabffbae177d77b11b18c77d240926  pyproject.toml
e55bfa8b56a1a4fdf051dacfe3c86b249ba584b2c4a051e21bf953d7831640db  requirements-dev.txt
1afbb079464ee2765cea1e4f99fa8b8a5e945425275ca8c974c578ebfa7df446  requirements.txt
be5387ff8334e6cdccab28411c344f1d9ccc25914b387244129e0c700942e113  run.sh
13c340ed0fe59f9edda6485e94bdc1b7bed3e17ca939e4b487483a38f0f6faad  static/index.html
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  tests/__init__.py
aaf6120e44365d7d688b9f963bd70feb187755f280a734873c84a098e9285130  tests/test_api.py
b156f756ee7b474848f09920c3e8755cc442a6716a92103dc08ac7b0fea73085  tests/test_data.py
f9bc81f7a4a5b18e6ee76d7dfba19ffab7c46ff1a7611e77b71c7ba36a100373  tests/test_normalizer.py
e3fa2fda98f07ee864e54b06543344c93f9d9e40c9703ee0cc54ee3fba3d7a45  tests/test_phonetic.py
4728f5dee745b57be2b5bb67f62987091f908e050c1bc3f60478d56053729a62  tests/test_regressions.py
```
