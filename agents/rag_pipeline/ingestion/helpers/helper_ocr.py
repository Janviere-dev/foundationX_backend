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


def repair_pdf_text(pdf_path: Path, dpi: int = 300) -> str:
    """Rebuild a PDF's text page-by-page directly from the PDF itself, OCR-ing
    any page that's empty or has broken/garbled text.

    Deliberately ignores the original pypdf-extracted text and its '\\f' page
    boundaries entirely: a broken font encoding can spuriously decode some of
    its glyphs to '\\f' too, which massively inflates the apparent page count
    (e.g. one book had 5445 '\\f'-delimited "pages" for a real 540-page PDF).
    Trusting that count to index into the real PDF sends most OCR calls to
    out-of-range pages, which silently come back empty. Using the PDF's own
    page objects as the source of truth for both the page count and each
    page's text sidesteps this entirely."""
    pages = []
    with fitz.open(pdf_path) as pdf:
        for page in pdf:
            page_text = page.get_text()
            if page_needs_ocr(page_text):
                pixmap = page.get_pixmap(dpi=dpi)
                image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                page_text = pytesseract.image_to_string(image)
            pages.append(page_text)

    return "\x0c".join(pages)
