import unittest
from types import SimpleNamespace
from unittest.mock import patch

from db.repositories.chat_repository import ChatRepository
from db.repositories.learning_content_repository import LearningContentRepository


class FakeAsyncCollection:
    def __init__(self, docs=None):
        self.documents = docs or {}

    async def find_one(self, filter_query):
        return self.documents.get(filter_query["_id"])

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


class RepositoryRetrievalTests(unittest.IsolatedAsyncioTestCase):
    async def test_chat_repository_lists_most_recent_sessions_first(self):
        fake_collection = FakeAsyncCollection(
            docs={
                "session-1": {
                    "_id": "session-1",
                    "user_id": "student-1",
                    "grade": "S3",
                    "messages": [{"question": "older question"}],
                    "turn_count": 1,
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                },
                "session-2": {
                    "_id": "session-2",
                    "user_id": "student-1",
                    "grade": "S3",
                    "messages": [{"question": "recent question"}],
                    "turn_count": 2,
                    "created_at": "2026-01-02T00:00:00+00:00",
                    "updated_at": "2026-01-02T00:00:00+00:00",
                },
            }
        )

        with patch("db.repositories.base.get_database", return_value={"chat_sessions": fake_collection}):
            repository = ChatRepository()
            sessions = await repository.list_sessions(user_id="student-1", limit=5)

        self.assertEqual([session["_id"] for session in sessions], ["session-2", "session-1"])

    async def test_learning_content_repository_returns_matching_content_by_id(self):
        fake_collection = FakeAsyncCollection(
            docs={
                "lesson-42": {
                    "_id": "lesson-42",
                    "user_id": "student-1",
                    "subject": "Mathematics",
                    "is_complete": False,
                }
            }
        )

        with patch("db.repositories.base.get_database", return_value={"learning_content": fake_collection}):
            repository = LearningContentRepository()
            content = await repository.get_content("lesson-42")

        self.assertEqual(content["subject"], "Mathematics")
        self.assertEqual(content["user_id"], "student-1")


if __name__ == "__main__":
    unittest.main()
