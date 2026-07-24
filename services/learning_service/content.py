#!/usr/bin/env python3

import uuid

from core.config import get_settings
from agents.adk.build import Agents
from agents.prompts.learning_prompt import learning_instruction, learning_prompt
from agents.rag_pipeline.retrieval.retriever import Retrieval
from agents.rag_pipeline.retrieval.init_sentence_transformamer import init_sentence_transformer, init_qdrant_retriever
from agents.schemas.learning_schema import GenerateLearningContentRequest, GenerateLearningResponse

async def get_content(request: GenerateLearningContentRequest) -> GenerateLearningResponse:
    retrieval = Retrieval(
        embedder=init_sentence_transformer(),
        retriver=init_qdrant_retriever(),
        )
    retrieved = await retrieval.retrieve_learning_content(
        query=request.learning_query,
        grade=request.grade,
        subject=request.subject,
        top_int=get_settings().TOP_K,
        )
    context = "\n\n---\n\n".join(document.content for document in retrieved["documents"])

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

    return GenerateLearningResponse.model_validate_json(result)
