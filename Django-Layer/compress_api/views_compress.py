from django.conf import settings
from django.http import JsonResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request

from .compressors import compress_with_ghostscript, compress_with_pypdf
from .constants import VALID_QUALITIES
from .view_docs import compress_large_pdf_schema, compress_small_pdf_schema
from .view_helpers import get_uploaded_pdf, run_compression


@compress_small_pdf_schema
@api_view(["POST"])
@parser_classes([MultiPartParser])
def compress_small_pdf(request: Request):
    """Compress a small PDF using pypdf (lossless)."""
    uploaded, error = get_uploaded_pdf(request)
    if error:
        return error

    limit_mb = getattr(settings, "SMALL_PDF_LIMIT_MB", 50)
    size_mb = uploaded.size / (1024 * 1024)

    if size_mb > limit_mb:
        return JsonResponse(
            {
                "error": (
                    f"File is {size_mb:.1f} MB - exceeds the {limit_mb} MB limit "
                    f"for this endpoint. Use /compress/larger-pdf instead."
                )
            },
            status=413,
        )

    return run_compression(
        uploaded=uploaded,
        compress_fn=lambda inp, out: compress_with_pypdf(inp, out),
        size_mb=size_mb,
    )


@compress_large_pdf_schema
@api_view(["POST"])
@parser_classes([MultiPartParser])
def compress_large_pdf(request: Request):
    """Compress any PDF using Ghostscript."""
    uploaded, error = get_uploaded_pdf(request)
    if error:
        return error

    quality = request.query_params.get("quality", "ebook")
    if quality not in VALID_QUALITIES:
        return JsonResponse(
            {"error": f"Invalid quality '{quality}'. Choose from: {sorted(VALID_QUALITIES)}"},
            status=400,
        )

    size_mb = uploaded.size / (1024 * 1024)

    return run_compression(
        uploaded=uploaded,
        compress_fn=lambda inp, out: compress_with_ghostscript(inp, out, quality),
        size_mb=size_mb,
        extra_headers={"X-Quality-Setting": quality},
    )
