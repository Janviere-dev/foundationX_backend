#!/usr/bin/env python3

import asyncio
import json
import logging
from pathlib import Path
from typing import List

from pymongo import ReplaceOne

from core.config import get_settings
from db.mongodb import connect_to_mongo, close_mongo_connection
from db.repositories.base import BaseRepository

settings = get_settings()

REPO_ROOT = Path(__file__).parent.parent.parent.parent
CACHES_DIR = REPO_ROOT / "caches"
LOGS_DIR = REPO_ROOT / "server_logs"
LEARNING_CHUNK_PATH = CACHES_DIR / "document_split.json"
ERRORS_LOG_PATH = LOGS_DIR / "errors.log"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

SLICE_SIZE = settings.STORE_SLICE_SIZE
MAX_RETRIES = settings.STORE_MAX_RETRIES
RETRY_DELAY_SECONDS = settings.STORE_RETRY_DELAY


def chunked(items: List, size: int):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def load_learning_units() -> List[dict]:
    """Load learning_units.json exactly as-is - every field, unmodified."""
    with open(LEARNING_CHUNK_PATH, encoding="utf-8") as file:
        chunks = json.load(file)
    logger.info("Loaded %d chunks from %s", len(chunks), LEARNING_CHUNK_PATH)
    return chunks


class StoreEmbedding(BaseRepository):
    def __init__(self, collection_name: str):
        super().__init__(collection_name=collection_name)

    async def bulk_upsert(self, documents: list[dict]) -> int:
        """ store many """
        if not documents:
            return 0
        operations = [ReplaceOne({"_id": doc["_id"]}, doc, upsert=True) for doc in documents]
        result = await self.collection.bulk_write(operations)
        return result.upserted_count + result.modified_count
    
    def to_mongo_document(self, chunk: dict) -> dict:
        """
        This function turn a normal ID to mongo db ID
        """
        mongo_doc = dict(chunk)
        mongo_doc["_id"] = self._to_id(doc_id=chunk.get("id", ""))
        return mongo_doc

    async def store_slice_with_retry(self, mongo_documents: List[dict]) -> int:
        """
        Upsert one slice, retrying transient failures (timeouts, connection
        errors) a few times before giving up on this slice.
        """
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return await self.bulk_upsert(mongo_documents)
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
        This function stores all the chunks
        """
        chunks = load_learning_units()
        mongo_documents = [self.to_mongo_document(chunk) for chunk in chunks]

        slices = list(chunked(mongo_documents, SLICE_SIZE))
        total_slices = len(slices)
        total_stored = 0

        for slice_index, document_slice in enumerate(slices, start=1):
            try:
                written = await self.store_slice_with_retry(document_slice)
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
    await connect_to_mongo()
    settings.MONGO_COLLECTION_NAME = "courses"
    document_store = StoreEmbedding(collection_name=settings.MONGO_COLLECTION_NAME)
    total = await document_store.store_embedding()
    await close_mongo_connection()
    return total

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(ERRORS_LOG_PATH, mode="a", encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )
    print(asyncio.run(main()))
