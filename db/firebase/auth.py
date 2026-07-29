from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import auth
from db.repositories.base import BaseRepository
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
        """
        This function creates a new user
        """
        try:
            new_user = await self.__db.insert_one(document=user_credentials)
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

    async def update_user_information(self, update_info:UpdateInformation, student_id:str):
        """
        This function update user information
        """
        student_info = update_info.model_dump(mode="json")

        try:
            update_student = await self.__db.update_one(doc_id=student_id, update=student_info)
        except Exception as error:
            print(error)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user info"
            )
        return {
            "status":True,
            "message":"Update OK",
            "data":{
                "user_id":student_id,
                "updated_info":update_info
            }
        }

@lru_cache
def authentication():
    security = HTTPBearer()
    db = BaseRepository(collection_name="users")
    return Auth(security=security, db=db)
