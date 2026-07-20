#!/usr/bin/env python3
"""
Full production run: OCR-repair every cached document (all 150, including
scanned past papers), save repaired full documents back to caches/document_split.json,
then chunk everything and save chunks to caches/chunks.json.

Progress and errors are logged to server_logs/event.log (and stdout) so the run can be
monitored while unattended on a server. Both caches/ and server_logs/ are created
automatically if they don't exist yet.

Run with: ./venv/bin/python3 -m agents.rag_pipeline.ingestion.run_ocr_and_chunk

Env vars:
  OCR_WORKERS - parallel OCR workers (default: os.cpu_count())
  OCR_LIMIT   - only process the first N cached documents (for smoke-testing)
  OCR_FILES   - comma-separated file_names to re-OCR; all other documents are
                loaded and re-chunked as-is but skipped for OCR (fast targeted
                re-run instead of reprocessing the whole corpus)
"""
import io
import json
import logging
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz
import pytesseract
from PIL import Image
from haystack import Document

from .helpers.helper_ocr import page_needs_ocr
from .chunking import DocumentSplitter
from core.config import get_settings

settings = get_settings()

RESSOURCES_ROOT = Path(__file__).parent.parent.parent / "ressources"
REPO_ROOT = Path(__file__).parent.parent.parent.parent
CACHES_DIR = REPO_ROOT / "caches"
LOGS_DIR = REPO_ROOT / "server_logs"
CACHE_PATH = CACHES_DIR / "document_split.json"
CHUNKS_PATH = CACHES_DIR / "chunks.json"
LOG_PATH = LOGS_DIR / "event.log"
MAX_WORKERS = settings.OCR_WORKERS

CACHES_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def find_pdf_path(file_name: str) -> Path | None:
    return next(RESSOURCES_ROOT.rglob(file_name), None)


def ocr_one_page(pdf_path: Path, page_index: int, dpi: int = 300) -> str:
    with fitz.open(pdf_path) as pdf:
        if page_index >= len(pdf):
            return ""
        pixmap = pdf[page_index].get_pixmap(dpi=dpi)
        image = Image.open(io.BytesIO(pixmap.tobytes("png")))
        return pytesseract.image_to_string(image)


def build_ocr_jobs(cached_documents, target_names=None):
    """For each document, extract fresh per-page text directly from the real
    PDF via PyMuPDF and collect every page needing OCR into one flat job list
    for corpus-wide parallel execution.

    Deliberately ignores the cached document's own '\\f'-delimited content
    entirely: a broken font encoding can spuriously decode some of its glyphs
    to '\\f' too, badly inflating the apparent page count (one book had 5445
    '\\f'-delimited "pages" for a real 540-page PDF). Trusting that count to
    index into the real PDF sends most OCR calls to out-of-range pages, which
    silently come back empty. Using the PDF's own pages as the source of
    truth for both the page count and each page's text sidesteps this."""
    jobs = []
    doc_pages = {}

    for doc_index, doc in enumerate(cached_documents):
        file_name = doc.get("file_name")
        if not file_name:
            logger.warning("Document at index %d has no file_name, skipping", doc_index)
            continue

        if target_names is not None and file_name not in target_names:
            continue

        try:
            pdf_path = find_pdf_path(file_name)
            if pdf_path is None:
                logger.warning("Could not find source PDF on disk for %s, skipping OCR", file_name)
                continue

            with fitz.open(pdf_path) as pdf:
                pages = [page.get_text() for page in pdf]

            doc_pages[doc_index] = pages
            bad_indexes = [i for i, p in enumerate(pages) if page_needs_ocr(p)]
            for i in bad_indexes:
                jobs.append((doc_index, pdf_path, i))

        except Exception:
            logger.exception("Failed to prepare OCR job for %s", file_name)

    return jobs, doc_pages


def run_ocr(cached_documents, target_names=None):
    jobs, doc_pages = build_ocr_jobs(cached_documents, target_names)
    logger.info("Total pages needing OCR: %d", len(jobs))

    start = time.perf_counter()
    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(ocr_one_page, pdf_path, page_index): (doc_index, page_index)
            for doc_index, pdf_path, page_index in jobs
        }
        for future in as_completed(futures):
            doc_index, page_index = futures[future]
            file_name = cached_documents[doc_index].get("file_name")
            try:
                doc_pages[doc_index][page_index] = future.result()
            except Exception:
                logger.exception("OCR failed for %s page %d", file_name, page_index + 1)

            done += 1
            if done % 25 == 0 or done == len(jobs):
                elapsed = time.perf_counter() - start
                logger.info("%d/%d pages OCR'd (%.1fs elapsed)", done, len(jobs), elapsed)

    elapsed = time.perf_counter() - start
    logger.info("OCR pass complete in %.1fs (%.1f min)", elapsed, elapsed / 60)

    for doc_index, pages in doc_pages.items():
        cached_documents[doc_index]["content"] = "\x0c".join(pages)

    return cached_documents


def run_chunking(cached_documents):
    splitter = DocumentSplitter()
    all_chunks = []

    for doc_dict in cached_documents:
        file_name = doc_dict.get("file_name")
        content = doc_dict.get("content")
        if not content or not content.strip():
            logger.warning("Skipping chunking for %s: still empty after OCR", file_name)
            continue

        try:
            document = Document.from_dict(doc_dict)
            chunks = splitter.run_splitter(documents=[document])
            all_chunks.extend(chunks)
            logger.info("Chunked %s into %d chunks", file_name, len(chunks))
        except Exception:
            logger.exception("Failed to chunk %s", file_name)

    return all_chunks


def main():
    logger.info("=== Starting OCR + chunking run ===")

    with open(CACHE_PATH, encoding="utf-8") as f:
        cached_documents = json.load(f)
    logger.info("Loaded %d cached documents", len(cached_documents))

    if settings.OCR_LIMIT:
        cached_documents = cached_documents[:settings.OCR_LIMIT]
        logger.info("OCR_LIMIT set: only processing first %d documents", settings.OCR_LIMIT)

    target_names = None
    if settings.OCR_FILES:
        target_names = {name.strip() for name in settings.OCR_FILES.split(",") if name.strip()}
        logger.info("OCR_FILES set: only re-OCR'ing %d target file(s): %s", len(target_names), sorted(target_names))

    cached_documents = run_ocr(cached_documents, target_names)

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cached_documents, f, indent=2)
    logger.info("Saved OCR-repaired documents to %s", CACHE_PATH)

    chunks = run_chunking(cached_documents)
    logger.info("Total chunks produced: %d", len(chunks))

    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump([chunk.to_dict() for chunk in chunks], f, indent=2)
    logger.info("Saved chunks to %s", CHUNKS_PATH)

    logger.info("=== Run complete ===")


if __name__ == "__main__":
    main()
