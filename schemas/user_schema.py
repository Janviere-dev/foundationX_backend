#!/usr/bin/env python3

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List

class NewUser(BaseModel):
    """
    New User information during signup from Firebase/FireAuth
    """
    user_id:str
    email_address:EmailStr
    created_at:datetime
