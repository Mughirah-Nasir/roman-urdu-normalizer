"""
FastAPI entry point for the Roman Urdu Normalizer.

Endpoints:
    GET  /                      - serves the demo frontend (static/index.html)
    GET  /health                - lightweight readiness probe
    GET  /stats                 - dictionary stats (lexicon sizes per category)
    POST /normalize             - normalize a single string
    POST /normalize/batch       - normalize up to 100 strings in one call
    GET  /docs                  - auto-generated OpenAPI docs
"""

import logging
import os
import time
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.data import CANONICAL_LEXICON, VARIANT_MAP, lexicon_stats
from app.exceptions import (
    BatchSizeError,
    DictionaryIntegrityError,
    InvalidInputError,
    NormalizerError,
)
from app.models import (
    BatchNormalizeRequest,
    BatchNormalizeResponse,
    ErrorResponse,
    HealthResponse,
    LexiconStatsResponse,
    NormalizeRequest,
    NormalizeResponse,
)
from app.normalizer import normalize_batch, normalize_text

# ----------------------------------------------------------------------------
# Logging — single structured log line per request
# ----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)
log = logging.getLogger("roman-urdu-normalizer")


# ----------------------------------------------------------------------------
# Production-hardening config — env-var driven
# ----------------------------------------------------------------------------
def _csv_env(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [s.strip() for s in raw.split(",") if s.strip()]

# CORS — closed by default. Set ALLOWED_ORIGINS="*" in dev only.
ALLOWED_ORIGINS = _csv_env("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")

# Request size limit — 1 MB by default (configurable up to 10 MB)
MAX_REQUEST_BYTES = int(os.getenv("MAX_REQUEST_BYTES", str(1 * 1024 * 1024)))

# Rate limit — requests per minute per IP. 0 disables.
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "0"))


# ----------------------------------------------------------------------------
# In-memory telemetry — top unresolved tokens for lexicon growth
# ----------------------------------------------------------------------------
# In production you'd push this to Prometheus / a tsdb. For a demo we
# keep an in-process Counter that the /metrics endpoint exposes.
TELEMETRY: dict[str, Counter | int] = {
    "request_count":     Counter(),
    "unknown_tokens":    Counter(),
    "ambiguous_tokens":  Counter(),
    "tokens_processed":  0,
}


# ----------------------------------------------------------------------------
# App
# ----------------------------------------------------------------------------
app = FastAPI(
    title="Roman Urdu Normalizer",
    description=(
        "A four-layer phonetic normalizer (phrase + variant + phonetic + unknown) for Roman Urdu text. Resolves "
        "common spelling variants (kya / kia / kyaa) and SMS shorthand "
        "(bht, nhi, kch) to canonical forms. Built by Mughirah Nasir."
    ),
    version=__version__,
    contact={
        "name": "Mughirah Nasir",
        "email": "mnasir.bee25seecs@seecs.edu.pk",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)


# Restricted CORS — origins controlled by ALLOWED_ORIGINS env var.
# Default is localhost only. For an open demo, set ALLOWED_ORIGINS="*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------------
# Request-size limit + simple in-process rate limiter
# ----------------------------------------------------------------------------
# Sliding-window-ish rate tracker keyed by client IP. Reset every minute.
_rate_window: dict[str, list[float]] = {}


@app.middleware("http")
async def hardening_middleware(request: Request, call_next):
    # Body-size guard for POST bodies
    if request.method == "POST":
        cl = request.headers.get("content-length")
        if cl and int(cl) > MAX_REQUEST_BYTES:
            return JSONResponse(
                status_code=413,
                content={"error": "payload_too_large",
                         "detail": f"request body exceeds {MAX_REQUEST_BYTES} bytes"},
            )

    # Rate limit
    if RATE_LIMIT_PER_MIN > 0:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = _rate_window.setdefault(client_ip, [])
        # Drop anything older than 60s
        cutoff = now - 60.0
        window[:] = [t for t in window if t > cutoff]
        if len(window) >= RATE_LIMIT_PER_MIN:
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limit_exceeded",
                         "detail": f"max {RATE_LIMIT_PER_MIN} requests per minute"},
                headers={"Retry-After": "60"},
            )
        window.append(now)

    return await call_next(request)


# ----------------------------------------------------------------------------
# Request logging middleware + telemetry
# ----------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """One structured log line per request: method, path, status, ms."""
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    TELEMETRY["request_count"][request.url.path] += 1  # type: ignore
    log.info(
        "%s %s -> %d (%.1fms)",
        request.method, request.url.path, response.status_code, elapsed_ms,
    )
    return response


# ----------------------------------------------------------------------------
# Exception handlers — turn our exceptions into proper HTTP responses
# ----------------------------------------------------------------------------
@app.exception_handler(BatchSizeError)
async def batch_size_error_handler(request: Request, exc: BatchSizeError):
    return JSONResponse(
        status_code=413,
        content=ErrorResponse(error="batch_size_exceeded", detail=str(exc)).model_dump(),
    )


@app.exception_handler(InvalidInputError)
async def invalid_input_handler(request: Request, exc: InvalidInputError):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(error="invalid_input", detail=str(exc)).model_dump(),
    )


@app.exception_handler(DictionaryIntegrityError)
async def dictionary_integrity_handler(request: Request, exc: DictionaryIntegrityError):
    # 500 — this means the server is internally broken
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(error="dictionary_integrity", detail=str(exc)).model_dump(),
    )


@app.exception_handler(NormalizerError)
async def normalizer_error_handler(request: Request, exc: NormalizerError):
    # Catch-all for anything else raised from the normalizer package
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(error="normalizer_error", detail=str(exc)).model_dump(),
    )


# ----------------------------------------------------------------------------
# Static frontend
# ----------------------------------------------------------------------------
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index():
    """Serve the demo HTML at the root URL."""
    index_path = _STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(404, "Demo page not found. Build the static folder.")
    return FileResponse(index_path)


# ----------------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health():
    """Lightweight readiness check. Returns dictionary sizes so callers can
    confirm the data layer loaded correctly."""
    return HealthResponse(
        status="ok",
        lexicon_size=len(CANONICAL_LEXICON),
        variant_map_size=len(VARIANT_MAP),
    )


@app.get("/stats", response_model=LexiconStatsResponse, tags=["meta"])
def stats():
    """Dictionary statistics — counts per category, homograph groups, etc.
    Useful for debugging and for the demo frontend."""
    return LexiconStatsResponse(**lexicon_stats())


@app.post(
    "/normalize",
    response_model=NormalizeResponse,
    tags=["normalize"],
    responses={400: {"model": ErrorResponse}},
)
def normalize(req: NormalizeRequest):
    """Normalize a single string of Roman Urdu text.

    Returns the rewritten string, per-token resolution records, and summary
    statistics. Tokens that nothing matched are passed through unchanged
    and marked source=\"unknown\" — we never silently guess."""
    result = normalize_text(req.text)
    _record_telemetry(result)
    return NormalizeResponse(**result)


@app.post(
    "/normalize/batch",
    response_model=BatchNormalizeResponse,
    tags=["normalize"],
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
    },
)
def normalize_batch_endpoint(req: BatchNormalizeRequest):
    """Normalize up to 100 strings in one call. Cheaper than 100 round
    trips when you have many short inputs to process."""
    results = normalize_batch(req.texts)
    for r in results:
        _record_telemetry(r)
    return BatchNormalizeResponse(
        results=[NormalizeResponse(**r) for r in results],
        count=len(results),
    )


def _record_telemetry(result: dict) -> None:
    """Update in-memory telemetry counters with token-source info from
    one normalization result. Used to populate /metrics."""
    TELEMETRY["tokens_processed"] += result["stats"]["total"]  # type: ignore
    for tok in result["tokens"]:
        if tok["source"] == "unknown":
            TELEMETRY["unknown_tokens"][tok["original"].lower()] += 1  # type: ignore
        if tok["ambiguous"]:
            TELEMETRY["ambiguous_tokens"][tok["original"].lower()] += 1  # type: ignore


@app.get("/metrics", tags=["meta"])
def metrics():
    """Operational telemetry: total tokens processed, per-endpoint request
    counts, and the top unresolved tokens — useful for lexicon growth."""
    unknown_counter = TELEMETRY["unknown_tokens"]
    ambiguous_counter = TELEMETRY["ambiguous_tokens"]
    request_counter = TELEMETRY["request_count"]
    assert isinstance(unknown_counter, Counter)
    assert isinstance(ambiguous_counter, Counter)
    assert isinstance(request_counter, Counter)
    return {
        "tokens_processed": TELEMETRY["tokens_processed"],
        "request_counts":   dict(request_counter),
        "top_unknown_tokens": [
            {"token": tok, "count": n}
            for tok, n in unknown_counter.most_common(20)
        ],
        "top_ambiguous_tokens": [
            {"token": tok, "count": n}
            for tok, n in ambiguous_counter.most_common(10)
        ],
        "lexicon_size": len(CANONICAL_LEXICON),
        "variant_map_size": len(VARIANT_MAP),
        "config": {
            "allowed_origins":    ALLOWED_ORIGINS,
            "max_request_bytes":  MAX_REQUEST_BYTES,
            "rate_limit_per_min": RATE_LIMIT_PER_MIN,
        },
    }
