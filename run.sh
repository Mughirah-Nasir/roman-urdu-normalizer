#!/bin/bash
# Roman Urdu Normalizer — convenience run script
set -e

if [ ! -d "venv" ]; then
  echo "→ creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "→ Roman Urdu Normalizer v1.2.0"
echo "→ starting server on http://localhost:8000"
echo "→ demo:        http://localhost:8000"
echo "→ API docs:    http://localhost:8000/docs"
echo "→ stats:       http://localhost:8000/stats"
echo ""

exec python -m uvicorn app.main:app --reload
