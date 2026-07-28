#!/usr/bin/env python3

import logging
from datetime import datetime, timezone
from typing import Optional

from db.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class QuizSessionRepository(BaseRepository):
    def __init__(self):
        super().__init__(collection_name="quiz_sessions")

    async def create_session(self, quizz_id: str, document: dict) -> str:
        """Store a newly generated quiz (questions, correct answers,
        grade/subject metadata), keyed by quizz_id so it can be looked up
        again when the student submits their answers. created_at is
        expected to already be set on the document by the caller, so it
        matches exactly what was also written to the Redis cache.
        """
        mongo_document = dict(document)
        mongo_document["_id"] = self._to_id(doc_id=quizz_id)
        await self.insert_one(mongo_document)
        logger.info("Quiz %s saved to MongoDB collection '%s'", quizz_id, self._collection_name)
        return quizz_id

    async def get_session(self, quizz_id: str) -> Optional[dict]:
        """
        Fetch a quiz by its quizz_id.
        """
        return await self.find_by_id(doc_id=quizz_id)

    async def find_incomplete_session(self, user_id: str) -> Optional[dict]:
        """Find this user's most recent quiz still in "started" status, if
        any - used to block starting a new quiz before the current one is
        finished or has expired into "abandoned"."""
        return await self.collection.find_one(
            {"user_id": user_id, "status": "started"},
            sort=[("created_at", -1)],
            )

    async def save_responses(self, quizz_id: str, responses: list[dict]) -> bool:
        """Attach the student's submitted answers to the quiz, before
        grading runs (grading happens as a separate background step)."""
        return await self.update_one(doc_id=quizz_id, update={"responses": responses})

    async def mark_completed(self, quizz_id: str) -> bool:
        """Mark a quiz as completed once the student has submitted their
        answers - this is what unblocks starting a new quiz."""
        return await self.update_one(
            doc_id=quizz_id,
            update={"status": "completed", "end_time": datetime.now(timezone.utc).isoformat()},
            )

    async def mark_abandoned(self, quizz_id: str) -> bool:
        """Mark a quiz as abandoned - the student never resumed it before
        its Redis cache entry expired."""
        return await self.update_one(
            doc_id=quizz_id,
            update={"status": "abandoned", "end_time": datetime.now(timezone.utc).isoformat()},
            )
