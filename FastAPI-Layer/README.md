# FastAPI-Layer — PDF Compressor

Lightweight FastAPI service with two PDF compression endpoints.

## Structure

```
FastAPI-Layer/
├── main.py            # App entry point — creates FastAPI app, registers router
├── routes.py          # All route handlers
├── compressors.py     # pypdf + Ghostscript logic (no FastAPI dependency)
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Run with Docker

```bash
docker compose up --build
```

API: http://localhost:8000  
Swagger UI: http://localhost:8000/docs

## Run locally

```bash
# Install Ghostscript first
sudo apt-get install ghostscript   # Linux
brew install ghostscript           # macOS

pip install -r requirements.txt
uvicorn main:app --reload
```

## Endpoints

### `POST /compress/small-pdf`
pypdf compression — lossless, no image resampling. Best under 50 MB.

```bash
curl -X POST http://localhost:8000/compress/small-pdf \
  -F "file=@document.pdf" -o compressed.pdf -D -
```

### `POST /compress/larger-pdf?quality=ebook`
Ghostscript compression — resamples images, handles any file size.

```bash
curl -X POST "http://localhost:8000/compress/larger-pdf?quality=ebook" \
  -F "file=@large.pdf" -o compressed.pdf -D -
```

Quality options: `screen` (72 DPI) · `ebook` (150 DPI) · `printer` (300 DPI) · `prepress` (300 DPI)

## Response headers

Both endpoints return compression stats in headers:

```
X-Original-Size-MB: 958.00
X-Compressed-Size-MB: 121.30
X-Reduction-Percent: 87.3
X-Quality-Setting: ebook   ← larger-pdf only
```
