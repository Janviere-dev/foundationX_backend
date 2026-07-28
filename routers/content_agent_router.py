#!/usr/bin/env python3

import logging

import openai
from fastapi import HTTPException
from fastapi.routing import APIRouter
from agents.schemas.learning_schema import GenerateLearningContentRequest, GenerateLearningResponse
from services.learning_service.content import get_learning_content_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/content",
    tags=["Content Routers"]
    )

@router.get("/")
async def test_router():
    return {
        "message":"Test Router"
    }

@router.post("/", response_model=GenerateLearningResponse)
async def generate_lesson(
    generate_request:GenerateLearningContentRequest
):
    try:
        return await get_learning_content_service().get_content(request=generate_request)
    except openai.APIError:
        raise HTTPException(
            status_code=503,
            detail="Learning content generation is temporarily unavailable, please try again shortly.",
            )
    except Exception:
        logger.exception("Learning agent failed unexpectedly")
        raise HTTPException(
            status_code=503,
            detail="Learning agent not available.",
            )

@router.get("/{content_id}", response_model=GenerateLearningResponse)
async def get_lesson(
    content_id:str,
    user_id:str,
    ) -> GenerateLearningResponse:
    response = await get_learning_content_service().get_saved_content(content_id=content_id, user_id=user_id)
    if response is None:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found, or does not belong to this user.",
            )
    return response

@router.patch("/{content_id}/complete", response_model=GenerateLearningResponse)
async def complete_lesson(
    content_id:str,
    user_id:str,
    ) -> GenerateLearningResponse:
    response = await get_learning_content_service().mark_complete(content_id=content_id, user_id=user_id)
    if response is None:
        raise HTTPException(
            status_code=404,
            detail="Lesson not found, or does not belong to this user.",
            )
    return response
