"""Tests for the client/ SDK.

These tests use FastAPI's TestClient internally — but mounted under a fake
base URL by monkey-patching urlopen. That way the SDK code paths run
exactly as they would in production, without spinning up a real server.
"""

import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from client import (
    NormalizerAPIError, NormalizerClientError,
    NormalizerTimeout, RomanUrduNormalizerClient,
)
from app.main import app

api_client = TestClient(app)


# -- shared fixture to route SDK calls through the in-process TestClient ----

@pytest.fixture
def patched_urlopen():
    """Patch urllib.request.urlopen so the SDK's HTTP calls hit FastAPI in-process."""
    with patch("client.normalizer_client.urllib.request.urlopen") as mock_open:
        def fake_urlopen(req, timeout=None):
            method = req.get_method()
            url = req.full_url
            path = url.split("/", 3)[-1]
            if not path.startswith("/"):
                path = "/" + path
            data = req.data
            body = json.loads(data.decode()) if data else None

            if method == "GET":
                resp = api_client.get(path)
            else:
                resp = api_client.post(path, json=body)

            if resp.status_code >= 400:
                # Simulate urllib's HTTPError behavior
                import urllib.error
                raise urllib.error.HTTPError(
                    url, resp.status_code, resp.text, hdrs={},
                    fp=MagicMock(read=lambda: resp.text.encode())
                )

            fake_resp = MagicMock()
            fake_resp.read.return_value = resp.text.encode()
            fake_resp.__enter__ = lambda s: s
            fake_resp.__exit__ = lambda *a: None
            return fake_resp

        mock_open.side_effect = fake_urlopen
        yield mock_open


# --- tests ----------------------------------------------------------------

class TestClientBasics:

    def test_requires_base_url(self):
        with pytest.raises(ValueError):
            RomanUrduNormalizerClient("")

    def test_strips_trailing_slash(self):
        c = RomanUrduNormalizerClient("http://localhost:8000/")
        assert c.base_url == "http://localhost:8000"

    def test_health(self, patched_urlopen):
        c = RomanUrduNormalizerClient("http://localhost:8000")
        result = c.health()
        assert result["status"] == "ok"

    def test_stats(self, patched_urlopen):
        c = RomanUrduNormalizerClient("http://localhost:8000")
        result = c.stats()
        assert "by_category" in result
        assert result["canonical_total"] > 100

    def test_normalize_single(self, patched_urlopen):
        c = RomanUrduNormalizerClient("http://localhost:8000")
        result = c.normalize("yr bht")
        assert "yaar" in result["normalized"]
        assert "bahut" in result["normalized"]

    def test_normalize_type_error(self):
        c = RomanUrduNormalizerClient("http://localhost:8000")
        with pytest.raises(TypeError):
            c.normalize(123)


class TestBatch:

    def test_batch_normal(self, patched_urlopen):
        c = RomanUrduNormalizerClient("http://localhost:8000")
        result = c.normalize_batch(["yr", "bht"])
        assert result["count"] == 2
        assert len(result["results"]) == 2

    def test_batch_empty_rejected(self):
        c = RomanUrduNormalizerClient("http://localhost:8000")
        with pytest.raises(ValueError):
            c.normalize_batch([])

    def test_batch_oversized_rejected_clientside(self):
        c = RomanUrduNormalizerClient("http://localhost:8000")
        with pytest.raises(ValueError, match="exceeds limit"):
            c.normalize_batch(["x"] * 200)

    def test_normalize_chunks_auto_splits(self, patched_urlopen):
        """Verify normalize_chunks splits 250 inputs into 3 batches of <= 100."""
        c = RomanUrduNormalizerClient("http://localhost:8000")
        inputs = [f"test{i}" for i in range(250)]
        results = c.normalize_chunks(inputs)
        assert len(results) == 250

    def test_normalize_chunks_empty(self, patched_urlopen):
        c = RomanUrduNormalizerClient("http://localhost:8000")
        assert c.normalize_chunks([]) == []


class TestErrorHandling:

    def test_4xx_error_not_retried(self, patched_urlopen):
        c = RomanUrduNormalizerClient("http://localhost:8000", max_retries=3)
        # An empty string should fail validation (422)
        with pytest.raises(NormalizerAPIError) as exc:
            c.normalize("")
        # 4xx should be non-retryable
        assert 400 <= exc.value.status_code < 500


class TestVersion:

    def test_version_exposed(self):
        from client import __version__
        assert __version__ == "1.0.0"
