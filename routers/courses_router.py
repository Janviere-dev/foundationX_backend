#!/usr/bin/env python3

import logging
from typing import List, Dict, Any

from fastapi import HTTPException
from fastapi.routing import APIRouter

from services.courses.load_courses import get_courses_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/courses",
    tags=["Courses"]
    )

@router.get("/", response_model=List[Dict[str, Any]])
async def get_courses():
    try:
        return await get_courses_service().display_available_courses()
    except Exception:
        logger.exception("Failed to load courses from Qdrant")
        raise HTTPException(
            status_code=503,
            detail="Courses are temporarily unavailable.",
            )

