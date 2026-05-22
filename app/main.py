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
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.data import VARIANT_MAP, CANONICAL_LEXICON, lexicon_stats
from app.exceptions import (
    BatchSizeError, DictionaryIntegrityError, InvalidInputError, NormalizerError,
)
from app.models import (
    BatchNormalizeRequest, BatchNormalizeResponse, ErrorResponse,
    HealthResponse, LexiconStatsResponse,
    NormalizeRequest, NormalizeResponse,
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
# App
# ----------------------------------------------------------------------------
app = FastAPI(
    title="Roman Urdu Normalizer",
    description=(
        "A three-layer phonetic normalizer for Roman Urdu text. Resolves "
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


# Permissive CORS — this is a demo service. Tighten the origins list before
# running anywhere that handles real user data.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------------
# Request logging middleware
# ----------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """One structured log line per request: method, path, status, ms."""
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
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
    return NormalizeResponse(**normalize_text(req.text))


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
    return BatchNormalizeResponse(
        results=[NormalizeResponse(**r) for r in results],
        count=len(results),
    )
