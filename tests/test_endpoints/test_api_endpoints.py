import unittest
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from db.firebase.auth import authentication
from routers.chat import router as chat_router
from routers.content_agent_router import router as content_router


class FakeChatService:
    def __init__(self):
        self.send_message = AsyncMock(
            return_value={
                "user_id": "student-1",
                "session_id": "session-123",
                "question": "What is algebra?",
                "ai_response": "Algebra is the branch of math dealing with symbols and rules.",
                "summary": None,
                "turn": 1,
                "sources": [],
                "external_sources": None,
            }
        )
        self.list_sessions = AsyncMock(return_value=[])
        self.get_session = AsyncMock(return_value=None)
        self.delete_session = AsyncMock(return_value=False)


class FakeLearningService:
    def __init__(self):
        self.get_content = AsyncMock(return_value={
            "content_id": "lesson-123",
            "user_id": "student-1",
            "subject": "Mathematics",
            "grade": "S3",
            "learning_plan": ["Learn the basics"],
            "learning_content": "Lesson body",
            "key_points": ["Key idea"],
            "checkpoints_questions_response": [],
            "rag_enabled": False,
            "retrival_details": [],
            "external_sources": None,
            "is_complete": False,
            "created_at": "2026-01-01T00:00:00+00:00",
        })
        self.get_lesson_progress = AsyncMock(return_value={"started": 1, "completed": 0, "in_progress": 1})
        self.get_saved_content = AsyncMock(return_value=None)
        self.mark_complete = AsyncMock(return_value=None)


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(chat_router)
        self.app.include_router(content_router)

        async def fake_student_context():
            return {"user_id": "student-1", "first_name": "Aline", "grade": "S3", "goals": ["math"]}

        self.app.dependency_overrides = {}
        self.app.dependency_overrides[authentication().get_student_context] = fake_student_context

        self.client = TestClient(self.app)

    def test_chat_welcome_endpoint(self):
        response = self.client.get("/api/chat/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Welcome to chatbot")

    @patch("routers.chat.get_chat_service", return_value=FakeChatService())
    def test_chat_post_endpoint_returns_ai_response(self, _mock_service):
        response = self.client.post(
            "/api/chat/",
            json={"question": "What is algebra?"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["session_id"], "session-123")
        self.assertEqual(response.json()["question"], "What is algebra?")

    @patch("routers.content_agent_router.get_learning_content_service", return_value=FakeLearningService())
    def test_content_progress_endpoint_uses_service(self, _mock_service):
        response = self.client.get("/api/content/progress")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["started"], 1)
        self.assertEqual(response.json()["completed"], 0)


if __name__ == "__main__":
    unittest.main()
