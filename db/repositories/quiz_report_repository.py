#!/usr/bin/env python3

import logging
from datetime import datetime, timezone
from typing import Optional

from db.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class QuizReportRepository(BaseRepository):
    def __init__(self):
        super().__init__(collection_name="quizz_report")

    async def save_report(self, quizz_id: str, report: dict) -> str:
        """Store the graded assessment report for a quiz, keyed by quizz_id."""
        mongo_document = dict(report)
        mongo_document["_id"] = self._to_id(doc_id=quizz_id)
        mongo_document["graded_at"] = datetime.now(timezone.utc).isoformat()
        await self.insert_one(mongo_document)
        logger.info("Quiz report %s saved to MongoDB collection '%s'", quizz_id, self._collection_name)
        return quizz_id

    async def get_report(self, quizz_id: str) -> Optional[dict]:
        """Fetch a graded report by quizz_id."""
        return await self.find_by_id(doc_id=quizz_id)

    async def list_reports_for_user(self, user_id: str) -> list[dict]:
        return await self.find_many(filter_query={"user_id": user_id}, limit=100)
