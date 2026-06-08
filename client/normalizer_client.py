"""
HTTP client for the Roman Urdu Normalizer API.

Zero third-party dependencies — uses only the Python standard library.
This is intentional: making the client easier to vendor than to depend on.
If you want async or HTTP/2, swap in httpx with a thin wrapper.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from collections.abc import Iterable
from typing import Any

DEFAULT_TIMEOUT = 5.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE = 0.25
MAX_BATCH_SIZE = 100


# --- exceptions -----------------------------------------------------------

class NormalizerClientError(Exception):
    """Base class for any error raised by this client."""


class NormalizerAPIError(NormalizerClientError):
    """API returned a non-2xx response."""

    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body
        super().__init__(f"API returned {status_code}: {body[:200]}")


class NormalizerTimeout(NormalizerClientError):
    """Request exceeded the timeout."""


# --- the client -----------------------------------------------------------

class RomanUrduNormalizerClient:
    """Synchronous HTTP client.

    Example:
        client = RomanUrduNormalizerClient("http://localhost:8000")
        result = client.normalize("yr bht thora kya")
        # -> {"input": "...", "normalized": "yaar bahut thora kya", ...}
    """

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        user_agent: str = "roman-urdu-normalizer-client/1.0",
    ):
        if not base_url:
            raise ValueError("base_url is required")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.user_agent = user_agent

    # --- public API ------------------------------------------------------

    def health(self) -> dict[str, Any]:
        """GET /health — confirm the API is up and the data layer loaded."""
        return self._request("GET", "/health")

    def stats(self) -> dict[str, Any]:
        """GET /stats — dictionary stats per part-of-speech category."""
        return self._request("GET", "/stats")

    def normalize(self, text: str) -> dict[str, Any]:
        """POST /normalize — single-string normalization."""
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}")
        return self._request("POST", "/normalize", body={"text": text})

    def normalize_batch(self, texts: Iterable[str]) -> dict[str, Any]:
        """POST /normalize/batch — up to 100 strings at once."""
        texts = list(texts)
        if not texts:
            raise ValueError("texts cannot be empty")
        if len(texts) > MAX_BATCH_SIZE:
            raise ValueError(
                f"batch size {len(texts)} exceeds limit {MAX_BATCH_SIZE}; "
                "use normalize_chunks() to auto-split"
            )
        return self._request("POST", "/normalize/batch", body={"texts": texts})

    def normalize_chunks(self, texts: Iterable[str]) -> list[dict[str, Any]]:
        """Like normalize_batch, but auto-splits inputs over MAX_BATCH_SIZE
        across multiple requests and returns the flat results list."""
        texts = list(texts)
        if not texts:
            return []
        all_results: list[dict[str, Any]] = []
        for i in range(0, len(texts), MAX_BATCH_SIZE):
            chunk = texts[i : i + MAX_BATCH_SIZE]
            resp = self.normalize_batch(chunk)
            all_results.extend(resp["results"])
        return all_results

    # --- internals -------------------------------------------------------

    def _request(self, method: str, path: str, body: dict | None = None) -> dict[str, Any]:
        url = self.base_url + path
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }
        if data is not None:
            headers["Content-Type"] = "application/json"

        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method=method)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    payload = resp.read().decode("utf-8")
                    return json.loads(payload)

            except urllib.error.HTTPError as e:
                err_body = e.read().decode("utf-8", errors="replace")
                # 4xx is not retryable
                if 400 <= e.code < 500:
                    raise NormalizerAPIError(e.code, err_body) from e
                last_exc = NormalizerAPIError(e.code, err_body)

            except urllib.error.URLError as e:
                if "timed out" in str(getattr(e, "reason", "")).lower():
                    last_exc = NormalizerTimeout(str(e))
                else:
                    last_exc = NormalizerClientError(str(e))

            except TimeoutError as e:
                last_exc = NormalizerTimeout(str(e))

            # Backoff before retrying (exponential)
            if attempt < self.max_retries - 1:
                time.sleep(self.backoff_base * (2 ** attempt))

        assert last_exc is not None
        raise last_exc
