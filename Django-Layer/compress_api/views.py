"""Compatibility module for URL imports.

Actual handlers live in dedicated modules to keep concerns separated.
"""

from .views_compress import compress_large_pdf, compress_small_pdf
from .views_index import index

__all__ = ["index", "compress_small_pdf", "compress_large_pdf"]
