#!/usr/bin/env python3

import logging
from datetime import datetime, timezone

from db.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ProgressRepository(BaseRepository):
    def __init__(self):
        super().__init__(collection_name="student_progress")

    async def start_lesson(self, user_id: str, subject: str, topic: str, content_id: str) -> str:
        document = {
            "user_id": user_id,
            "subject": subject,
            "topic": topic,
            "content_id": content_id,
            "status": "started",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            }
        return await self.insert_one(document=document)

    async def complete_lesson(self, content_id: str) -> bool:
        # matched by content_id, not _id - BaseRepository.update_one assumes _id
        result = await self.collection.update_one(
            {"content_id": content_id},
            {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}},
            )
        return result.modified_count > 0

    async def count_progress(self, user_id: str) -> dict:
        started = await self.count({"user_id": user_id})
        completed = await self.count({"user_id": user_id, "status": "completed"})
        return {"started": started, "completed": completed, "in_progress": started - completed}
