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

import hmac
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

# Upper bound on distinct client IPs tracked by the rate limiter. Stale IPs
# are pruned once this is reached, so the tracker cannot grow without bound.
MAX_TRACKED_IPS = int(os.getenv("MAX_TRACKED_IPS", "10000"))

# Upper bound on distinct tokens kept per telemetry counter. Without a cap,
# an attacker sending novel tokens grows the unknown-token Counter forever.
TELEMETRY_MAX_TOKENS = int(os.getenv("TELEMETRY_MAX_TOKENS", "5000"))

# Optional bearer token for /metrics. When set, the endpoint (which exposes
# fragments of user input) requires "Authorization: Bearer <token>".
METRICS_TOKEN = os.getenv("METRICS_TOKEN", "")


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


def _bounded_increment(counter: Counter, key: str,
                       cap: int | None = None) -> None:
    """Increment counter[key], keeping the counter's size bounded.

    When the counter exceeds the cap, it is compacted to the most frequent
    half — cheap, and it preserves exactly the signal /metrics reports
    (top-N tokens). Rare junk from a flood of novel tokens is dropped.
    """
    cap = TELEMETRY_MAX_TOKENS if cap is None else cap
    counter[key] += 1
    if cap > 0 and len(counter) > cap:
        kept = counter.most_common(max(cap // 2, 1))
        counter.clear()
        counter.update(dict(kept))


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


def _prune_rate_window(now: float) -> None:
    """Evict IPs with no request in the last 60s so the tracker cannot
    accumulate one timestamp list per unique client IP forever."""
    cutoff = now - 60.0
    stale = [ip for ip, ts in _rate_window.items() if not ts or ts[-1] <= cutoff]
    for ip in stale:
        del _rate_window[ip]


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
        # A chunked body carries no Content-Length, which would bypass the
        # size guard entirely. This JSON API has no legitimate need for
        # chunked uploads, so require a declared length instead.
        te = request.headers.get("transfer-encoding", "")
        if cl is None and "chunked" in te.lower():
            return JSONResponse(
                status_code=411,
                content={"error": "length_required",
                         "detail": "chunked transfer encoding is not supported; "
                                   "send a Content-Length header"},
            )

    # Rate limit
    if RATE_LIMIT_PER_MIN > 0:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        if client_ip not in _rate_window and len(_rate_window) >= MAX_TRACKED_IPS:
            _prune_rate_window(now)
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
            _bounded_increment(TELEMETRY["unknown_tokens"], tok["original"].lower())  # type: ignore[arg-type]
        if tok["ambiguous"]:
            _bounded_increment(TELEMETRY["ambiguous_tokens"], tok["original"].lower())  # type: ignore[arg-type]


@app.get("/metrics", tags=["meta"])
def metrics(request: Request):
    """Operational telemetry: total tokens processed, per-endpoint request
    counts, and the top unresolved tokens — useful for lexicon growth.

    The top-unknown list contains raw fragments of user input, so when the
    METRICS_TOKEN env var is set, callers must send a matching
    "Authorization: Bearer <token>" header."""
    if METRICS_TOKEN:
        auth = request.headers.get("authorization", "")
        expected = f"Bearer {METRICS_TOKEN}"
        if not hmac.compare_digest(auth.encode(), expected.encode()):
            raise HTTPException(
                status_code=401,
                detail="metrics endpoint requires a valid bearer token",
            )
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
