"""
Example: normalize messages from a WhatsApp chat export.

WhatsApp's "Export chat" feature produces a text file in this format:
    [DD/MM/YYYY, HH:MM:SS] Sender Name: message text
    [DD/MM/YYYY, HH:MM:SS] Sender Name: another message

This script parses it, normalizes each message body, and writes a JSONL
file with structured records. Perfect input for downstream analysis,
classification, sentiment work, or feeding to an LLM.

Run:
    python examples/normalize_whatsapp.py chat.txt --output chat.jsonl

Output is one JSON object per line:
    {"timestamp": "2025-01-12 14:23:08", "sender": "Ali", "original": "yr kya ho rha h", "normalized": "yaar kya ho raha hai"}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client import RomanUrduNormalizerClient


# WhatsApp export line format. Tolerant of common variants.
LINE_RE = re.compile(
    r"^\[?(?P<date>\d{1,2}/\d{1,2}/\d{2,4})[, ]+(?P<time>\d{1,2}:\d{2}(?::\d{2})?)\]?\s*"
    r"[-]?\s*(?P<sender>[^:]+):\s*(?P<message>.+)$"
)


def parse_whatsapp_export(path: Path) -> list[dict]:
    records: list[dict] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            m = LINE_RE.match(line)
            if not m:
                # Continuation of previous message (multi-line)
                if records:
                    records[-1]["original"] += "\n" + line
                continue
            records.append({
                "date":      m.group("date"),
                "time":      m.group("time"),
                "sender":    m.group("sender").strip(),
                "original":  m.group("message").strip(),
            })
    return records


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="normalize_whatsapp",
        description="Normalize a WhatsApp chat export into structured JSONL.",
    )
    parser.add_argument("input", help="path to WhatsApp chat export .txt")
    parser.add_argument("--output", default=None,
                        help="output JSONL path (default: <input>.jsonl)")
    parser.add_argument("--api", default="http://localhost:8000")
    args = parser.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        print(f"error: {in_path} not found", file=sys.stderr)
        return 1
    out_path = Path(args.output) if args.output else in_path.with_suffix(".jsonl")

    records = parse_whatsapp_export(in_path)
    print(f"parsed {len(records)} messages from {in_path}")
    if not records:
        return 0

    client = RomanUrduNormalizerClient(args.api)
    texts = [r["original"] for r in records]
    results = client.normalize_chunks(texts)

    with open(out_path, "w", encoding="utf-8") as fh:
        for rec, result in zip(records, results):
            rec["normalized"] = result["normalized"]
            rec["stats"] = result["stats"]
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    changed = sum(1 for r, res in zip(records, results)
                  if r["original"] != res["normalized"])
    print(f"wrote {out_path}")
    print(f"{changed}/{len(records)} messages changed at least one token")
    return 0


if __name__ == "__main__":
    sys.exit(main())
