#!/usr/bin/env python3
"""
Standalone test: run OCR repair across all cached documents (skipping empty
ones) and report how it performs. Patches document_split.json in place with
the repaired content, so the work isn't wasted.

Run with: ./venv/bin/python3 -m agents.rag_pipeline.ingestion.test_ocr_repair
"""
import io
import json
import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz
import pytesseract
from PIL import Image

from .helpers.helper_ocr import page_needs_ocr

RESSOURCES_ROOT = Path(__file__).parent.parent.parent / "ressources"
CACHE_PATH = Path(__file__).parent.parent.parent.parent / "document_split.json"
MAX_WORKERS = int(os.getenv("OCR_WORKERS", os.cpu_count()))


def find_pdf_path(file_name: str) -> Path | None:
    return next(RESSOURCES_ROOT.rglob(file_name), None)


def ocr_one_page(pdf_path: Path, page_index: int, dpi: int = 300) -> str:
    with fitz.open(pdf_path) as pdf:
        if page_index >= len(pdf):
            return ""
        pixmap = pdf[page_index].get_pixmap(dpi=dpi)
        image = Image.open(io.BytesIO(pixmap.tobytes("png")))
        return pytesseract.image_to_string(image)


def main():
    with open(CACHE_PATH, encoding="utf-8") as f:
        cached_documents = json.load(f)

    non_empty = [d for d in cached_documents if d.get("content") and d["content"].strip()]
    print(f"Testing OCR repair on {len(non_empty)} non-empty documents "
          f"(skipping {len(cached_documents) - len(non_empty)} empty ones)")
    print(f"Using {MAX_WORKERS} parallel workers\n")

    # build the full work list: (doc_index, pdf_path, bad_page_index) across ALL docs.
    # keyed by list index, not file_name - several cached documents share the same
    # file_name (the same PDF exists under multiple folders), so file_name would collide.
    jobs = []
    doc_pages = {}
    missing_files = []

    for doc_index, doc in enumerate(non_empty):
        pages = doc["content"].split("\x0c")
        doc_pages[doc_index] = pages
        bad_indexes = [i for i, p in enumerate(pages) if page_needs_ocr(p)]
        if not bad_indexes:
            continue
        pdf_path = find_pdf_path(doc["file_name"])
        if pdf_path is None:
            missing_files.append(doc["file_name"])
            continue
        for i in bad_indexes:
            jobs.append((doc_index, pdf_path, i))

    if missing_files:
        print(f"WARNING: could not find source PDF on disk for {len(missing_files)} files, skipping their OCR:")
        for name in missing_files:
            print(f"  - {name}")
        print()

    print(f"Total pages needing OCR: {len(jobs)}\n")

    start = time.perf_counter()
    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(ocr_one_page, pdf_path, page_index): (doc_index, page_index, non_empty[doc_index]["file_name"])
            for doc_index, pdf_path, page_index in jobs
        }
        for future in as_completed(futures):
            doc_index, page_index, file_name = futures[future]
            try:
                doc_pages[doc_index][page_index] = future.result()
            except Exception as e:
                print(f"FAIL  {file_name} page {page_index + 1}: {e}")
            done += 1
            if done % 25 == 0 or done == len(jobs):
                elapsed = time.perf_counter() - start
                print(f"{done}/{len(jobs)} pages OCR'd ({elapsed:.1f}s elapsed)")

    elapsed = time.perf_counter() - start
    print(f"\nOCR pass complete in {elapsed:.1f}s ({elapsed/60:.1f} min)")

    # non_empty entries are the same dict objects referenced inside cached_documents,
    # so mutating them here updates cached_documents too - no name-based lookup needed
    for doc_index, pages in doc_pages.items():
        non_empty[doc_index]["content"] = "\x0c".join(pages)

    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cached_documents, f, indent=2)
    print(f"Patched repaired content into {CACHE_PATH}")


if __name__ == "__main__":
    main()
