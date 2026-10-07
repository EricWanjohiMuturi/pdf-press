import os
import shutil
import tempfile

from django.http import FileResponse, JsonResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request

from .converters import convert_pdf_to_docx
from .view_docs import pdf_to_word_schema
from .view_helpers import get_uploaded_pdf

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class _CleanupFile:
    """File wrapper that removes its temp directory when closed by the response."""

    def __init__(self, path, work_dir):
        self._f = open(path, "rb")
        self._work_dir = work_dir

    def __getattr__(self, name):
        return getattr(self._f, name)

    def __iter__(self):
        return iter(self._f)

    def close(self):
        self._f.close()
        shutil.rmtree(self._work_dir, ignore_errors=True)


@pdf_to_word_schema
@api_view(["POST"])
@parser_classes([MultiPartParser])
def pdf_to_word(request: Request):
    """Convert a PDF of any size to a Word (.docx) document."""
    uploaded, error = get_uploaded_pdf(request)
    if error:
        return error

    work_dir = tempfile.mkdtemp()
    try:
        input_path = os.path.join(work_dir, "input.pdf")
        output_path = os.path.join(work_dir, "output.docx")

        with open(input_path, "wb") as f:
            for chunk in uploaded.chunks():
                f.write(chunk)

        convert_pdf_to_docx(input_path, output_path)

        base_name = os.path.splitext(os.path.basename(uploaded.name))[0]
        response = FileResponse(
            _CleanupFile(output_path, work_dir),
            content_type=DOCX_CONTENT_TYPE,
            as_attachment=True,
            filename=f"{base_name}.docx",
        )
        response["X-Original-Size-MB"] = f"{os.path.getsize(input_path) / (1024 * 1024):.2f}"
        response["X-Output-Size-MB"] = f"{os.path.getsize(output_path) / (1024 * 1024):.2f}"
        return response
    except Exception as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        return JsonResponse({"error": str(e)}, status=500)
