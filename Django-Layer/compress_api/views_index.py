from django.conf import settings
from django.http import JsonResponse

from .view_docs import index_schema


@index_schema
def index(request):
    limit = getattr(settings, "SMALL_PDF_LIMIT_MB", 50)
    return JsonResponse({
        "service": "PDF Compressor API",
        "endpoints": {
            "POST /compress/small-pdf": f"pypdf - PDFs under {limit} MB",
            "POST /compress/larger-pdf": "Ghostscript - any size, image resampling",
        },
    })
