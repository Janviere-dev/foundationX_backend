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
        again when the student submits their answers.
        """
        mongo_document = dict(document)
        mongo_document["_id"] = self._to_id(doc_id=quizz_id)
        mongo_document["created_at"] = datetime.now(timezone.utc).isoformat()
        await self.insert_one(mongo_document)
        logger.info("Quiz %s saved to MongoDB collection '%s'", quizz_id, self._collection_name)
        return quizz_id

    async def get_session(self, quizz_id: str) -> Optional[dict]:
        """
        Fetch a quiz by its quizz_id.
        """
        return await self.find_by_id(doc_id=quizz_id)

    async def find_incomplete_session(self, user_id: str) -> Optional[dict]:
        """Find this user's most recent quiz that hasn't been graded yet,
        if any - used to block starting a new quiz before the current one
        is finished. The report itself lives in the separate quizz_report
        collection, so completion is tracked here via the graded flag
        instead of checking for a report field directly."""
        return await self.collection.find_one(
            {"user_id": user_id, "graded": {"$ne": True}},
            sort=[("created_at", -1)],
            )

    async def save_responses(self, quizz_id: str, responses: list[dict]) -> bool:
        """Attach the student's submitted answers to the quiz, before
        grading runs (grading happens as a separate background step)."""
        return await self.update_one(doc_id=quizz_id, update={"responses": responses})

    async def mark_graded(self, quizz_id: str) -> bool:
        """Mark a quiz as graded once its report has been saved to the
        quizz_report collection, so find_incomplete_session doesn't need to
        cross-reference that separate collection."""
        return await self.update_one(doc_id=quizz_id, update={"graded": True})
