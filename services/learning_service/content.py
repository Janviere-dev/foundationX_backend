#!/usr/bin/env python3

import uuid

from core.config import get_settings
from agents.adk.build import Agents
from agents.prompts.learning_prompt import learning_instruction, learning_prompt
from agents.rag_pipeline.retrieval.retriever import Retrieval
from agents.rag_pipeline.retrieval.init_sentence_transformamer import init_remote_embedder, init_qdrant_retriever
from agents.schemas.learning_schema import (
    GenerateLearningContentRequest,
    GenerateLearningResponse,
    RetreivedChunks,
    ChunkDetail,
    )

async def get_content(request: GenerateLearningContentRequest) -> GenerateLearningResponse:
    retrieval = Retrieval(
        embedder=init_remote_embedder(),
        retriver=init_qdrant_retriever(),
        )
    retrieved = await retrieval.retrieve_learning_content(
        query=request.learning_query,
        grade=request.grade,
        subject=request.subject,
        top_int=get_settings().TOP_K,
        )
    documents = retrieved["documents"]
    context = "\n\n---\n\n".join(document.content for document in documents)

    instruction = learning_instruction.format(
        grade=request.grade,
        subject=request.subject,
        learning_query=request.learning_query,
        )
    instruction = f"Context:\n{context}\n\n{instruction}"

    agent = Agents(instructions=instruction, prompt=learning_prompt)
    result = await agent.run(
        user_id=str(uuid.uuid4()),
        agent_name="learning_llm",
        )

    response = GenerateLearningResponse.model_validate_json(result)

    # The model never sees document.meta (only the raw chunk text), so it
    # can't reliably report book_name/page_number/similarity_score itself -
    # replace its guess with the real retrieval data we already have.
    response.rag_enabled = bool(documents)
    response.retrival_details = [
        RetreivedChunks(
            course=request.subject,
            lessons=[request.learning_query],
            book_name=document.meta.get("file_name"),
            page_number=[document.meta["page_number"]] if document.meta.get("page_number") is not None else None,
            chunk_retrived=len(documents),
            chunk_detail=ChunkDetail(
                chunk_content=document.content,
                similarity_score=document.score,
                ),
            )
        for document in documents
        ]

    return response
