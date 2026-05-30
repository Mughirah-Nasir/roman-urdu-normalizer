"""
Minimal example — calling the Roman Urdu Normalizer from Python.

Run the API first:
    python -m uvicorn app.main:app

Then:
    python examples/minimal_example.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client import RomanUrduNormalizerClient


def main():
    client = RomanUrduNormalizerClient("http://localhost:8000")

    # Confirm the API is up
    health = client.health()
    print(f"API status: {health['status']}, lexicon size: {health['lexicon_size']}")

    # Single sentence
    result = client.normalize("yr bht thora kch kya kr rhe ho")
    print()
    print(f"Input:      {result['input']}")
    print(f"Normalized: {result['normalized']}")
    print(f"Stats:      {result['stats']}")

    # Batch
    print()
    print("--- Batch ---")
    batch = client.normalize_batch([
        "kese ho yr",
        "abhi a rha hun",
        "bht thora khaya",
    ])
    for r in batch["results"]:
        print(f"  {r['input']!r:<35} -> {r['normalized']!r}")


if __name__ == "__main__":
    main()
