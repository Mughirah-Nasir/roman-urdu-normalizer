"""
Generate adversarial perturbations of the hand-curated gold-standard.

Takes the 250 hand-curated examples and produces 250 more by applying
realistic real-world ugliness:

    - emoji insertion       (e.g. "kya scene 😂 hai")
    - vowel repetition      (e.g. "yaarrrr" -> stretched)
    - punctuation excess    (e.g. "kya??!!")
    - hashtag suffix        (e.g. "kya scene hai #karachi")
    - casing chaos          (e.g. "KyA tUm Aa rHe Ho")
    - whitespace stress     (multiple spaces, leading/trailing)

The methodology — base + perturbations — is how real NLP eval datasets
are built (CheckList, HANS, etc). It exposes systematic weaknesses
without requiring 5x more hand-curation.

Crucially: the *expected output* is also perturbed in lockstep, so the
score is whether the normalizer survives the noise, not whether it
normalizes away noise it shouldn't touch.

Author: Mughirah Nasir, 2026.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path


EMOJIS = ["😂", "🤣", "😭", "❤️", "🔥", "👀", "🙏", "🥲", "😎", "🤔", "💯", "🎉"]
HASHTAGS = ["#karachi", "#lahore", "#islamabad", "#pakistan", "#desi", "#urdu",
            "#PSL", "#WhatsApp", "#chai", "#student", "#NUST", "#monsoon"]


def perturb_emoji(input_text: str, expected: str, rng: random.Random) -> tuple[str, str]:
    """Insert 1-2 emojis at random positions in both input and expected."""
    if not input_text.strip():
        return input_text, expected
    n_emoji = rng.choice([1, 1, 2])  # mostly 1, sometimes 2
    emojis = rng.sample(EMOJIS, n_emoji)
    where = rng.choice(["start", "end", "middle"])
    if where == "start":
        prefix = " ".join(emojis) + " "
        return prefix + input_text, prefix + expected
    elif where == "end":
        suffix = " " + " ".join(emojis)
        return input_text + suffix, expected + suffix
    else:
        # Insert at first whitespace boundary
        e_str = " " + " ".join(emojis) + " "
        # Replace first space if exists, else append
        if " " in input_text:
            mid_input = input_text.replace(" ", e_str, 1)
            mid_exp = expected.replace(" ", e_str, 1)
            return mid_input, mid_exp
        return input_text + e_str, expected + e_str


def perturb_vowel_repeat(input_text: str, expected: str, rng: random.Random) -> tuple[str, str]:
    """Pick a vowel in the input and repeat it 2-4 times — common SMS stretch.
    The expected output gets the same stretch since the normalizer should
    pass repeated vowels through unchanged (collapsing them is incorrect:
    "yaarrr" still means "yaar" but stretching is a stylistic choice)."""
    if not input_text.strip():
        return input_text, expected
    vowels = re.findall(r'[aeiouAEIOU]', input_text)
    if not vowels:
        return input_text, expected
    target_vowel = rng.choice(vowels)
    repeat = target_vowel * rng.choice([2, 3, 4])
    # Replace the first occurrence
    new_input = input_text.replace(target_vowel, repeat, 1)
    new_expected = expected.replace(target_vowel, repeat, 1) if target_vowel in expected else expected
    return new_input, new_expected


def perturb_punctuation_excess(input_text: str, expected: str, rng: random.Random) -> tuple[str, str]:
    """Add 2-5 ?, !, or both at the end."""
    if not input_text.strip():
        return input_text, expected
    n = rng.choice([2, 3, 4, 5])
    punct = rng.choice(["?", "!", "?!", "!!", "..."])
    addition = punct * n if len(punct) == 1 else punct + ("!" * (n - 1))
    return input_text + addition, expected + addition


def perturb_hashtag(input_text: str, expected: str, rng: random.Random) -> tuple[str, str]:
    """Append 1-2 hashtags."""
    if not input_text.strip():
        return input_text, expected
    n = rng.choice([1, 1, 2])
    tags = rng.sample(HASHTAGS, n)
    suffix = " " + " ".join(tags)
    return input_text + suffix, expected + suffix


def perturb_casing_chaos(input_text: str, expected: str, rng: random.Random) -> tuple[str, str]:
    """Randomize the case of each letter, preserving non-letters."""
    if not input_text.strip():
        return input_text, expected
    def chaos(s: str) -> str:
        return "".join(c.upper() if rng.random() < 0.5 else c.lower() for c in s)
    # Important caveat: the normalizer lowercases internally, so the expected
    # output keeps original casing structure. We score F1 case-insensitively.
    return chaos(input_text), expected


def perturb_whitespace(input_text: str, expected: str, rng: random.Random) -> tuple[str, str]:
    """Double-up spaces randomly, occasionally lead/trail with whitespace."""
    if not input_text.strip():
        return input_text, expected
    # Inject double-spaces
    parts = input_text.split(" ")
    new_input = "  ".join(parts) if rng.random() < 0.5 else " ".join(parts)
    # Add leading/trailing whitespace sometimes
    if rng.random() < 0.4:
        new_input = " " + new_input
    if rng.random() < 0.4:
        new_input = new_input + " "
    # Expected: collapse multi-spaces to single (normalizer should handle this)
    return new_input, expected


PERTURBATIONS = [
    ("emoji_insert",     perturb_emoji),
    ("vowel_repeat",     perturb_vowel_repeat),
    ("punct_excess",     perturb_punctuation_excess),
    ("hashtag_suffix",   perturb_hashtag),
    ("casing_chaos",     perturb_casing_chaos),
    ("whitespace_stress", perturb_whitespace),
]


def generate_perturbations(
    base_records: list[dict],
    out_path: Path,
    seed: int = 0xBEE,
    n_per_base: int = 1,
) -> int:
    rng = random.Random(seed)
    written = 0
    with open(out_path, "w", encoding="utf-8") as fh:
        for base in base_records:
            # Skip edge cases where perturbation makes no sense
            if base["category"].startswith("edge_") and base["category"] != "edge_unknown":
                continue
            for _ in range(n_per_base):
                pert_name, pert_fn = rng.choice(PERTURBATIONS)
                new_input, new_expected = pert_fn(base["input"], base["expected"], rng)
                rec = {
                    "id":       f"{base['id']}_pert_{pert_name}",
                    "category": f"{base['category']}__{pert_name}",
                    "input":    new_input,
                    "expected": new_expected,
                    "notes":    f"adversarial perturbation of {base['id']}: {pert_name}",
                    "base_id":  base["id"],
                    "perturbation": pert_name,
                }
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                written += 1
    return written


def main() -> int:
    parser = argparse.ArgumentParser(prog="generate_adversarial")
    parser.add_argument("--input",  default="benchmark/gold_standard.jsonl",
                        help="path to base hand-curated dataset")
    parser.add_argument("--output", default="benchmark/gold_standard_adversarial.jsonl",
                        help="output path for perturbations")
    parser.add_argument("--seed",   type=int, default=0xBEE)
    parser.add_argument("--n",      type=int, default=1,
                        help="number of perturbations per base example")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    base = []
    with open(in_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            base.append(json.loads(line))

    n = generate_perturbations(base, out_path, args.seed, args.n)
    print(f"generated {n} perturbations from {len(base)} base examples → {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
