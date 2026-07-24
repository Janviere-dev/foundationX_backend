#!/usr/bin/env python3

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator

class GenerateLearningContentRequest(BaseModel):
    """Base class for generating learning content"""
    learning_query:str = Field(description="Question to send to the learning agent")
    grade:str = Field(description="Student current grade eg.Senior 6")
    subject:str = Field(description="Subject the student need to learn eg.Calculus/Quadratic Equations")

class Checkpoint_question(BaseModel):
    question:Dict[str,Any]

class GenerateLearningResponse(BaseModel):
    """
    Base class for learning response
    """
    subject:str = Field(description="Learning subject")
    grade:str = Field(description="Student current grade")
    learning_plan:List[str] = Field(description="Steps by steps Lesson plan")
    learning_content:str = Field(description="Lesson content")
    checkpoints_questions_response:List[Checkpoint_question] = Field(description="Checkpoint questions")
