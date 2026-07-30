#!/usr/bin/env python3

from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional

class UpdateInformation(BaseModel):
    """
    New User information during signup from Firebase/FireAuth
    """
    first_name:str = Field(description="User first name")
    last_name:str = Field(description="User last name")
    school:str = Field(description="Student school")
    grade:str = Field(description="Student grade")
    subjects:List[str] = Field(description="Student subjects")
    goals:List[str] = Field(description="Student choosen goals")
    gender:Optional[str] = Field(description="Student gender", default="Rather not say")
    date_of_birth:Optional[date] = Field(description="Student date of birth")
    updated_at:datetime = Field(description="Date and time user updated profile information")
    onboarding_complete:bool = Field(description="Onboarding status", default=True)
