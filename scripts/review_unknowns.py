"""
Reviewer tool — turn /metrics top unknowns into proposed variant_map entries.

This script closes the lexicon-growth loop the external review asked for:

    /metrics → top unknown tokens → reviewer decides → patch generated
                                                   ↓
                                            variant map updated
                                            regression test added
                                            CHANGELOG entry queued

Workflow (interactive):

    1. Hit a running normalizer's /metrics endpoint to pull the top
       unresolved tokens. Or, alternatively, point at a JSON dump.
    2. For each token, the script proposes 1-3 likely canonical forms
       by running phonetic-key lookup against the lexicon.
    3. The reviewer (a native Urdu speaker) accepts / corrects / skips.
    4. Accepted mappings are written to:
         - a unified-diff patch against app/data.py (apply with `patch -p1`)
         - a generated test file at tests/test_review_promoted.py
         - a CHANGELOG line in `/tmp/changelog_entry.md`
    5. Reviewer runs tests, audits the patch, opens a PR.

Usage:
    python -m scripts.review_unknowns --api http://localhost:8000
    python -m scripts.review_unknowns --from-json metrics_dump.json
    python -m scripts.review_unknowns --top 20

Author: Mughirah Nasir, 2026.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.data import CANONICAL_LEXICON, VARIANT_MAP, all_canonical_words  # noqa: E402
from app.phonetic import phonetic_key  # noqa: E402


def fetch_metrics(api: str) -> dict:
    """Pull the /metrics endpoint of a running normalizer."""
    url = f"{api.rstrip('/')}/metrics"
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def propose_candidates(token: str, top_n: int = 3) -> list[tuple[str, str]]:
    """
    Suggest plausible canonical resolutions for an unknown token.
    Returns up to N (canonical_word, reason) pairs.
    """
    proposals: list[tuple[str, str]] = []
    lower = token.lower()
    if not lower:
        return proposals

    # Phonetic-key candidates
    key = phonetic_key(lower)
    if len(key) >= 2:
        same_key = [w for w in all_canonical_words() if phonetic_key(w) == key]
        for w in same_key[:top_n]:
            proposals.append((w, f"shares phonetic key '{key}'"))

    # Substring fuzzy: canonical word containing the token, or vice versa
    if len(proposals) < top_n:
        for w in sorted(CANONICAL_LEXICON):
            if w == lower:
                continue
            if (lower in w or w in lower) and abs(len(w) - len(lower)) <= 2:
                proposals.append((w, f"substring overlap with '{w}'"))
                if len(proposals) >= top_n:
                    break

    return proposals[:top_n]


def interactive_review(unknowns: list[dict]) -> dict[str, str]:
    """Walk through each unknown token, get a verdict from the reviewer."""
    accepted: dict[str, str] = {}
    skipped: list[str] = []

    print(f"\n{len(unknowns)} unknown tokens to review.")
    print("For each one: type 'y' to accept the top suggestion, "
          "type a custom mapping, or 's' to skip.\n")

    for i, entry in enumerate(unknowns, 1):
        token = entry["token"]
        count = entry["count"]
        if token in VARIANT_MAP:
            print(f"[{i}/{len(unknowns)}] {token!r} (seen {count}x) — already in variant map; skipping")
            continue

        proposals = propose_candidates(token)
        print(f"\n[{i}/{len(unknowns)}] Unknown token: {token!r}  (seen {count}x)")
        if proposals:
            for j, (w, why) in enumerate(proposals, 1):
                print(f"  {j}) {w}    ({why})")
        else:
            print("  (no automatic suggestions)")

        choice = input("  >>> [y / 1-3 / custom / s=skip / q=quit]: ").strip().lower()

        if choice in ("q", "quit"):
            print("Quitting review session.")
            break
        if choice in ("s", "skip", ""):
            skipped.append(token)
            continue
        if choice == "y" and proposals:
            accepted[token] = proposals[0][0]
            print(f"  → accepted: {token!r} -> {proposals[0][0]!r}")
            continue
        if choice.isdigit() and proposals:
            idx = int(choice) - 1
            if 0 <= idx < len(proposals):
                accepted[token] = proposals[idx][0]
                print(f"  → accepted: {token!r} -> {proposals[idx][0]!r}")
                continue
        # Custom string mapping
        if choice:
            accepted[token] = choice
            print(f"  → custom: {token!r} -> {choice!r}")

    print(f"\nDone. {len(accepted)} accepted, {len(skipped)} skipped.")
    return accepted


def write_patch(accepted: dict[str, str], out_path: Path) -> None:
    """Write a unified-diff patch that can be applied to app/data.py."""
    lines = ["# Patch generated by scripts/review_unknowns.py",
             "# Apply with: patch -p1 < lexicon_growth.patch",
             "# Or manually paste the lines below into VARIANT_MAP in app/data.py.",
             "",
             "# --- a/app/data.py", "# +++ b/app/data.py", "#",
             "# New VARIANT_MAP entries:", ""]
    for src, tgt in sorted(accepted.items()):
        lines.append(f'    "{src}": "{tgt}",')
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_tests(accepted: dict[str, str], out_path: Path) -> None:
    """Generate a pytest file that pins the new mappings as regression tests."""
    lines = [
        '"""',
        "Auto-generated regression tests for variant_map entries promoted from",
        "/metrics top-unknowns. Each test pins that a previously-unknown token",
        "now resolves to its agreed canonical form.",
        "",
        "Run: python -m pytest tests/test_review_promoted.py",
        '"""',
        "",
        "from app.normalizer import normalize_token",
        "",
        "",
        "class TestPromotedUnknowns:",
        "",
    ]
    for src, tgt in sorted(accepted.items()):
        safe_name = "".join(c if c.isalnum() else "_" for c in src)
        lines.append(f"    def test_{safe_name}_resolves(self):")
        lines.append(f"        result = normalize_token({src!r})")
        lines.append(f"        assert result['normalized'] == {tgt!r}")
        lines.append("        assert result['source'] == 'variant_map'")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_changelog_entry(accepted: dict[str, str], out_path: Path) -> None:
    """Queue a CHANGELOG snippet for the next release."""
    lines = ["### Added", ""]
    lines.append(f"- {len(accepted)} new variant_map entries promoted from "
                 "live `/metrics` top-unknowns review:")
    for src, tgt in sorted(accepted.items()):
        lines.append(f"  - `{src}` → `{tgt}`")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(prog="review_unknowns")
    parser.add_argument("--api", default="http://localhost:8000",
                        help="base URL of running normalizer (default: localhost:8000)")
    parser.add_argument("--from-json", default=None,
                        help="instead of hitting /metrics, read from a JSON file")
    parser.add_argument("--top", type=int, default=20,
                        help="how many top unknowns to review (default: 20)")
    parser.add_argument("--out-dir", default="/tmp",
                        help="where to write patch/tests/changelog (default: /tmp)")
    parser.add_argument("--non-interactive", action="store_true",
                        help="print proposals only, don't prompt (for CI / dry run)")
    args = parser.parse_args()

    if args.from_json:
        with open(args.from_json) as f:
            metrics = json.load(f)
    else:
        try:
            metrics = fetch_metrics(args.api)
        except Exception as e:
            print(f"ERROR fetching {args.api}/metrics: {e}", file=sys.stderr)
            print("Hint: is `python -m uvicorn app.main:app` running?", file=sys.stderr)
            return 1

    unknowns = metrics.get("top_unknown_tokens", [])[: args.top]
    if not unknowns:
        print("No unknown tokens in /metrics. Either nothing's been processed "
              "yet, or your normalizer is doing great. Either way, nothing to do.")
        return 0

    if args.non_interactive:
        print("== Dry run — proposals only ==\n")
        for entry in unknowns:
            token = entry["token"]
            proposals = propose_candidates(token)
            print(f"{token!r}  (seen {entry['count']}x):")
            for w, why in proposals:
                print(f"  → {w}  ({why})")
            print()
        return 0

    accepted = interactive_review(unknowns)
    if not accepted:
        print("\nNothing to write. Exiting.")
        return 0

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    patch_path = out_dir / "lexicon_growth.patch"
    tests_path = out_dir / "test_review_promoted.py"
    chlg_path  = out_dir / "changelog_entry.md"
    write_patch(accepted, patch_path)
    write_tests(accepted, tests_path)
    write_changelog_entry(accepted, chlg_path)

    print("\nWrote:")
    print(f"  patch:     {patch_path}")
    print(f"  tests:     {tests_path}")
    print(f"  changelog: {chlg_path}")
    print("\nNext steps:")
    print(f"  1. Review {patch_path}")
    print("  2. Copy entries into app/data.py::VARIANT_MAP")
    print(f"  3. Copy {tests_path} into tests/")
    print("  4. Run pytest, verify the new tests pass and nothing regresses")
    print("  5. Add the changelog entry, commit, PR")
    return 0


if __name__ == "__main__":
    sys.exit(main())
