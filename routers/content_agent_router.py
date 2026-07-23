#!/usr/bin/env python3

from fastapi.routing import APIRouter

router = APIRouter(
    prefix="/content",
    tags=["Content Routers"]
    )

@router.get("/")
async def test_router():
    return {
        "message":"Test Router"
    }
