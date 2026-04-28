"""
routes.py
All API route definitions.
Imported by main.py and mounted on the FastAPI app.
"""

import os
import shutil
import tempfile

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse

from compressors import compress_with_ghostscript, compress_with_pypdf

router = APIRouter()

SMALL_PDF_LIMIT_MB = 50
VALID_QUALITIES = {"screen", "ebook", "printer", "prepress"}


def _size_mb(path: str) -> float:
    return os.path.getsize(path) / (1024 * 1024)


def _compression_headers(original_mb: float, compressed_mb: float, extra: dict = {}) -> dict:
    reduction = ((original_mb - compressed_mb) / original_mb) * 100
    return {
        "X-Original-Size-MB": f"{original_mb:.2f}",
        "X-Compressed-Size-MB": f"{compressed_mb:.2f}",
        "X-Reduction-Percent": f"{reduction:.1f}",
        **extra,
    }


@router.get("/", tags=["Info"])
def root():
    return {
        "service": "PDF Compressor API",
        "endpoints": {
            "POST /compress/small-pdf": f"pypdf — PDFs under {SMALL_PDF_LIMIT_MB} MB",
            "POST /compress/larger-pdf": "Ghostscript — any size, image resampling",
        },
    }


@router.post("/compress/small-pdf", tags=["Compress"])
async def compress_small_pdf(file: UploadFile = File(...)):
    """
    Compress a small PDF (< 50 MB) using pypdf.
    Lossless — removes redundant objects and compresses content streams.
    """
    _validate_pdf(file.filename)

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)

    if size_mb > SMALL_PDF_LIMIT_MB:
        raise HTTPException(
            status_code=413,
            detail=(
                f"File is {size_mb:.1f} MB — exceeds the {SMALL_PDF_LIMIT_MB} MB limit "
                f"for this endpoint. Use /compress/larger-pdf instead."
            ),
        )

    work_dir = tempfile.mkdtemp()
    try:
        input_path = os.path.join(work_dir, "input.pdf")
        output_path = os.path.join(work_dir, "compressed.pdf")

        with open(input_path, "wb") as f:
            f.write(contents)

        compress_with_pypdf(input_path, output_path)

        compressed_mb = _size_mb(output_path)
        headers = _compression_headers(size_mb, compressed_mb)

        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename=f"compressed_{file.filename}",
            headers=headers,
        )
    except Exception as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compress/larger-pdf", tags=["Compress"])
async def compress_large_pdf(
    file: UploadFile = File(...),
    quality: str = Query(default="ebook", enum=list(VALID_QUALITIES)),
):
    """
    Compress any PDF using Ghostscript.
    Resamples embedded images to the target DPI for the chosen quality level.

    - screen   : 72 DPI  — smallest file
    - ebook    : 150 DPI — recommended default
    - printer  : 300 DPI — print ready
    - prepress : 300 DPI — near lossless
    """
    _validate_pdf(file.filename)

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)

    work_dir = tempfile.mkdtemp()
    try:
        input_path = os.path.join(work_dir, "input.pdf")
        output_path = os.path.join(work_dir, "compressed.pdf")

        with open(input_path, "wb") as f:
            f.write(contents)

        compress_with_ghostscript(input_path, output_path, quality)

        compressed_mb = _size_mb(output_path)
        headers = _compression_headers(
            size_mb, compressed_mb, extra={"X-Quality-Setting": quality}
        )

        return FileResponse(
            path=output_path,
            media_type="application/pdf",
            filename=f"compressed_{file.filename}",
            headers=headers,
        )
    except Exception as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


def _validate_pdf(filename: str):
    if not filename or not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .pdf")
