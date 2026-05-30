# Examples

End-to-end usage scripts. Each one is self-contained and uses the Python client SDK from `client/`.

| Script | What it does |
| --- | --- |
| `minimal_example.py` | Smallest possible program that calls the API |
| `normalize_csv.py` | Normalize a Roman Urdu column in a CSV file |
| `normalize_whatsapp.py` | Parse a WhatsApp chat export and emit cleaned JSONL |

Before running any of these, start the API:

```bash
python -m uvicorn app.main:app --reload
```

Then in another terminal, run any example. All scripts default to `http://localhost:8000` but accept `--api` to point at a different deployment.

## Example: WhatsApp export pipeline

Useful real-world flow:

```bash
# 1. Export a chat from WhatsApp ("More" → "Export chat" → "Without media")
# 2. Send yourself the .txt file
# 3. Process it:
python examples/normalize_whatsapp.py WhatsApp\ Chat\ with\ Friends.txt --output friends.jsonl

# 4. Each line is a structured record:
head -1 friends.jsonl
# {"date": "12/05/26", "time": "14:23", "sender": "Ali", "original": "yr kya scene h", "normalized": "yaar kya scene hai", "stats": {...}}
```

## Example: CSV pipeline

```bash
# 1. Have a CSV with a Roman Urdu column, e.g. customer survey responses
# 2. Run:
python examples/normalize_csv.py survey.csv --column response --output survey_clean.csv

# 3. The output has an extra response_normalized column
```
