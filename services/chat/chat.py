import logging
from datetime import datetime, timezone
from functools import lru_cache
from typing import List, Optional
from uuid import uuid4

from google.adk.tools import FunctionTool

from core.config import get_settings
from agents.rag_pipeline.retrieval.retriever import Retrieval
from agents.rag_pipeline.retrieval.init_sentence_transformamer import init_remote_embedder, init_qdrant_retriever
from agents.tools.learning_agent_tools import search_web_articles, search_web_videos

from agents.prompts.chat_prompt import instruction as chat_instruction

from agents.schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
    ChatTurn,
    ChatSessionSummary,
    ChatHistoryResponse,
    )
from db.repositories.chat_repository import ChatRepository
from services.chat.chat_helpers import (
    RECENT_TURNS,
    SUMMARY_EVERY_N_TURNS,
    build_chat_instruction,
    build_context,
    build_external_resources,
    build_history_block,
    document_to_source_chunk,
    run_chat_agent,
    run_summary_agent,
    )

logger = logging.getLogger(__name__)

chat_agent_tools = [
    FunctionTool(search_web_articles),
    FunctionTool(search_web_videos),
    ]


class ChatManagement:
    def __init__(self):
        self.retriever = Retrieval(
            embedder=init_remote_embedder(),
            retriver=init_qdrant_retriever(),
            )
        self.chat_repository = ChatRepository()

    async def send_message(self, request: ChatRequest) -> ChatResponse:
        """
        Send one chat turn. If session_id is omitted, starts a new session;
        otherwise continues an existing one, using its prior turns/summary
        as conversation context.
        """
        session = None
        if request.session_id:
            session = await self.chat_repository.get_session(request.session_id)
            if session is None or session.get("user_id") != request.user_id:
                raise ValueError(f"No chat session found for session_id={request.session_id}")

        session_id = request.session_id or str(uuid4())
        previous_messages = session.get("messages", []) if session else []
        previous_summary = session.get("summary") if session else None
        turn_count = session.get("turn_count", 0) if session else 0

        retrieval = await self.retriever.retrieve_chat_content(
            query=request.question,
            grade=request.grade,
            top_int=get_settings().TOP_K,
            )
        documents = retrieval["documents"]
        source_chunks = [document_to_source_chunk(document) for document in documents]

        instruction = build_chat_instruction(
            instruction=chat_instruction.format(grade=request.grade),
            chunk_context=build_context(source_chunks),
            summary=previous_summary,
            history_block=build_history_block(previous_messages[-RECENT_TURNS:]),
            )

        final_text, captured = await run_chat_agent(
            instruction=instruction,
            question=request.question,
            user_id=request.user_id,
            tools=chat_agent_tools,
            )

        external_sources = build_external_resources(request.question, captured)

        now = datetime.now(timezone.utc).isoformat()
        turn = turn_count + 1
        turn_record = {
            "turn": turn,
            "question": request.question,
            "ai_response": final_text,
            "sources": [chunk.model_dump(mode="json") for chunk in source_chunks],
            "external_sources": external_sources.model_dump(mode="json") if external_sources else None,
            "created_at": now,
            }

        summary = previous_summary
        if turn % SUMMARY_EVERY_N_TURNS == 0:
            summary = await run_summary_agent(
                grade=request.grade,
                messages=previous_messages + [turn_record],
                user_id=request.user_id,
                )

        if session is None:
            await self.chat_repository.create_session(
                session_id=session_id,
                document={
                    "user_id": request.user_id,
                    "grade": request.grade,
                    "messages": [turn_record],
                    "turn_count": turn,
                    "summary": summary,
                    "created_at": now,
                    "updated_at": now,
                    },
                )
        else:
            await self.chat_repository.append_turn(
                session_id=session_id,
                turn=turn_record,
                turn_count=turn,
                summary=summary,
                updated_at=now,
                )

        return ChatResponse(
            user_id=request.user_id,
            session_id=session_id,
            question=request.question,
            ai_response=final_text,
            summary=summary,
            turn=turn,
            sources=source_chunks,
            external_sources=external_sources,
            )

    async def list_sessions(self, user_id: str) -> List[ChatSessionSummary]:
        """List a user's chat sessions, most recently updated first."""
        documents = await self.chat_repository.list_sessions(user_id=user_id)
        return [
            ChatSessionSummary(
                session_id=str(document["_id"]),
                user_id=document["user_id"],
                grade=document["grade"],
                turn_count=document.get("turn_count", 0),
                last_question=document["messages"][-1]["question"] if document.get("messages") else "",
                summary=document.get("summary"),
                created_at=document["created_at"],
                updated_at=document["updated_at"],
                )
            for document in documents
            ]

    async def get_session(self, session_id: str, user_id: str) -> Optional[ChatHistoryResponse]:
        """Fetch a session's full turn history."""
        document = await self.chat_repository.get_session(session_id)
        if document is None or document.get("user_id") != user_id:
            return None
        return ChatHistoryResponse(
            session_id=str(document["_id"]),
            user_id=document["user_id"],
            grade=document["grade"],
            summary=document.get("summary"),
            turn_count=document.get("turn_count", 0),
            messages=[ChatTurn.model_validate(turn) for turn in document.get("messages", [])],
            created_at=document["created_at"],
            updated_at=document["updated_at"],
            )

    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Delete a chat session."""
        document = await self.chat_repository.get_session(session_id)
        if document is None or document.get("user_id") != user_id:
            return False
        return await self.chat_repository.delete_session(session_id)


@lru_cache
def get_chat_service() -> ChatManagement:
    return ChatManagement()
