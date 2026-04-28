# Django-Layer — PDF Compressor

Django + Django REST Framework service with two PDF compression endpoints.

## Structure

```
Django-Layer/
├── config/
│   ├── settings.py        # Django config, file limits, DRF setup
│   ├── urls.py            # Root URL dispatcher
│   └── wsgi.py            # WSGI entry point for Gunicorn
├── compress_api/
│   ├── compressors.py     # pypdf + Ghostscript logic (no Django dependency)
│   ├── views.py           # Compatibility exports for URL imports
│   ├── views_index.py     # Service/index endpoint handler
│   ├── views_compress.py  # Compression endpoint handlers
│   ├── view_helpers.py    # Shared request/response helper utilities
│   ├── view_docs.py       # OpenAPI/Swagger schema decorators
│   └── urls.py            # App-level URL patterns
├── manage.py
├── pyproject.toml
├── Dockerfile
└── docker-compose.yml
```

## Run with Docker

```bash
docker compose up --build
```

API: http://localhost:8001

Docs:
- Swagger UI: http://localhost:8001/api/docs/
- ReDoc: http://localhost:8001/api/redoc/
- OpenAPI schema: http://localhost:8001/api/schema/

## Run locally

```bash
# Install Ghostscript first
sudo apt-get install ghostscript   # Linux
brew install ghostscript           # macOS

uv sync
uv run manage.py migrate
uv run manage.py runserver
```

## Endpoints

### `POST /compress/small-pdf`
pypdf compression — lossless, no image resampling. Best under 50 MB.

```bash
curl -X POST http://localhost:8001/compress/small-pdf \
  -F "file=@document.pdf" -o compressed.pdf -D -
```

### `POST /compress/larger-pdf?quality=ebook`
Ghostscript compression — resamples images, handles any file size.

```bash
curl -X POST "http://localhost:8001/compress/larger-pdf?quality=ebook" \
  -F "file=@large.pdf" -o compressed.pdf -D -
```

Quality options: `screen` (72 DPI) · `ebook` (150 DPI) · `printer` (300 DPI) · `prepress` (300 DPI)

## Response headers

```
X-Original-Size-MB: 958.00
X-Compressed-Size-MB: 121.30
X-Reduction-Percent: 87.3
X-Quality-Setting: ebook   ← larger-pdf only
```
