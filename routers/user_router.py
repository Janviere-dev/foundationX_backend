#!/usr/bin/env python3

from fastapi.routing import APIRouter

router = APIRouter(
    prefix="/api/users"
    )

@router.post("/add_user")
async def create_new_user():
    return "Success"

@router.put("/extend_user_information")
async def extend_user_info():
    return "Success"

@router.get("/all_users")
async def get_all_users():
    return "success"
