"""
compressors.py
Core compression logic — decoupled from routing.
Importable and testable independently of FastAPI.
"""

import subprocess
from pypdf import PdfReader, PdfWriter


def compress_with_pypdf(input_path: str, output_path: str) -> None:
    """
    Lossless structural compression using pypdf.
    Best for PDFs under 50 MB.
    Compresses content streams and removes redundant objects.
    Does NOT resample embedded images.
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        page.compress_content_streams()
        writer.add_page(page)

    writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)

    with open(output_path, "wb") as f:
        writer.write(f)


def compress_with_ghostscript(
    input_path: str,
    output_path: str,
    quality: str = "ebook",
) -> None:
    """
    Full compression via Ghostscript.
    Handles any file size. Resamples images to target DPI.

    quality options:
        screen   → 72 DPI  (smallest file)
        ebook    → 150 DPI (recommended default)
        printer  → 300 DPI (print ready)
        prepress → 300 DPI (near lossless)
    """
    result = subprocess.run(
        [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            f"-dPDFSETTINGS=/{quality}",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
            f"-sOutputFile={output_path}",
            input_path,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Ghostscript failed: {result.stderr.strip()}")
