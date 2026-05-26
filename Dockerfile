# syntax=docker/dockerfile:1.6

# ============================================================
# Stage 1 — build wheels for our dependencies
# ============================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt


# ============================================================
# Stage 2 — slim runtime
# ============================================================
FROM python:3.12-slim AS runtime

# Create a non-root user — never run a web service as root
ARG USER=normalizer
ARG UID=10001
RUN groupadd --system --gid ${UID} ${USER} \
 && useradd  --system --uid ${UID} --gid ${UID} \
             --create-home --home-dir /home/${USER} \
             --shell /usr/sbin/nologin ${USER}

WORKDIR /app

# Install pre-built wheels from the builder stage (no compilation in runtime)
COPY --from=builder /build/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

# Copy the application
COPY --chown=${USER}:${USER} app/    ./app/
COPY --chown=${USER}:${USER} static/ ./static/

USER ${USER}

EXPOSE 8000

# Healthcheck — Docker / k8s can use this to know if the container is alive
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request as u, sys; \
        sys.exit(0) if u.urlopen('http://localhost:8000/health').getcode()==200 else sys.exit(1)"

# Don't use --reload in production. One worker per CPU core via gunicorn-style is the
# next step up, but a single uvicorn worker is fine for the demo.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
