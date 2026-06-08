"""
Example: normalize a Roman Urdu column in a CSV file.

Use case: you have customer feedback / survey responses / WhatsApp message
exports as a CSV, and you want to clean up the Roman Urdu column before
running search, classification, or feeding it to an LLM.

Run:
    python examples/normalize_csv.py input.csv --column message --output cleaned.csv

What it does:
    1. Read every row of the CSV
    2. For each row, normalize the `--column` field through the API
    3. Write a new CSV with an additional `<column>_normalized` column

This script uses the Python client SDK (not raw HTTP), so it handles
retries and large inputs automatically.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

# Make the client importable when running from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client import RomanUrduNormalizerClient


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="normalize_csv",
        description="Normalize a Roman Urdu column in a CSV file."
    )
    parser.add_argument("input", help="path to input CSV file")
    parser.add_argument("--column", default="message",
                        help="name of the column to normalize (default: message)")
    parser.add_argument("--output", default=None,
                        help="output CSV path (default: <input>_normalized.csv)")
    parser.add_argument("--api", default="http://localhost:8000",
                        help="base URL of the normalizer API")
    parser.add_argument("--batch", type=int, default=100,
                        help="how many rows to send per request (default: 100)")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"error: {in_path} not found", file=sys.stderr)
        return 1
    out_path = Path(args.output) if args.output else in_path.with_stem(in_path.stem + "_normalized")

    client = RomanUrduNormalizerClient(args.api)

    with open(in_path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if args.column not in reader.fieldnames:
            print(f"error: column {args.column!r} not in CSV "
                  f"(found: {reader.fieldnames})", file=sys.stderr)
            return 1
        rows = list(reader)

    print(f"loaded {len(rows)} rows from {in_path}")

    # Batch through the API in chunks
    texts = [r[args.column] or "" for r in rows]
    results = client.normalize_chunks(texts)

    out_field = f"{args.column}_normalized"
    fieldnames = list(reader.fieldnames) + [out_field]
    with open(out_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row, result in zip(rows, results, strict=False):
            row[out_field] = result["normalized"]
            writer.writerow(row)

    n_changed = sum(1 for r, res in zip(rows, results, strict=False)
                    if r[args.column] != res["normalized"])
    print(f"wrote {out_path}")
    print(f"normalized {n_changed} / {len(rows)} rows changed at least one token")
    return 0


if __name__ == "__main__":
    sys.exit(main())
