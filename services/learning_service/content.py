#!/usr/bin/env python3

import uuid
from functools import lru_cache

from core.config import get_settings
from agents.prompts.learning_prompt import learning_instruction, learning_prompt
from agents.rag_pipeline.retrieval.retriever import Retrieval
from agents.rag_pipeline.retrieval.init_sentence_transformamer import init_remote_embedder, init_qdrant_retriever
from agents.schemas.learning_schema import GenerateLearningContentRequest, GenerateLearningResponse
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

    async def get_content(self, request: GenerateLearningContentRequest) -> GenerateLearningResponse:
        retrieved = await self.retriever.retrieve_learning_content(
            query=request.learning_query,
            grade=request.grade,
            subject=request.subject,
            top_int=get_settings().TOP_K,
            )
        documents = retrieved["documents"]

        instruction = learning_instruction.format(
            grade=request.grade,
            subject=request.subject,
            learning_query=request.learning_query,
            )
        instruction = with_context(instruction, build_context(documents))

        result = await run_agent(
            instruction=instruction,
            prompt=learning_prompt,
            user_id=str(uuid.uuid4()),
            agent_name="learning_llm",
            )

        response = GenerateLearningResponse.model_validate_json(result)

        response.rag_enabled = bool(documents)
        response.external_sources = None
        response.retrival_details = [
            document_to_retrieved_chunk(
                document,
                subject=request.subject,
                learning_query=request.learning_query,
                total_retrieved=len(documents),
                )
            for document in documents
            ]

        return response


@lru_cache
def get_learning_content_service() -> LearningContent:
    return LearningContent()
