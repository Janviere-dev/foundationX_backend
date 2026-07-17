import io
import re
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

# marks a page extracted from a PDF with a broken/non-standard font encoding
# (pypdf/PyMuPDF both decode these glyphs to control characters instead of real text)
CORRUPTION_PATTERN = re.compile(r"[\x00-\x08\x0b\x0e-\x1f]")


def page_needs_ocr(page_text: str) -> bool:
    """True if a page's extracted text is empty (scanned image) or contains
    control-character garbage from a broken font encoding - both cases the
    normal text layer can't recover from."""
    if not page_text or not page_text.strip():
        return True
    return bool(CORRUPTION_PATTERN.search(page_text))


def repair_pdf_text(pdf_path: Path, extracted_text: str, dpi: int = 300) -> str:
    """Replace any broken page in extracted_text with OCR'd text from the
    original PDF. Pages are '\\f'-separated, matching PyPDFToDocument's
    per-page joining. Only opens/rasterizes pages that actually need it."""
    pages = extracted_text.split("\x0c")

    with fitz.open(pdf_path) as pdf:
        # a totally empty/near-empty extraction (e.g. a scanned PDF with no text
        # layer at all) yields far fewer "pages" here than the PDF actually has -
        # pad out to the real page count so every page gets OCR'd, not just the first
        if len(pages) < len(pdf):
            pages += [""] * (len(pdf) - len(pages))

        bad_page_indexes = [i for i, page_text in enumerate(pages) if page_needs_ocr(page_text)]
        for i in bad_page_indexes:
            if i >= len(pdf):
                continue
            pixmap = pdf[i].get_pixmap(dpi=dpi)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            pages[i] = pytesseract.image_to_string(image)

    return "\x0c".join(pages)
