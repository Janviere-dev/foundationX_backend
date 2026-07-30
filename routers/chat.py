#!/usr/bin/env python3

import logging

import openai
from fastapi import HTTPException, Depends
from fastapi.routing import APIRouter

from agents.schemas.chat_schema import (
    ChatRequest,
    ChatResponse,
    ChatSessionSummary,
    ChatHistoryResponse,
    )

from services.chat.chat import get_chat_service
from db.firebase.auth import authentication

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/chat",
    tags=["Chat With Learning Agent bot"]
    )

@router.get("/")
async def welcome():
    return {
        "message":"Welcome to chatbot"
    }

@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    student:dict = Depends(authentication().get_student_context),
    ):
    try:
        return await get_chat_service().send_message(request=request, student=student)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except openai.APIError:
        raise HTTPException(
            status_code=503,
            detail="Chat is temporarily unavailable, please try again shortly.",
            )
    except Exception:
        logger.exception("Chat agent failed unexpectedly")
        raise HTTPException(
            status_code=503,
            detail="Chat agent not available.",
            )

@router.get("/sessions", response_model=list[ChatSessionSummary])
async def list_sessions(student:dict = Depends(authentication().get_student_context)):
    return await get_chat_service().list_sessions(user_id=student["user_id"])

@router.get("/{session_id}", response_model=ChatHistoryResponse)
async def get_session(session_id: str, student:dict = Depends(authentication().get_student_context)):
    response = await get_chat_service().get_session(session_id=session_id, user_id=student["user_id"])
    if response is None:
        raise HTTPException(
            status_code=404,
            detail="Chat session not found, or does not belong to this user.",
            )
    return response

@router.delete("/{session_id}")
async def delete_session(session_id: str, student:dict = Depends(authentication().get_student_context)):
    deleted = await get_chat_service().delete_session(session_id=session_id, user_id=student["user_id"])
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Chat session not found, or does not belong to this user.",
            )
    return {"session_id": session_id, "deleted": True}
