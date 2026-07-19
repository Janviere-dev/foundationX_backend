#!/usr/bin/env python3

import asyncio
import logging
import os
from pathlib import Path
from haystack import Document
from typing import List
from agents.rag_pipeline.qdrant_config import init_qdrant
from agents.rag_pipeline.qdrant_config import QdrantDocumentStore
from haystack.document_stores.types import DuplicatePolicy

from agents.rag_pipeline.ingestion.embedding import (
    create_embedder,
    get_documents_to_embed,
    embed_documents,
)

REPO_ROOT = Path(__file__).parent.parent.parent.parent
LOGS_DIR = REPO_ROOT / "server_logs"
ERRORS_LOG_PATH = LOGS_DIR / "errors.log"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

SLICE_SIZE = int(os.getenv("STORE_SLICE_SIZE", "500"))
MAX_RETRIES = int(os.getenv("STORE_MAX_RETRIES", "3"))
RETRY_DELAY_SECONDS = int(os.getenv("STORE_RETRY_DELAY", "5"))


def chunked(items: List, size: int):
    for i in range(0, len(items), size):
        yield items[i:i + size]


class StoreEmbedding:
    def __init__(self, qdrant_store:QdrantDocumentStore):
        self.__qdrant_store = qdrant_store

    def meta_data(self) -> set[str]:
        """
        prepare for storage
        """
        return {
            "file_name",
            "subject",
            "grade",
            "page_number",
            "sparse_embedding",
            "date_added"
            }

    def to_qdrant_documents(self, embedded_docs: List[Document]) -> List[Document]:
        return [
            Document.from_dict({
                "id":document.id,
                "content":document.content,
                "embedding":document.embedding,
                "score":document.score,
                "meta": {
                    key:value for key, value in document.meta.items() if key in self.meta_data()
                    }
                }) for document in embedded_docs]

    def get_existing_ids(self) -> set:
        """Fetch IDs already stored in Qdrant, so a re-run doesn't waste time
        re-embedding and re-uploading documents that already succeeded."""
        existing_documents = self.__qdrant_store.filter_documents()
        existing_ids = {doc.id for doc in existing_documents}
        logger.info("Found %d document(s) already stored in Qdrant, will skip those", len(existing_ids))
        return existing_ids

    async def write_with_retry(self, qdrant_documents: List[Document]) -> int:
        """Write one slice to Qdrant, retrying transient failures (timeouts,
        connection errors) a few times before giving up on this slice."""
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await self.__qdrant_store.write_documents_async(
                    documents=qdrant_documents,
                    policy=DuplicatePolicy.OVERWRITE,
                    )
            except Exception as error:
                last_error = error
                if attempt < MAX_RETRIES:
                    logger.warning(
                        "Write attempt %d/%d failed (%s), retrying in %ds...",
                        attempt, MAX_RETRIES, error, RETRY_DELAY_SECONDS,
                        )
                    await asyncio.sleep(RETRY_DELAY_SECONDS)
        raise last_error

    async def store_embedding(self) -> int:
        """
        Embed and store documents slice by slice instead of all at once:
        - keeps GPU memory usage bounded (small batch_size, small slice in flight)
        - retries transient write failures instead of giving up on the first try
        - skips documents already stored in Qdrant, so re-running after a
          partial failure only processes what's actually missing
        """
        documents = get_documents_to_embed()

        existing_ids = self.get_existing_ids()
        documents = [doc for doc in documents if doc.id not in existing_ids]
        logger.info("%d document(s) remaining to embed and store", len(documents))

        if not documents:
            logger.info("Nothing left to do, all documents already stored")
            return 0

        embedder = create_embedder()

        slices = list(chunked(documents, SLICE_SIZE))
        total_slices = len(slices)
        total_stored = 0

        for slice_index, document_slice in enumerate(slices, start=1):
            try:
                embedded_slice = embed_documents(embedder, document_slice)
                qdrant_documents = self.to_qdrant_documents(embedded_slice)
                written = await self.write_with_retry(qdrant_documents)
                total_stored += written
                logger.info(
                    "Slice %d/%d stored (%d documents, %d total so far)",
                    slice_index, total_slices, written, total_stored,
                    )
            except Exception:
                logger.exception(
                    "Slice %d/%d failed after retries - skipping, continuing with next slice",
                    slice_index, total_slices,
                    )

        return total_stored

async def main():
    document_store = StoreEmbedding(qdrant_store=init_qdrant())
    return await document_store.store_embedding()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(ERRORS_LOG_PATH, mode="a", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,  # embedding.py already configured the root logger on import
                     # (targeting ingestion.log); without force=True, basicConfig()
                     # silently no-ops here and everything keeps going to that file
    )
    print(asyncio.run(main()))
