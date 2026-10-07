"""
converters.py
PDF -> Word conversion helpers.
"""

import os
import re
import tempfile

import pymupdf
from docx import Document
from pdf2docx import Converter

_FONT_SUFFIX = re.compile(r"(?:[-,]?(?:PS)?MT|[-,]?(?:Roman|Regular))$|[-,](?:Bold|Italic|BoldItalic|Oblique)(?:MT)?$")


def _strip_glyph_outlines(src: str, dst: str) -> bool:
    """Remove vector glyph outlines drawn over real text (fake bold); they come out as duplicated outlined text in Word."""
    doc = pymupdf.open(src)
    changed = False
    for page in doc:
        words = [pymupdf.Rect(w[:4]) for w in page.get_text("words")]
        if not words:
            continue
        marked = False
        for dr in page.get_drawings():
            r = dr["rect"]
            if dr["type"] != "s" or len(dr["items"]) < 3 or not (3 <= r.height <= 80) or r.is_empty:
                continue
            if any((r & w).get_area() >= 0.5 * r.get_area() for w in words):
                page.add_redact_annot(pymupdf.Rect(r.x0 + 0.5, r.y0 + 0.5, r.x1 - 0.5, r.y1 - 0.5))
                marked = True
        if marked:
            page.apply_redactions(images=0, graphics=2, text=1)
            changed = True
    if changed:
        doc.save(dst, garbage=3, deflate=True)
    doc.close()
    return changed


def _normalize_fonts(docx_path: str) -> None:
    # PDF names like "ArialMT" are unknown to Word and fall back to a serif font.
    doc = Document(docx_path)
    qn = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    for el in doc.element.body.iter(f"{qn}rFonts"):
        for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
            name = el.get(f"{qn}{attr}")
            if name:
                el.set(f"{qn}{attr}", _FONT_SUFFIX.sub("", name.split("+")[-1]))
    doc.save(docx_path)


def convert_pdf_to_docx(input_path: str, output_path: str) -> None:
    # pdf2docx parses and writes page by page, so large PDFs are handled without loading all pages at once.
    with tempfile.TemporaryDirectory() as tmp:
        cleaned = os.path.join(tmp, "cleaned.pdf")
        source = cleaned if _strip_glyph_outlines(input_path, cleaned) else input_path

        cv = Converter(source)
        try:
            cv.convert(
                output_path,
                start=0,
                end=None,
                # Keep original line breaks and avoid false table detection, the main causes of distorted text.
                line_break_width_ratio=0.1,
                line_break_free_space_ratio=0.3,
                new_paragraph_free_space_ratio=1.2,
                max_line_spacing_ratio=2.0,
                parse_stream_table=False,
                clip_image_res_ratio=6.0,
                raw_exceptions=True,
            )
        finally:
            cv.close()

    _normalize_fonts(output_path)
