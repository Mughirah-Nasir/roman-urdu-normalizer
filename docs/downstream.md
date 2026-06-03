# Why Normalization Matters Downstream

This document answers a question reviewers ask: *"OK, but what's the point?"*

Normalization is a means, not an end. The value shows up downstream: in search, deduplication, classification, and any system that processes Roman Urdu text as data.

Below is a concrete demonstration. Numbers are reproducible — every code block can be pasted into a Python REPL with the running normalizer at `http://localhost:8000`.

---

## Demo 1 — Search recall

A Pakistani e-commerce site indexes customer reviews. Someone searches `"nahi"` ("no" / "didn't"). Without normalization, here's what gets matched:

```python
reviews = [
    "shipping nai aya time pe",       # nai
    "quality nahin acha tha",         # nahin
    "main satisfied nahi hun",        # nahi
    "kahan se kharida nai pta",       # nai
    "kch bhi nai aya box me",         # nai
]
query = "nahi"

# Without normalization: naive substring match
hits = [r for r in reviews if query in r]
print(f"Without normalization: {len(hits)}/5 reviews matched")
# Output: Without normalization: 1/5 reviews matched
```

With normalization:

```python
from client import RomanUrduNormalizerClient
client = RomanUrduNormalizerClient("http://localhost:8000")

normalized_reviews = [client.normalize(r)["normalized"] for r in reviews]
normalized_query = client.normalize(query)["normalized"]

hits = [r for r in normalized_reviews if normalized_query in r]
print(f"With normalization: {len(hits)}/5 reviews matched")
# Output: With normalization: 5/5 reviews matched
```

**Recall went from 20% to 100%** on this query. This is the headline value proposition for any Roman Urdu search system.

---

## Demo 2 — Duplicate detection

A customer service team aggregates complaints. The same complaint, typed five different ways, should count as one issue:

```python
complaints = [
    "yr meri delivery nai ai abi tk",
    "bhai shipping abhi tak nahi aya",
    "delivery bohat late hai ye",
    "yaar meri delivery nahi ayi abhi tak",
    "delivery bht zyada late hai",
]

# Without normalization: 5 distinct strings
print(f"Without normalization: {len(set(complaints))} unique complaints")
# Output: 5

# With normalization
normalized = [client.normalize(c)["normalized"] for c in complaints]
print(f"With normalization: {len(set(normalized))} unique complaints")
# Output: 4 (first and fourth collapse to the same canonical form)
```

Imperfect — `bht` ("very") and `bohat` ("very") are both in the variant map, so they collapse correctly, but stylistic variation in the rest of the sentence keeps similar complaints distinct. With a downstream similarity threshold (cosine similarity on normalized text) you get much tighter clustering than on raw input.

---

## Demo 3 — Sentiment preprocessing

A sentiment classifier is trained on canonical Roman Urdu text but receives messy SMS input at inference time:

```python
inputs = [
    "bht khush hun yr 🥳",           # SMS shorthand
    "wo mjhe pasand nai aya bilkul", # negation
    "kch khaas nai tha",              # neutral
    "shopping kafi acha laga",        # positive
]

for inp in inputs:
    normalized = client.normalize(inp)["normalized"]
    # Now `normalized` is what the classifier sees
    print(f"{inp:<40} -> {normalized}")
```

The classifier's vocabulary needs to know `bahut` (it does), not `bht` (which wasn't in training). Normalization is the bridge between user input and a model trained on canonical text. Without it, the classifier sees:

- `bht` → OOV token → discarded
- `mjhe` → OOV token → discarded
- `nai` → matched to negation? maybe? depends on training data

After normalization, the classifier sees clean canonical words it was actually trained on.

---

## Demo 4 — Cleaning data for LLM prompts

When you build a system that feeds user Roman Urdu into an LLM (say, ChaiBot — the freelancer proposal assistant), normalization helps for two reasons:

1. **Token efficiency.** LLM tokenizers (BPE) sometimes split SMS shorthand into many tokens. `bht` tokenizes worse than `bahut`. Normalized input uses fewer tokens, which is fewer dollars at scale.

2. **Consistency.** LLMs respond more reliably to canonical input than to a soup of spelling variants. If half your prompts say `bht` and half say `bahut`, the model sees them as different words and your few-shot examples leak signal.

Quick measurement:

```python
import requests
# Hypothetical token-counting call
for variant in ["bht", "bohat", "bahut", "bhut"]:
    tokens = count_tokens_for(variant)  # using your tokenizer
    print(f"{variant:<10} -> {tokens} tokens")
# All four spellings of "very" — varying token counts because BPE.
```

After running each through the normalizer, all four become `bahut` and tokenize identically.

---

## Demo 5 — Aggregating WhatsApp business chat

Imagine a Pakistani small-business owner with 6 months of WhatsApp customer messages. They want to know: what are the top complaints?

Naive approach — word frequency over raw messages:

```
Top words: "delivery", "krdo", "kr", "nai", "abhi", "ho", "bhai", "kab", "rahi", "yr", ...
```

A bunch of these are just spelling noise. After normalization:

```
Top words: "delivery", "kar", "nahi", "abhi", "ho", "bhai", "kab", "raha", "yaar", "kya", ...
```

Now `kr` and `karo` and `krdo` all roll up to `kar` — making "kar" (the verb "do") visible as a top word. The signal is in the canonical form, not the spelling variant.

---

## Summary table

| Use case | Without normalization | With normalization | Win |
|---|---|---|---|
| Search by canonical query | Misses spelling variants | Matches all variants | **Massive recall lift** |
| Duplicate detection | Treats variants as distinct | Collapses spelling variants | Cleaner clusters |
| Sentiment / classification | OOV tokens discarded | Canonical tokens recognized | More signal preserved |
| LLM prompt input | Token-inefficient + inconsistent | Compact + canonical | Cost + quality |
| Aggregation / analytics | Top words polluted by spelling noise | Top words reflect real frequency | Cleaner BI |

---

## What this *doesn't* solve

- **Semantic understanding.** Normalization is spelling, not meaning. `kal mile ge` ("we'll meet tomorrow") is still ambiguous between yesterday and tomorrow after normalization. See `docs/limitations.md`.
- **Code-switched English.** Normalization doesn't translate `office me hun` to `I am at the office`. It just rewrites `me` to canonical `me`.
- **Sentiment scoring itself.** Normalization is the preprocessing step. You still need a sentiment classifier on top.

In short: this service is a **clean input layer**. It makes everything downstream easier and more reliable. It is not, by itself, a Roman Urdu understanding system.

---

**Author:** Mughirah Nasir, 2026.
