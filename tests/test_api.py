"""Tests for the FastAPI HTTP surface.

Uses fastapi.testclient.TestClient — no real network, no real server boot.
Confirms that:
  - endpoints return the expected status codes
  - request validation works (Pydantic)
  - exception handlers turn our exceptions into proper JSON responses
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:

    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["lexicon_size"] > 100  # we have a real dictionary
        assert data["variant_map_size"] > 100


class TestStatsEndpoint:

    def test_stats_endpoint_returns_categories(self):
        resp = client.get("/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "by_category" in data
        assert "pronouns" in data["by_category"]
        assert "verbs_infinitive" in data["by_category"]
        assert data["homograph_groups"] >= 6


class TestNormalizeEndpoint:

    def test_normalize_basic(self):
        resp = client.post("/normalize", json={"text": "yr bht kya"})
        assert resp.status_code == 200
        data = resp.json()
        assert "yaar" in data["normalized"]
        assert "bahut" in data["normalized"]

    def test_normalize_returns_tokens(self):
        resp = client.post("/normalize", json={"text": "bht"})
        data = resp.json()
        assert len(data["tokens"]) == 1
        assert data["tokens"][0]["source"] == "variant_map"

    def test_normalize_empty_string_rejected(self):
        # min_length=1 in the Pydantic model
        resp = client.post("/normalize", json={"text": ""})
        assert resp.status_code == 422  # validation error

    def test_normalize_missing_field(self):
        resp = client.post("/normalize", json={})
        assert resp.status_code == 422

    def test_normalize_oversized_text(self):
        # max_length=5000
        resp = client.post("/normalize", json={"text": "a" * 5001})
        assert resp.status_code == 422


class TestBatchEndpoint:

    def test_batch_basic(self):
        resp = client.post("/normalize/batch", json={"texts": ["yr", "bht", "nhi"]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 3
        assert len(data["results"]) == 3

    def test_batch_empty_list_rejected(self):
        # min_length=1 in the Pydantic model
        resp = client.post("/normalize/batch", json={"texts": []})
        assert resp.status_code == 422

    def test_batch_oversized_rejected_by_pydantic(self):
        # Pydantic max_length=100 should catch this BEFORE it hits our code
        oversized = ["a"] * 101
        resp = client.post("/normalize/batch", json={"texts": oversized})
        assert resp.status_code == 422

    def test_batch_preserves_order(self):
        inputs = ["bht", "nhi", "kya"]
        resp = client.post("/normalize/batch", json={"texts": inputs})
        data = resp.json()
        assert data["results"][0]["input"] == "bht"
        assert data["results"][1]["input"] == "nhi"
        assert data["results"][2]["input"] == "kya"


class TestMetricsEndpoint:

    def test_metrics_open_when_no_token_configured(self):
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "tokens_processed" in data
        assert "top_unknown_tokens" in data

    def test_metrics_requires_token_when_configured(self, monkeypatch):
        import app.main as main_module
        monkeypatch.setattr(main_module, "METRICS_TOKEN", "s3cret")
        assert client.get("/metrics").status_code == 401
        bad = client.get("/metrics", headers={"Authorization": "Bearer wrong"})
        assert bad.status_code == 401
        ok = client.get("/metrics", headers={"Authorization": "Bearer s3cret"})
        assert ok.status_code == 200


class TestUnboundedStateGuards:
    """The in-memory telemetry and rate tracker must stay bounded — an
    attacker sending novel tokens or rotating IPs must not grow process
    memory forever."""

    def test_unknown_token_counter_is_bounded(self):
        from collections import Counter

        from app.main import _bounded_increment
        counter: Counter = Counter()
        cap = 50
        for i in range(cap * 4):
            _bounded_increment(counter, f"junk{i}", cap=cap)
        assert len(counter) <= cap

    def test_bounded_increment_keeps_frequent_tokens(self):
        from collections import Counter

        from app.main import _bounded_increment
        counter: Counter = Counter()
        cap = 50
        for _ in range(100):
            _bounded_increment(counter, "hot-token", cap=cap)
        for i in range(cap * 2):
            _bounded_increment(counter, f"junk{i}", cap=cap)
        assert "hot-token" in counter
        assert counter["hot-token"] >= 100

    def test_rate_window_prunes_stale_ips(self):
        import time

        from app.main import _prune_rate_window, _rate_window
        _rate_window.clear()
        now = time.time()
        _rate_window["stale-ip"] = [now - 120.0]
        _rate_window["fresh-ip"] = [now - 1.0]
        _prune_rate_window(now)
        assert "stale-ip" not in _rate_window
        assert "fresh-ip" in _rate_window
        _rate_window.clear()

    def test_chunked_post_without_content_length_rejected(self):
        # A chunked body has no Content-Length, which would bypass the body
        # size guard entirely, so the API refuses it.
        def gen():
            yield b'{"text": "bht"}'

        resp = client.post("/normalize", content=gen(),
                           headers={"Content-Type": "application/json"})
        assert resp.status_code == 411
        assert resp.json()["error"] == "length_required"


class TestOpenAPISchema:
    """The auto-generated OpenAPI schema is itself a deliverable."""

    def test_openapi_schema_available(self):
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "/normalize" in schema["paths"]
        assert "/normalize/batch" in schema["paths"]
        assert "/health" in schema["paths"]
        assert "/stats" in schema["paths"]

    def test_docs_page_accessible(self):
        resp = client.get("/docs")
        assert resp.status_code == 200
