#!/usr/bin/env python3

import uuid
from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional

from core.config import get_settings
from agents.prompts.learning_prompt import learning_instruction, learning_prompt
from agents.prompts.personalization import format_first_name, format_goals
from agents.rag_pipeline.retrieval.retriever import Retrieval
from agents.rag_pipeline.retrieval.init_sentence_transformamer import init_remote_embedder, init_qdrant_retriever
from agents.schemas.learning_schema import (
    GenerateLearningContentRequest,
    GenerateLearningResponse,
    LearningResponsePayload,
    LessonProgressSummary,
    )
from db.repositories.learning_content_repository import LearningContentRepository
from db.repositories.progress_repository import ProgressRepository
from db.redis.save_generated_learning_content import (
    cache_learning_content,
    get_cached_learning_content,
    cache_content_lookup,
    get_cached_content_id,
    )
from services.learning_service.helper_learning_service import (
    build_context,
    with_context,
    run_agent,
    document_to_retrieved_chunk,
    )

class LearningContent:
    def __init__(self):
        self.retriever = Retrieval(
            embedder=init_remote_embedder(),
            retriver=init_qdrant_retriever(),
            )
        self.content_repository = LearningContentRepository()
        self.progress_repository = ProgressRepository()

    async def get_content(self, request: GenerateLearningContentRequest, student: dict) -> GenerateLearningResponse:
        existing_content_id = await get_cached_content_id(
            user_id=student["user_id"],
            subject=request.subject,
            learning_query=request.learning_query,
            grade=student["grade"],
            )
        if existing_content_id:
            existing = await self.get_saved_content(content_id=existing_content_id, user_id=student["user_id"])
            if existing:
                return existing

        retrieved = await self.retriever.retrieve_learning_content(
            query=request.learning_query,
            grade=student["grade"],
            subject=request.subject,
            top_int=get_settings().TOP_K,
            )
        documents = retrieved["documents"]

        instruction = learning_instruction.format(
            grade=student["grade"],
            subject=request.subject,
            learning_query=request.learning_query,
            first_name=format_first_name(student.get("first_name")),
            goals=format_goals(student.get("goals")),
            )
        instruction = with_context(instruction, build_context(documents))

        result = await run_agent(
            instruction=instruction,
            prompt=learning_prompt,
            user_id=student["user_id"],
            agent_name="learning_llm",
            )

        payload = LearningResponsePayload.model_validate_json(result)

        response = GenerateLearningResponse(
            content_id=str(uuid.uuid4()),
            user_id=student["user_id"],
            subject=request.subject,
            grade=student["grade"],
            learning_plan=payload.learning_plan,
            learning_content=payload.learning_content,
            key_points=payload.key_points,
            checkpoints_questions_response=payload.checkpoints_questions_response,
            rag_enabled=bool(documents),
            external_sources=None,
            is_complete=False,
            created_at=datetime.now(timezone.utc).isoformat(),
            retrival_details=[
                document_to_retrieved_chunk(
                    document,
                    subject=request.subject,
                    learning_query=request.learning_query,
                    total_retrieved=len(documents),
                    )
                for document in documents
                ],
            )

        await self.content_repository.create_content(
            content_id=response.content_id,
            document=response.model_dump(mode="json"),
            )
        await cache_learning_content(content_id=response.content_id, document_json=response.model_dump_json())
        await cache_content_lookup(
            user_id=student["user_id"],
            subject=request.subject,
            learning_query=request.learning_query,
            grade=student["grade"],
            content_id=response.content_id,
            )
        await self.progress_repository.start_lesson(
            user_id=student["user_id"],
            subject=request.subject,
            topic=request.learning_query,
            content_id=response.content_id,
            )

        return response

    async def get_saved_content(self, content_id: str, user_id: str) -> Optional[GenerateLearningResponse]:
        """Cache-aside read: check Redis first, fall back to MongoDB (the
        permanent copy) on a miss and repopulate the cache. A lesson never
        disappears just because the cache expired or was evicted."""
        cached_json = await get_cached_learning_content(content_id)
        if cached_json is not None:
            response = GenerateLearningResponse.model_validate_json(cached_json)
            if response.user_id != user_id:
                return None
            return response

        document = await self.content_repository.get_content(content_id)
        if document is None or document.get("user_id") != user_id:
            return None

        response = GenerateLearningResponse.model_validate(document)
        await cache_learning_content(content_id=content_id, document_json=response.model_dump_json())
        return response

    async def mark_complete(self, content_id: str, user_id: str) -> Optional[GenerateLearningResponse]:
        """Mark a lesson as completed by the student. Updates MongoDB (the
        source of truth) and refreshes the cache so it doesn't keep
        serving a stale is_complete=False copy."""
        document = await self.content_repository.get_content(content_id)
        if document is None or document.get("user_id") != user_id:
            return None

        await self.content_repository.mark_complete(content_id=content_id)
        await self.progress_repository.complete_lesson(content_id=content_id)

        response = GenerateLearningResponse.model_validate(document)
        response.is_complete = True
        await cache_learning_content(content_id=content_id, document_json=response.model_dump_json())

        return response

    async def get_lesson_progress(self, user_id: str) -> LessonProgressSummary:
        counts = await self.progress_repository.count_progress(user_id)
        return LessonProgressSummary(**counts)


@lru_cache
def get_learning_content_service() -> LearningContent:
    return LearningContent()
