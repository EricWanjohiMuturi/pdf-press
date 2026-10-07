"""
main.py
Application entry point.
Creates the FastAPI app and registers routers.
"""

from fastapi import FastAPI
from routes import router

app = FastAPI(
    title="PDF Compressor API",
    description=(
        "Compression: pypdf for small PDFs under 50 MB, "
        "Ghostscript for larger files with image resampling. "
        "Conversion: PDF to Word (.docx) for any file size."
    ),
    version="1.0.0",
)

app.include_router(router)
