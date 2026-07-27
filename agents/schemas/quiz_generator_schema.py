#!/usr/bin/env python3

from typing import Optional, List, Dict
from pydantic import BaseModel, field_validator, Field
from .learning_schema import GenerateLearningContentRequest, QuestionDetail

class QuizzQuestionRequest(GenerateLearningContentRequest):
    """
    Quizz base request. session_id is intentionally not part of the request -
    it's server-generated per quiz so it can never collide, and only ever
    goes out in the response.
    """
    user_id:str = Field(description="User asking question ID")
    number_question:int = Field(description="How many questions do the student want", ge=5, le=30)

class SourceChunk(BaseModel):
    """
    A retrieved chunk used to ground the generated quizz questions
    """
    book_name:Optional[str] = Field(description="Name of the book or syllabus", default=None)
    page_number:Optional[List[int]] = Field(description="Relevant page numbers", default=None)
    content:str = Field(description="The chunk's text content")
    similarity_score:float = Field(description="Retrieval similarity score")

class QuizzQuestionPayload(BaseModel):
    """
    What the model actually needs to produce via output_schema.
    user_id/session_id/grade/subject/learning_query are already known from
    the request, and number_questions/complete are derived in code from
    len(question_details) - the model only needs to produce the questions.
    """
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
    question_details:List[QuestionDetail] = Field(description="Each question details and response")
    questions_sources:List[SourceChunk] = Field(description="Question sources")
    complete:bool = Field(description="True if quizz completed and False if not", default=True)
