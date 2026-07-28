#!/usr/bin/env python3

from fastapi import Depends, Header
from fastapi.routing import APIRouter
from datetime import datetime
from zoneinfo import ZoneInfo

from db.firebase.auth import authentication

router = APIRouter(
    prefix="/api/users",
    tags=["User Management"]
    )

@router.put("/extend_user_information")
async def extend_user_info():
    return "Success"

@router.post("/create_user")
async def get_all_users(user:dict = Depends(authentication().verify_credentials)):
    user_credential = {}
    user_credential["_id"] = user["uid"]
    user_credential["user_id"] = user.get("user_id", "")
    user_credential["email"] = user.get("email","")
    user_credential["email_verified"] = user.get("email_verified","")
    user_credential["sign_in_provider"] = user.get("firebase","").get("sign_in_provider", "")
    user_credential["time_added"] = datetime.now(ZoneInfo("Africa/Kigali"))
    return await authentication().create_new_user(user_credentials=user_credential)
