"""
Latency benchmark for the Roman Urdu Normalizer.

Measures end-to-end normalization latency by running the normalizer on a
realistic mix of Pakistani Roman Urdu inputs and reporting percentile
latencies plus throughput.

Usage:
    python -m benchmark.latency
    python -m benchmark.latency --iterations 100000
    python -m benchmark.latency --json > latency_results.json

Notes:
    - We run in-process (not through HTTP) because we want to measure the
      normalizer's actual cost, not network + framework overhead.
    - Inputs come from the gold-standard dataset, sampled with replacement
      to amortize variance across the input distribution.
    - Warmup runs are excluded to avoid measuring import + cache misses.
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
import time
from pathlib import Path

from app.normalizer import normalize_text


def _load_inputs() -> list[str]:
    """Load realistic inputs from the gold-standard dataset."""
    path = Path(__file__).parent / "gold_standard.jsonl"
    inputs: list[str] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec["input"]:  # skip empty
                inputs.append(rec["input"])
    return inputs


def measure(iterations: int = 10_000, warmup: int = 1_000) -> dict[str, float]:
    inputs = _load_inputs()
    if not inputs:
        raise RuntimeError("gold-standard inputs are empty")

    rng = random.Random(0xBEE)
    sample = [rng.choice(inputs) for _ in range(iterations + warmup)]

    # Warmup
    for s in sample[:warmup]:
        normalize_text(s)

    # Measure — per-call timing via perf_counter_ns for sub-microsecond precision
    timings_ns: list[int] = []
    overall_start = time.perf_counter()
    for s in sample[warmup:]:
        t0 = time.perf_counter_ns()
        normalize_text(s)
        timings_ns.append(time.perf_counter_ns() - t0)
    overall_elapsed = time.perf_counter() - overall_start

    timings_us = sorted(t / 1000.0 for t in timings_ns)

    def pct(p: float) -> float:
        if not timings_us:
            return 0.0
        idx = max(0, min(len(timings_us) - 1, int(round((p / 100.0) * (len(timings_us) - 1)))))
        return timings_us[idx]

    return {
        "iterations": iterations,
        "warmup": warmup,
        "wallclock_seconds": round(overall_elapsed, 4),
        "throughput_per_sec": round(iterations / overall_elapsed, 1),
        "latency_us_min":    round(timings_us[0], 2),
        "latency_us_p50":    round(pct(50), 2),
        "latency_us_p95":    round(pct(95), 2),
        "latency_us_p99":    round(pct(99), 2),
        "latency_us_max":    round(timings_us[-1], 2),
        "latency_us_mean":   round(statistics.fmean(timings_us), 2),
        "latency_us_stdev":  round(statistics.stdev(timings_us) if len(timings_us) > 1 else 0.0, 2),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="latency_benchmark")
    parser.add_argument("--iterations", type=int, default=10_000)
    parser.add_argument("--warmup", type=int, default=1_000)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    result = measure(args.iterations, args.warmup)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    print()
    print("┌─────────────────────────────────────────────────────────────┐")
    print("│        ROMAN URDU NORMALIZER — LATENCY BENCHMARK            │")
    print("├─────────────────────────────────────────────────────────────┤")
    print(f"│ Iterations:              {result['iterations']:<35d}│")
    print(f"│ Warmup runs:             {result['warmup']:<35d}│")
    print(f"│ Wallclock seconds:       {result['wallclock_seconds']:<35.4f}│")
    print(f"│ Throughput (calls/sec):  {result['throughput_per_sec']:<35,.1f}│")
    print("├─────────────────────────────────────────────────────────────┤")
    print(f"│ Min latency:             {result['latency_us_min']:>10.2f} µs                  │")
    print(f"│ p50 (median):            {result['latency_us_p50']:>10.2f} µs                  │")
    print(f"│ p95:                     {result['latency_us_p95']:>10.2f} µs                  │")
    print(f"│ p99:                     {result['latency_us_p99']:>10.2f} µs                  │")
    print(f"│ Max latency:             {result['latency_us_max']:>10.2f} µs                  │")
    print(f"│ Mean ± stdev:            {result['latency_us_mean']:>10.2f} ± {result['latency_us_stdev']:.2f} µs           │")
    print("└─────────────────────────────────────────────────────────────┘")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
