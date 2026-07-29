#!/usr/bin/env python3

import logging
from typing import List, Dict, Any

from fastapi import Depends, HTTPException
from fastapi.routing import APIRouter

from services.courses.load_courses import get_courses_service
from db.firebase.auth import authentication

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/courses",
    tags=["Courses"]
    )

@router.get("/", response_model=List[Dict[str, Any]])
async def get_courses(credentials:dict = Depends(authentication().verify_credentials)):
    try:
        return await get_courses_service().display_available_courses()
    except Exception:
        logger.exception("Failed to load courses from Qdrant")
        raise HTTPException(
            status_code=503,
            detail="Courses are temporarily unavailable.",
            )

