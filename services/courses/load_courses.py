#!/usr/bin/env python3

import asyncio
from functools import lru_cache
from typing import List

from qdrant_client import AsyncQdrantClient
from db.mongodb import connect_to_mongo, close_mongo_connection
from db.repositories.base import BaseRepository
from core.config import get_settings
from .subject_list import get_all_subjects

class Courses:
    def __init__(self, client: AsyncQdrantClient, base:BaseRepository):
        self.__client = client
        self.__db = base

    async def load_courses(self) -> List[str]:
        """
        load all courses stored in qdrant
        """
        settings = get_settings()
        subjects: set[str] = set()
        offset = None

        while True:
            points, offset = await self.__client.scroll(
                collection_name=settings.QDRANT_COLLECTION_NAME,
                limit=1000,
                offset=offset,
                with_payload=["meta.subject"],
                with_vectors=False,
                )
            for point in points:
                subject = point.payload.get("meta", {}).get("subject")
                if subject:
                    subjects.add(subject)
            if offset is None:
                break
        print("Loading course complete...")
        foundation_x_courses = {
            "courses":sorted(subjects)
        }
        print("saving to mongodb...")
        return await self.__db.insert_one(document=foundation_x_courses)

    async def courses_breakdown(self):
        """
        Batch insert all 18 subjects, each with their topics/subtopics, into mongodb
        """
        documents = get_all_subjects()
        print(f"saving {len(documents)} courses to mongodb...")
        return await self.__db.collection.insert_many(documents)

    async def display_available_courses(self):
        """
        Load all available courses/topics/subtopics from mongodb
        """
        all_courses = await self.__db.find_many(filter_query={})
        for courses in all_courses:
            courses["_id"] = str(courses["_id"])
        return all_courses

@lru_cache
def get_courses_service() -> Courses:
    settings = get_settings()
    client = AsyncQdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    base = BaseRepository(collection_name="courses_breakdown_plan")
    return Courses(client=client, base=base)

async def main():
    await connect_to_mongo()
    try:
        return await get_courses_service().courses_breakdown()
    finally:
        await close_mongo_connection()

if __name__ == "__main__":
    print(asyncio.run(main()))
