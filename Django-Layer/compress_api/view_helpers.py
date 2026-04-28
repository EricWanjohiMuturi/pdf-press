import os
import shutil
import tempfile

from django.http import FileResponse, JsonResponse


def get_uploaded_pdf(request):
    """Validate uploaded input and return (uploaded_file, error_response)."""
    uploaded = request.FILES.get("file")
    if not uploaded:
        return None, JsonResponse(
            {"error": "No file provided. Send a PDF via the 'file' field."}, status=400
        )
    if not uploaded.name.lower().endswith(".pdf"):
        return None, JsonResponse(
            {"error": "Uploaded file must be a .pdf"}, status=400
        )
    return uploaded, None


def run_compression(uploaded, compress_fn, size_mb, extra_headers=None):
    """Write upload to disk, compress it, then return the file response."""
    work_dir = tempfile.mkdtemp()
    try:
        input_path = os.path.join(work_dir, "input.pdf")
        output_path = os.path.join(work_dir, "compressed.pdf")

        with open(input_path, "wb") as f:
            for chunk in uploaded.chunks():
                f.write(chunk)

        compress_fn(input_path, output_path)

        compressed_mb = os.path.getsize(output_path) / (1024 * 1024)
        reduction = ((size_mb - compressed_mb) / size_mb) * 100

        response = FileResponse(
            open(output_path, "rb"),
            content_type="application/pdf",
            as_attachment=True,
            filename=f"compressed_{uploaded.name}",
        )
        response["X-Original-Size-MB"] = f"{size_mb:.2f}"
        response["X-Compressed-Size-MB"] = f"{compressed_mb:.2f}"
        response["X-Reduction-Percent"] = f"{reduction:.1f}"

        for key, value in (extra_headers or {}).items():
            response[key] = value

        return response

    except Exception as e:
        shutil.rmtree(work_dir, ignore_errors=True)
        return JsonResponse({"error": str(e)}, status=500)
