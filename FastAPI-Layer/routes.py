"""
routes.py
All API route definitions.
Imported by main.py and mounted on the FastAPI app.
"""

import os
import shutil
import tempfile

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from compressors import compress_with_ghostscript, compress_with_pypdf
from converters import convert_pdf_to_docx

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
            "POST /convert/pdf-to-word": "pdf2docx — any size, returns .docx",
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


DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@router.post("/convert/pdf-to-word", tags=["Convert"])
async def pdf_to_word(file: UploadFile = File(...)):
    """
    Convert a PDF of any size to a Word (.docx) document.
    The upload is streamed to disk and converted page by page.
    """
    _validate_pdf(file.filename)

    work_dir = tempfile.mkdtemp()
    try:
        input_path = os.path.join(work_dir, "input.pdf")
        output_path = os.path.join(work_dir, "output.docx")

        with open(input_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)

        original_mb = _size_mb(input_path)
        await run_in_threadpool(convert_pdf_to_docx, input_path, output_path)

        base_name = os.path.splitext(os.path.basename(file.filename))[0]
        return FileResponse(
            path=output_path,
            media_type=DOCX_MEDIA_TYPE,
            filename=f"{base_name}.docx",
            headers={
                "X-Original-Size-MB": f"{original_mb:.2f}",
                "X-Output-Size-MB": f"{_size_mb(output_path):.2f}",
            },
            background=BackgroundTask(shutil.rmtree, work_dir, ignore_errors=True),
        )
    except Exception as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=str(e))


def _validate_pdf(filename: str):
    if not filename or not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a .pdf")
