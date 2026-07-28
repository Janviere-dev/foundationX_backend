#!/usr/bin/env python3

from typing import List

from agents.adk.build import Agents
from agents.schemas.learning_schema import RetreivedChunks, ChunkDetail


def build_context(documents: List) -> str:
    """Join retrieved document contents into a single context block."""
    return "\n\n---\n\n".join(document.content for document in documents)


def with_context(instruction: str, context: str) -> str:
    """Prepend a context block to an agent instruction."""
    return f"Context:\n{context}\n\n{instruction}"


async def run_agent(
        instruction: str,
        prompt: str,
        user_id: str,
        agent_name: str,
        agent_builder: str = "learning_llm",
        ) -> str:
    """Build and run an agent, returning its raw text/JSON result."""
    agent = Agents(instructions=instruction, prompt=prompt, agent_builder=agent_builder)
    return await agent.run(user_id=user_id, agent_name=agent_name)


def document_to_retrieved_chunk(document, subject: str, learning_query: str, total_retrieved: int) -> RetreivedChunks:
    """Build a RetreivedChunks entry from a retrieved Haystack Document."""
    return RetreivedChunks(
        course=subject,
        lessons=[learning_query],
        book_name=document.meta.get("file_name"),
        page_number=[document.meta["page_number"]] if document.meta.get("page_number") is not None else None,
        chunk_retrived=total_retrieved,
        chunk_detail=ChunkDetail(
            chunk_content=document.content,
            similarity_score=document.score,
            ),
        )
