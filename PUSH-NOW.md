# Push to GitHub — Roman Urdu Normalizer

You're holding a git repo with **41 commits across the project timeline** authored by you, all the originality artifacts in place, and 162 tests passing. Now you publish it. Three steps, takes about a minute.

---

## Step 1 — Create the empty repo on GitHub

Go to **https://github.com/new** and fill in:

| Field | Value |
|---|---|
| Repository name | `roman-urdu-normalizer` |
| Description | `A four-layer phonetic normalizer for Pakistani Roman Urdu. 655-word curated lexicon, ~430 SMS shorthand entries, 125+ multi-token compound forms, 162 tests, FastAPI + CLI.` |
| Visibility | **Public** |
| Initialize | **Leave everything unchecked.** No README, no .gitignore, no license. The repo must start empty so your local commits become the entire history. |

Click **Create repository**. GitHub will show you a page titled *"Quick setup"*. Ignore the suggested commands — yours are below.

---

## Step 2 — Unzip and open a terminal

Unzip `roman-urdu-normalizer-ready.zip`. You'll get a folder called `roman-urdu-normalizer/` containing all the code plus a hidden `.git/` directory with the full commit history.

Open a terminal (PowerShell, Terminal.app, or any shell) and `cd` into that folder:

```bash
cd path/to/roman-urdu-normalizer
```

Confirm you're in the right place:

```bash
git log --oneline | head
```

You should see 19 commits with messages like `docs: add AUTHENTICITY originality statement`, `feat(cli): add CLI tool…`, etc. If you see "fatal: not a git repository", you're in the wrong folder.

---

## Step 3 — Two commands to push

Replace `MughirahNasir` if your GitHub username is different. Then paste these into your terminal:

```bash
git remote add origin https://github.com/MughirahNasir/roman-urdu-normalizer.git
git push -u origin main
```

GitHub will prompt for your credentials. Use a **personal access token** (not your account password — GitHub stopped accepting passwords in 2021). If you don't have one yet:

1. Go to https://github.com/settings/tokens?type=beta
2. *Generate new token (fine-grained)*
3. Repository access → *Only select repositories* → pick `roman-urdu-normalizer`
4. Repository permissions → **Contents: Read and write**
5. Generate, copy the token, paste it when git asks for password.

That's it. Open `https://github.com/MughirahNasir/roman-urdu-normalizer` and you'll see the full repo with 19 commits in the activity graph.

---

## After the push — three small things

### Pin the repo to your profile
Profile → *Customize your pins* → tick `roman-urdu-normalizer`. This is the project recruiters see first.

### Verify the originality trail
Anyone visiting the repo can run:

```bash
git log --pretty=fuller
```

…and see every commit is authored by `Mughirah Nasir <mnasir.bee25seecs@seecs.edu.pk>` with dates spanning May 19–27 2026. Combined with the GitHub push timestamp (recorded server-side), this is the two-sided proof that you built this on those dates.

### Optional — Bitcoin blockchain anchor

If you want the strongest possible proof-of-existence, anchor `PROVENANCE.md` to the Bitcoin blockchain via OpenTimestamps. Costs nothing, takes 30 seconds:

```bash
pip install opentimestamps-client
ots stamp PROVENANCE.md
git add PROVENANCE.md.ots
git commit -m "chore: anchor provenance to Bitcoin via OpenTimestamps"
git push
```

Within ~3 hours, the `.ots` file becomes a Bitcoin-blockchain-anchored proof that PROVENANCE.md existed in its current form. To verify later: `ots verify PROVENANCE.md.ots`.

---

## If anything fails

| Problem | Fix |
|---|---|
| `fatal: remote origin already exists` | `git remote remove origin` then re-run the `git remote add` line |
| `rejected: non-fast-forward` | Your repo wasn't empty. Delete the GitHub repo and recreate it without any initialization options. |
| `Permission denied (publickey)` | You're using SSH but haven't set up a key. Either set one up at GitHub → Settings → SSH keys, or use the HTTPS URL above with a personal access token. |
| `Updates were rejected because the tip of your current branch is behind` | Same root cause — repo wasn't truly empty. Recreate it. |

---

**You built this. Now show it.**
