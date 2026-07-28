#!/usr/bin/env python3

import logging
from typing import Optional

from db.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ChatRepository(BaseRepository):
    def __init__(self):
        super().__init__(collection_name="chat_sessions")

    async def create_session(self, session_id: str, document: dict) -> str:
        """Permanently store a new chat session (first turn included)."""
        mongo_document = dict(document)
        mongo_document["_id"] = self._to_id(doc_id=session_id)
        await self.insert_one(mongo_document)
        logger.info("Chat session %s saved to MongoDB collection '%s'", session_id, self._collection_name)
        return session_id

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Fetch a chat session by its session_id."""
        return await self.find_by_id(doc_id=session_id)

    async def append_turn(self, session_id: str, turn: dict, turn_count: int, summary: Optional[str], updated_at: str) -> bool:
        """Append a new turn to an existing session and refresh its
        bookkeeping fields (turn_count/summary/updated_at)."""
        result = await self.collection.update_one(
            {"_id": self._to_id(doc_id=session_id)},
            {
                "$push": {"messages": turn},
                "$set": {"turn_count": turn_count, "summary": summary, "updated_at": updated_at},
                },
            )
        return result.modified_count > 0

    async def list_sessions(self, user_id: str, limit: int = 50) -> list[dict]:
        """List a user's chat sessions, most recently updated first."""
        cursor = self.collection.find({"user_id": user_id}).sort("updated_at", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session."""
        return await self.delete_one(doc_id=session_id)
