from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiRequest,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from rest_framework import serializers

from .constants import VALID_QUALITIES
UPLOAD_PLACEHOLDER = "<binary PDF file>"


class PDFUploadSerializer(serializers.Serializer):
    file = serializers.FileField(help_text="PDF file to compress.")


ErrorResponseSerializer = inline_serializer(
    name="ErrorResponse",
    fields={"error": serializers.CharField()},
)

index_schema = extend_schema(
    summary="Service information",
    description="Returns a summary of available compression endpoints.",
    responses={
        200: inline_serializer(
            name="ServiceInfoResponse",
            fields={
                "service": serializers.CharField(),
                "endpoints": inline_serializer(
                    name="ServiceEndpoints",
                    fields={
                        "POST /compress/small-pdf": serializers.CharField(),
                        "POST /compress/larger-pdf": serializers.CharField(),
                    },
                ),
            },
        )
    },
)

compress_small_pdf_schema = extend_schema(
    summary="Compress a small PDF",
    description=(
        "Compresses a PDF with pypdf (lossless structural compression). "
        "Files above SMALL_PDF_LIMIT_MB are rejected."
    ),
    request=OpenApiRequest(
        request=PDFUploadSerializer,
        encoding={"file": {"contentType": "application/pdf"}},
        examples=[
            OpenApiExample(
                "Multipart upload",
                summary="Upload PDF using multipart form-data",
                value={"file": UPLOAD_PLACEHOLDER},
                request_only=True,
            )
        ],
    ),
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.BINARY,
            description=(
                "Compressed PDF file (application/pdf). "
                "Response headers include X-Original-Size-MB, "
                "X-Compressed-Size-MB, and X-Reduction-Percent."
            ),
        ),
        400: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Missing upload or invalid file type.",
            examples=[
                OpenApiExample(
                    "Missing file",
                    value={"error": "No file provided. Send a PDF via the 'file' field."},
                ),
                OpenApiExample(
                    "Wrong extension",
                    value={"error": "Uploaded file must be a .pdf"},
                ),
            ],
        ),
        413: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="File exceeds the small-PDF endpoint size limit.",
            examples=[
                OpenApiExample(
                    "Too large",
                    value={
                        "error": "File is 88.3 MB — exceeds the 50 MB limit for this endpoint. Use /compress/larger-pdf instead."
                    },
                )
            ],
        ),
        500: OpenApiResponse(response=ErrorResponseSerializer, description="Compression failed."),
    },
)

compress_large_pdf_schema = extend_schema(
    summary="Compress a larger PDF",
    description=(
        "Compresses a PDF with Ghostscript and optional quality profile. "
        "Recommended for large files and stronger size reduction."
    ),
    request=OpenApiRequest(
        request=PDFUploadSerializer,
        encoding={"file": {"contentType": "application/pdf"}},
        examples=[
            OpenApiExample(
                "Multipart upload",
                summary="Upload PDF using multipart form-data",
                value={"file": UPLOAD_PLACEHOLDER},
                request_only=True,
            )
        ],
    ),
    parameters=[
        OpenApiParameter(
            name="quality",
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            enum=sorted(VALID_QUALITIES),
            default="ebook",
            description="Ghostscript quality profile.",
        )
    ],
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.BINARY,
            description=(
                "Compressed PDF file (application/pdf). "
                "Response headers include X-Original-Size-MB, "
                "X-Compressed-Size-MB, X-Reduction-Percent, and X-Quality-Setting."
            ),
        ),
        400: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Missing upload, invalid file type, or invalid quality value.",
            examples=[
                OpenApiExample(
                    "Invalid quality",
                    value={
                        "error": "Invalid quality 'ultra'. Choose from: ['ebook', 'prepress', 'printer', 'screen']"
                    },
                )
            ],
        ),
        500: OpenApiResponse(response=ErrorResponseSerializer, description="Compression failed."),
    },
)
