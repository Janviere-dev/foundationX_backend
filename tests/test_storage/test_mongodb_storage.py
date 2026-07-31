import unittest
from types import SimpleNamespace
from unittest.mock import patch

from db.repositories.base import BaseRepository
from db.repositories.chat_repository import ChatRepository
from db.repositories.learning_content_repository import LearningContentRepository


class FakeAsyncCollection:
    def __init__(self):
        self.documents = {}

    async def insert_one(self, document):
        self.documents[document["_id"]] = document
        return SimpleNamespace(inserted_id=document["_id"])

    async def find_one(self, filter_query):
        return self.documents.get(filter_query["_id"])

    async def update_one(self, filter_query, update):
        document = self.documents.get(filter_query["_id"])
        if document is None:
            return SimpleNamespace(modified_count=0)
        document.update(update.get("$set", {}))
        return SimpleNamespace(modified_count=1)

    async def delete_one(self, filter_query):
        document = self.documents.pop(filter_query["_id"], None)
        return SimpleNamespace(deleted_count=1 if document is not None else 0)

    def find(self, filter_query):
        filtered = [doc for doc in self.documents.values() if all(doc.get(k) == v for k, v in filter_query.items())]
        return FakeCursor(filtered)


class FakeCursor:
    def __init__(self, documents):
        self.documents = documents

    def sort(self, key, direction):
        self.documents = sorted(
            self.documents,
            key=lambda item: item.get(key, ""),
            reverse=direction == -1,
        )
        return self

    def limit(self, value):
        self.documents = self.documents[:value]
        return self

    async def to_list(self, length=None):
        return self.documents[:length] if length is not None else self.documents


class MongoStorageTests(unittest.IsolatedAsyncioTestCase):
    async def test_base_repository_insert_and_fetch_round_trip(self):
        fake_collection = FakeAsyncCollection()
        with patch("db.repositories.base.get_database", return_value={"users": fake_collection}):
            repository = BaseRepository(collection_name="users")
            inserted_id = await repository.insert_one({"_id": "user-123", "name": "Jane"})
            fetched = await repository.find_by_id("user-123")

        self.assertEqual(inserted_id, "user-123")
        self.assertEqual(fetched["name"], "Jane")

    async def test_chat_repository_create_and_delete_session(self):
        fake_collection = FakeAsyncCollection()
        with patch("db.repositories.base.get_database", return_value={"chat_sessions": fake_collection}):
            repository = ChatRepository()
            created = await repository.create_session(
                session_id="session-001",
                document={
                    "user_id": "student-1",
                    "grade": "S3",
                    "messages": [],
                    "turn_count": 0,
                    "summary": None,
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                },
            )
            deleted = await repository.delete_session("session-001")

        self.assertEqual(created, "session-001")
        self.assertTrue(deleted)

    async def test_learning_repository_mark_complete_updates_document(self):
        fake_collection = FakeAsyncCollection()
        fake_collection.documents["lesson-001"] = {
            "_id": "lesson-001",
            "user_id": "student-1",
            "is_complete": False,
        }

        with patch("db.repositories.base.get_database", return_value={"learning_contents": fake_collection}):
            repository = LearningContentRepository()
            updated = await repository.mark_complete("lesson-001")
            document = await repository.get_content("lesson-001")

        self.assertTrue(updated)
        self.assertTrue(document["is_complete"])


if __name__ == "__main__":
    unittest.main()
