#!/usr/bin/env python3

from bson import ObjectId

from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorCollection

from db.mongodb import get_database


class BaseRepository:
    """Base repository providing common async CRUD operations for MongoDB collections."""

    def __init__(self, collection_name: str):
        self._collection_name = collection_name

    @property
    def collection(self) -> AsyncIOMotorCollection:
        """Return the Motor collection instance for this repository."""
        return get_database()[self._collection_name]

    def _to_id(self, doc_id:str):
        """
        Try to convert to ObjectId (for Mongo-generated IDs); fall back to plain string (for UUID IDs).
        """
        try:
            return ObjectId(doc_id)
        except Exception:
            return doc_id

    async def find_by_id(self, doc_id: str) -> Optional[dict]:
        """Find a single document by its _id field."""
        return await self.collection.find_one({"_id": self._to_id(doc_id=doc_id)})

    async def find_many(
        self,
        filter_query: dict,
        skip: int = 0,
        limit: int = 50,
        sort: Optional[list[tuple[str, int]]] = None,
    ) -> list[dict]:
        """Find multiple documents matching filter_query with pagination and optional sorting."""
        cursor = self.collection.find(filter_query).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        return await cursor.to_list(length=limit)

    async def insert_one(self, document: dict) -> str:
        """Insert a single document and return its _id as a string."""
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)

    async def update_one(self, doc_id: str, update: dict) -> bool:
        """Update fields on a single document. Returns True if a document was modified."""
        result = await self.collection.update_one(
            {"_id": self._to_id(doc_id=doc_id)}, {"$set": update}
        )
        return result.modified_count > 0

    async def delete_one(self, doc_id: str) -> bool:
        """Delete a single document by _id. Returns True if a document was deleted."""
        result = await self.collection.delete_one({"_id": self._to_id(doc_id=doc_id)})
        return result.deleted_count > 0

    async def count(self, filter_query: Optional[dict] = None) -> int:
        """Count documents matching the filter, or all documents if no filter given."""
        return await self.collection.count_documents(filter_query or {})
