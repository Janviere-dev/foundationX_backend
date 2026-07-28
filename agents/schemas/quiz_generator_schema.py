#!/usr/bin/env python3

from typing import Optional, List, Dict
from enum import Enum
from pydantic import BaseModel, field_validator, Field
from .learning_schema import GenerateLearningContentRequest, QuestionDetail

class QuizzLevel(str, Enum):
    Easy = "easy"
    Medium = "medium"
    Hard = "hard"

class QuizzStatus(str, Enum):
    Started = "started"
    Completed = "completed"
    Abandoned = "abandoned"

class QuizzQuestionRequest(GenerateLearningContentRequest):
    number_question:int = Field(description="How many questions do the student want", ge=5, le=30)
    quizz_level:Optional[QuizzLevel] = Field(description="Quizz level default if provided, if not, fall back to agent owns generation", default=None)

class SourceChunk(BaseModel):
    """
    A retrieved chunk used to ground the generated quizz questions
    """
    book_name:Optional[str] = Field(description="Name of the book or syllabus", default=None)
    page_number:Optional[List[int]] = Field(description="Relevant page numbers", default=None)
    content:str = Field(description="The chunk's text content")
    similarity_score:float = Field(description="Retrieval similarity score")

class QuizzQuestionPayload(BaseModel):
    question_details:List[QuestionDetail] = Field(description="Each question details and response")

class QuizzQuestionResponse(BaseModel):
    """
    Quizz Question Response
    """
    user_id:str = Field(description="Current user ID who ask question")
    quizz_id:str = Field(description="ID of this quizz - same value previously called session_id")
    grade:str = Field(description="Current User grade")
    learning_query:str = Field(description="User provided learning subject")
    subject:str = Field(description="Subject tight with the user query")
    number_questions:int = Field(description="Number of question user asked", ge=5, le=30)
    quizz_level:Optional[QuizzLevel] = Field(description="Choosen level quizz questions default to agent generated quizz if not provided", default=None)
    question_details:List[QuestionDetail] = Field(description="Each question details and response")
    questions_sources:List[SourceChunk] = Field(description="Question sources")
    status:QuizzStatus = Field(description="Current quizz status", default=QuizzStatus.Started)
    created_at:Optional[str] = Field(description="When the quizz was generated", default=None)
    end_time:Optional[str] = Field(description="When the quizz was completed or abandoned", default=None)
