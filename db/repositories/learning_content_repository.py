#!/usr/bin/env python3

import logging
from typing import Optional

from core.config import get_settings
from db.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class LearningContentRepository(BaseRepository):
    def __init__(self):
        super().__init__(collection_name=get_settings().MONGO_COLLECTION_NAME)

    async def create_content(self, content_id: str, document: dict) -> str:
        """Permanently store a generated lesson, keyed by content_id.
        created_at is expected to already be set on the document by the
        caller, so it matches what was also written to the Redis cache."""
        mongo_document = dict(document)
        mongo_document["_id"] = self._to_id(doc_id=content_id)
        await self.insert_one(mongo_document)
        logger.info("Learning content %s saved to MongoDB collection '%s'", content_id, self._collection_name)
        return content_id

    async def get_content(self, content_id: str) -> Optional[dict]:
        """Fetch a lesson by its content_id."""
        return await self.find_by_id(doc_id=content_id)

    async def mark_complete(self, content_id: str) -> bool:
        """Mark a lesson as completed by the student."""
        return await self.update_one(doc_id=content_id, update={"is_complete": True})
