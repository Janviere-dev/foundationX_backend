import json

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from db.repositories.base import BaseRepository
from db.redis.cache_student_profile import (
    cache_student_profile,
    get_cached_student_profile,
    invalidate_cached_student_profile,
    )
from schemas.user_schema import UpdateInformation
from datetime import date

from functools import lru_cache

class Auth:
    def __init__(self, security:HTTPBearer, db:BaseRepository):
        self.__security = security
        self.__db = db

    async def verify_credentials(self,
                                 credentials:HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """
        This function a user credential
        """
        token = credentials.credentials
        try:
            decode_token = auth.verify_id_token(token)
            return decode_token
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not authorized to access this ressource",
                headers={"WWW-Authenticate": "Bearer"},
            )

    async def create_new_user(self, user_credentials:dict):
        existing = await self.__db.find_by_id(doc_id=user_credentials["_id"])
        if existing:
            return {"status":True, "message":"User already exists", "data":existing}

        try:
            await self.__db.insert_one(document=user_credentials)
        except Exception as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to save a new user:\n {str(error)}"
            )

        return {
            "status":True,
            "message":"User saved successfully",
            "data":user_credentials
        }

    async def update_user_information(self, update_info:UpdateInformation, student_id:str, email_verified:bool):
        student_info = update_info.model_dump(mode="json")
        student_info["email_verified"] = email_verified

        try:
            update_student = await self.__db.update_one(doc_id=student_id, update=student_info)
        except Exception as error:
            print(error)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user info"
            )
        await invalidate_cached_student_profile(student_id)
        return {
            "status":True,
            "message":"Update OK",
            "data":{
                "user_id":student_id,
                "updated_info":update_info
            }
        }

    async def _fetch_profile(self, user_id:str):
        cached_profile = await get_cached_student_profile(user_id)
        if cached_profile is not None:
            return json.loads(cached_profile)

        document = await self.__db.find_by_id(doc_id=user_id)
        if document:
            await cache_student_profile(user_id=user_id, profile_json=json.dumps(document, default=str))
        return document

    async def check_user_exist_verify(self, user_id:str):
        check_user = await self._fetch_profile(user_id)
        if not check_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.Complete registration"
            )
        if not check_user.get("email_verified") or not check_user.get("onboarding_complete"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please complete your onboarding and ensure your email is verified"
            )
        return [str(check_user.get("user_id")),
                check_user.get("first_name"),
                check_user.get("grade"), check_user.get("goals")
                ]

    async def get_my_profile(self, user_id:str) -> dict:
        # No onboarding/email-verified gate here - the frontend calls this
        # specifically to find out whether onboarding is needed.
        profile = await self._fetch_profile(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.Complete registration"
            )
        return profile

    async def get_student_context(
            self,
            credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
            ) -> dict:
        decoded_token = await self.verify_credentials(credentials=credentials)
        user_id, first_name, grade, goals = await self.check_user_exist_verify(user_id=decoded_token["uid"])
        return {
            "user_id": user_id,
            "first_name": first_name,
            "grade": grade,
            "goals": goals,
            }

@lru_cache
def authentication():
    security = HTTPBearer()
    db = BaseRepository(collection_name="users")
    return Auth(security=security, db=db)
