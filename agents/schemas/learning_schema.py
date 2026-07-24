#!/usr/bin/env python3

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator, AnyHttpUrl

class GenerateLearningContentRequest(BaseModel):
    """Base class for generating learning content"""
    learning_query:str = Field(description="Question to send to the learning agent")
    grade:str = Field(description="Student current grade eg.Senior 6")
    subject:str = Field(description="Subject the student need to learn eg.Calculus/Quadratic Equations")

class QuestionDetail(BaseModel):
    text:str = Field(description="The checkpoint question text")
    options:List[str] = Field(description="Multiple choice answer options")
    answer:str = Field(description="The correct answer, matching one of the options")

class ChunkDetail(BaseModel):
    chunk_content:str = Field(description="Chunk content")
    similarity_score:float = Field(description="Chunk similarity score")

class RetreivedChunks(BaseModel):
    course:str = Field(description="The student provided course")
    lessons:List[str] = Field(description="The different lessons taught")
    book_name:Optional[str] = Field(description="Name of the book or syllabus where the response came from")
    page_number:Optional[List[int]] = Field(description="The different page where the lessons came from")
    chunk_retrived:int = Field(description="Total number of chunks retrieved")
    chunk_detail:ChunkDetail

class Checkpoint_question(BaseModel):
    question:QuestionDetail

class ArticlesLink(BaseModel):
    article_title:str = Field(description="Name of the article")
    article_description:str = Field(description="Headline/description about the article")
    link:AnyHttpUrl = Field(description="Link of the article")

class VideoLink(BaseModel):
    video_title:str = Field(description="Name of the video")
    video_description:str = Field(description="Description of the video")
    link:AnyHttpUrl = Field(description="Link to the course video")

class External_ressources(BaseModel):
    """
    tavily result
    """
    query:str = Field(description="query value sent to Tavily")
    response:str = Field(description="Response from tavily")
    article_retrieved:bool = Field(description="True if external article was retrieved, False if not")
    video_retreieved:bool = Field(description="True if youtube video was retrieved else False")
    articles:Optional[List[ArticlesLink]] = Field(description="Articles retrieved", default=None)
    videos:Optional[List[VideoLink]] = Field(description="Youtube Videos retrieved", default=None)
    external_source_retrived:bool = Field(description="True if any external source else False")

class GenerateLearningResponse(BaseModel):
    """
    Base class for learning response
    """
    subject:str = Field(description="Learning subject")
    grade:str = Field(description="Student current grade")
    learning_plan:List[str] = Field(description="Steps by steps Lesson plan")
    learning_content:str = Field(description="Lesson content")
    checkpoints_questions_response:List[Checkpoint_question] = Field(description="Checkpoint questions")
    rag_enabled:bool = Field(description="True if chunks retrieved and False if not")
    retrival_details:List[RetreivedChunks]
    external_sources:Optional[External_ressources] = Field(description="External sources field", default=None)
