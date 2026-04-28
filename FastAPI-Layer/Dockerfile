# ── Base ──────────────────────────────────────────────────────────────────────
FROM python:3.12-slim
 
# ── System dependency: Ghostscript ────────────────────────────────────────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends ghostscript \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
 
# ── Install uv ────────────────────────────────────────────────────────────────
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
 
# ── App setup ─────────────────────────────────────────────────────────────────
WORKDIR /app
 
# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock* ./
 
# Install dependencies — no virtualenv needed inside Docker
RUN uv sync --frozen --no-dev --no-editable
 
COPY . .
 
# ── Run ───────────────────────────────────────────────────────────────────────
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]