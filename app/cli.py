"""
Command-line interface for the Roman Urdu Normalizer.

Use cases:
  - quick one-off normalization without booting the FastAPI server
  - batch processing from a shell pipeline (cat file.txt | python -m app.cli)
  - dictionary diagnostics (--stats)

Examples:
  $ echo "yr bht thora kya"  | python -m app.cli
  yaar bahut thora kya

  $ python -m app.cli "kese ho?"
  kaise ho?

  $ python -m app.cli --json "yr bht thora"
  {"input": "yr bht thora", "normalized": "yaar bahut thora", ...}

  $ python -m app.cli --stats
  Variant map entries: 344
  Canonical total:     655
  ...
"""

import argparse
import json
import sys

from app.console import ensure_utf8_stdout
from app.data import lexicon_stats
from app.normalizer import normalize_text


def _print_stats() -> None:
    """Pretty-print lexicon stats to stdout."""
    s = lexicon_stats()
    print("=== Roman Urdu Normalizer — lexicon stats ===")
    print(f"Variant map entries:           {s['variant_map_entries']:>6}")
    print(f"Canonical lexicon total:       {s['canonical_total']:>6}")
    print(f"Total recognized spellings:    {s['total_recognized_spellings']:>6}")
    print(f"Homograph groups:              {s['homograph_groups']:>6}")
    print()
    print("--- By category ---")
    for cat, n in sorted(s["by_category"].items(), key=lambda x: -x[1]):
        print(f"  {cat:30s} {n:>5}")


def _normalize_lines(lines, as_json: bool) -> None:
    """Normalize a list of lines, print results."""
    for line in lines:
        line = line.rstrip("\n")
        if not line:
            print()
            continue
        result = normalize_text(line)
        if as_json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            print(result["normalized"])


def main() -> int:
    ensure_utf8_stdout()  # pass-through emoji/Nastaliq crashes cp1252 consoles
    parser = argparse.ArgumentParser(
        prog="roman-urdu-normalizer",
        description="Normalize Roman Urdu text from the command line.",
    )
    parser.add_argument(
        "text", nargs="?",
        help="text to normalize. If omitted, reads from stdin (one line per record).",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="emit full JSON output (input, normalized, tokens, stats) per line.",
    )
    parser.add_argument(
        "--stats", action="store_true",
        help="print dictionary statistics and exit.",
    )

    args = parser.parse_args()

    if args.stats:
        _print_stats()
        return 0

    if args.text is not None:
        _normalize_lines([args.text], as_json=args.json)
        return 0

    # No positional arg — read from stdin
    if sys.stdin.isatty():
        # interactive terminal with no input piped — show help
        parser.print_help()
        return 1

    _normalize_lines(sys.stdin, as_json=args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
