#!/usr/bin/env python3

import openai
from fastapi import HTTPException
from fastapi.routing import APIRouter
from agents.schemas.learning_schema import GenerateLearningContentRequest, GenerateLearningResponse
from services.learning_service.content import get_content

router = APIRouter(
    prefix="/content",
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
        return await get_content(request=generate_request)
    except openai.APIError:
        raise HTTPException(
            status_code=503,
            detail="Learning content generation is temporarily unavailable, please try again shortly.",
            )
