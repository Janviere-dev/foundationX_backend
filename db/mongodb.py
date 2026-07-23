#!/usr/bin/env python3

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from core.config import get_settings
import logging

logger = logging.getLogger(__name__)

settings = get_settings()

class MongoDB:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

mongo_db = MongoDB()

async def connect_to_mongo():
    logger.info("Connecting to MongoDB...")

    mongo_db.client = AsyncIOMotorClient(settings.MONGODB_URI)
    mongo_db.db = mongo_db.client[settings.MONGO_DB_NAME]

    # Optional: test connection
    await mongo_db.client.admin.command("ping")

    logger.info("MongoDB connection established")

async def close_mongo_connection():
    logger.info("Closing MongoDB connection...")

    if mongo_db.client:
        mongo_db.client.close()

    logger.info("MongoDB connection closed")

def get_database() -> AsyncIOMotorDatabase:
    return mongo_db.db
