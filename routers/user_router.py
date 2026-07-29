#!/usr/bin/env python3

from fastapi import Depends, Header
from fastapi.routing import APIRouter
from datetime import datetime
from zoneinfo import ZoneInfo

from db.firebase.auth import authentication
from schemas.user_schema import UpdateInformation

router = APIRouter(
    prefix="/api/users",
    tags=["User Management"]
    )

@router.post("/create_user")
async def create_user(user:dict = Depends(authentication().verify_credentials)):
    user_credential = {}
    user_credential["_id"] = user["uid"]
    user_credential["user_id"] = user.get("user_id", "")
    user_credential["email"] = user.get("email","")
    user_credential["email_verified"] = user.get("email_verified","")
    user_credential["sign_in_provider"] = user.get("firebase","").get("sign_in_provider", "")
    user_credential["onboarding_complete"] = False
    user_credential["time_added"] = datetime.now(ZoneInfo("Africa/Kigali"))
    return await authentication().create_new_user(user_credentials=user_credential)

@router.put("/extend_info")
async def extend_user_info(
    update_info:UpdateInformation,
    authorization:dict = Depends(authentication().verify_credentials),
    ):
    user_id = authorization["uid"]
    return await authentication().update_user_information(
        update_info=update_info,
        student_id=user_id
        )
