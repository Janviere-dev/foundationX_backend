#!/usr/bin/env python3

from motor.motor_asyncio import AsyncIOMotorDatabase


async def ensure_indexes(db: AsyncIOMotorDatabase) -> None:
    """Create MongoDB indexes on application startup."""
    await db.documents.create_index([("course_id", 1)])
    await db.documents.create_index([("status", 1)])
