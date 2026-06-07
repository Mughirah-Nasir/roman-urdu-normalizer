# Deployment Guide

How to run this in production. Covers Render, Fly.io, and Docker Compose.

The defaults in `app/main.py` are production-safe:

- **CORS** is locked down to `localhost` unless you explicitly open it via `ALLOWED_ORIGINS`.
- **Request size** is capped at 1 MB unless you raise `MAX_REQUEST_BYTES`.
- **Rate limiting** is disabled by default (set `RATE_LIMIT_PER_MIN` to enable).

You can verify any deployment's runtime config by hitting `GET /metrics` and inspecting the `config` field.

---

## Environment variables

| Variable | Default | What it does |
|---|---|---|
| `ALLOWED_ORIGINS` | `http://localhost:8000,http://127.0.0.1:8000` | Comma-separated CORS allowlist. Use `*` only for open public demos. |
| `MAX_REQUEST_BYTES` | `1048576` (1 MB) | Max body size for POST requests. Returns HTTP 413 if exceeded. |
| `RATE_LIMIT_PER_MIN` | `0` (disabled) | Max requests per minute per IP. Returns HTTP 429 if exceeded. |

Set these in your platform's environment-variable UI (Render dashboard, Fly secrets, Docker Compose `environment:` block).

---

## Option 1 — Render.com (recommended for portfolio demos)

Render is the easiest free-tier option for showing a live URL to recruiters.

1. **Sign in** to https://render.com with your GitHub account.
2. Click **New +** → **Web Service**.
3. Pick your `roman-urdu-normalizer` repo.
4. Use these settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
5. Under **Environment Variables**, set:
   - `ALLOWED_ORIGINS=https://yourappname.onrender.com` (so the frontend can call its own backend)
   - `RATE_LIMIT_PER_MIN=60` (modest protection on a public demo)
6. Click **Create Web Service**.

Render builds the image, deploys, and gives you a public URL like `https://roman-urdu-normalizer.onrender.com`. First request after idle takes ~30 seconds (cold start on free tier); subsequent requests are fast.

---

## Option 2 — Fly.io (better cold-start performance)

Fly's free tier has slower cold starts but you can configure machine sizing.

1. Install `flyctl`: https://fly.io/docs/hands-on/install-flyctl/
2. From the repo root:
   ```bash
   flyctl auth login
   flyctl launch --no-deploy
   ```
   When prompted: app name = `roman-urdu-normalizer-yourname`, region = closest to you.
3. Edit `fly.toml` to set environment variables:
   ```toml
   [env]
     ALLOWED_ORIGINS = "https://roman-urdu-normalizer-yourname.fly.dev"
     RATE_LIMIT_PER_MIN = "60"
     MAX_REQUEST_BYTES = "1048576"
   ```
4. Deploy:
   ```bash
   flyctl deploy
   ```

The included `Dockerfile` is what Fly will use. The container exposes port 8000, runs as a non-root user, and includes a `HEALTHCHECK` instruction.

---

## Option 3 — Docker Compose (self-hosted)

If you have a VPS or homelab, this is the cleanest setup. Save as `docker-compose.yml`:

```yaml
version: "3.9"
services:
  normalizer:
    build: .
    image: roman-urdu-normalizer:latest
    container_name: roman-urdu-normalizer
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      ALLOWED_ORIGINS: "https://your-domain.com"
      MAX_REQUEST_BYTES: "1048576"
      RATE_LIMIT_PER_MIN: "120"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
    # Optional resource limits
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: "0.5"
```

Bring it up:

```bash
docker compose up -d
docker compose logs -f normalizer        # tail logs
```

Put nginx, Caddy, or Cloudflare in front for TLS and you're done.

---

## Reverse-proxy notes (nginx example)

If you're terminating TLS at nginx and proxying to the FastAPI process:

```nginx
location /api/normalize/ {
    # Forward client IP so our rate limiter sees real source addresses
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Real-IP $remote_addr;

    # Cap the upload size at the proxy too — defense in depth
    client_max_body_size 1m;

    proxy_pass http://127.0.0.1:8000/;
}
```

**Important:** the current rate-limiter keys on `request.client.host`, which is the *immediate* client. If you're behind a proxy, you need to either:

1. Configure the proxy to pass `X-Forwarded-For` (above), and
2. Run uvicorn with `--proxy-headers --forwarded-allow-ips="*"` so FastAPI honors the forwarded IP.

Without this, every request will appear to come from `127.0.0.1` and the rate limit will be ineffective.

---

## Observability

The included `/metrics` endpoint returns:

- `tokens_processed` — total tokens since process start
- `request_counts` — per-endpoint counters
- `top_unknown_tokens` — the 20 most-frequent unresolved tokens from live traffic
- `top_ambiguous_tokens` — top 10 ambiguous tokens (homograph hits)
- `lexicon_size`, `variant_map_size` — current dictionary sizes
- `config` — the env-var-driven config (so you can verify what's actually loaded)

**Privacy warning:** `top_unknown_tokens` contains raw user-typed text. If you're processing user-generated content, this list could include PII or sensitive strings. Either restrict access to `/metrics` (auth in front of the proxy), or modify `app/main.py` to hash or aggregate the unknown-token counter before exposure.

**Suggested scraping pattern:** if you have Prometheus or similar, pull `/metrics` every 30 seconds and graph `tokens_processed` and `request_counts`. Run a periodic batch job that pulls `top_unknown_tokens`, reviews them, and adds legitimate Roman Urdu shortenings to `app/data.py::VARIANT_MAP`.

---

## Production checklist

Before pointing real users at it:

- [ ] Set `ALLOWED_ORIGINS` to your actual frontend domain(s). Don't leave `*` unless this is an open demo.
- [ ] Set `RATE_LIMIT_PER_MIN` to something reasonable for your traffic (60–300 is sane for a demo).
- [ ] Decide on `MAX_REQUEST_BYTES`. Default 1 MB is plenty for typical chat/SMS use. Raise for bulk processing.
- [ ] Put TLS in front (Cloudflare, nginx, Caddy, or your platform's auto-TLS).
- [ ] Set up a healthcheck against `/health` (every platform supports this).
- [ ] Decide whether `/metrics` is publicly readable or auth-gated.
- [ ] Pin the Python version and dependency versions in your image (the included `Dockerfile` already does this — uses `python:3.12-slim` and the pinned `requirements.txt`).
- [ ] Set up log aggregation (the app emits one structured log line per request to stdout).

---

## Scaling notes

- The normalizer is **CPU-bound stateless lookup**. Add uvicorn workers (`--workers 4`) to use multiple cores. No locking or shared state to worry about.
- The lexicon is loaded once at process start (~10 ms) and resides in memory. Each worker holds its own copy (~2 MB), so 4 workers = ~8 MB total. Negligible.
- The in-memory `/metrics` telemetry is **per-worker**. With multiple workers, each `/metrics` request hits one worker at random and reports that worker's view. For accurate aggregation, run a single worker or push counters to a shared backend (Redis, statsd).
- The rate limiter is also **per-process**. Multi-worker deployments effectively multiply the limit by `N` workers. Acceptable for demos; not acceptable for strict per-user quota enforcement.

---

**Need help?** Open an issue at https://github.com/Mughirah-Nasir/roman-urdu-normalizer/issues.
