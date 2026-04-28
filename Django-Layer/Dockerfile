# ── Base ──────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

# ── System dependency: Ghostscript ────────────────────────────────────────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends ghostscript \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── App setup ─────────────────────────────────────────────────────────────────
WORKDIR /app
COPY pyproject.toml .
RUN python -c "import tomllib, subprocess; deps=tomllib.load(open('pyproject.toml','rb'))['project']['dependencies']; subprocess.check_call(['pip','install','--no-cache-dir', *deps])"

COPY . .

# ── Run ───────────────────────────────────────────────────────────────────────
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --run-syncdb && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2"]
