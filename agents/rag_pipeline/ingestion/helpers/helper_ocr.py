import io
import re
from pathlib import Path

import fitz
import pytesseract
from PIL import Image

# marks a page extracted from a PDF with a broken/non-standard font encoding
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
    """
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
