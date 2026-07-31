from uuid import uuid4
from pydantic import BaseModel, field_validator, Field
from typing import List, Dict, Optional
from .quiz_generator_schema import QuizzLevel

class UserResponse(BaseModel):
    """A single answer submitted by the student for one quiz question."""
    question_number:int = Field(description="1-indexed position of the question in the original quiz")
    selected_answer:str = Field(description="The letter of the option the student selected (a, b, c, d, ...), matching its position in that question's options list")

class QuizzAssessmentRequest(BaseModel):
    """
    Request to submit answers for a completed quiz.
    """
    quizz_id:str = Field(description="ID of the quizz returned when the questions were generated")
    responses:List[UserResponse] = Field(description="Student's answer for each question")

class QuizzSubmissionAck(BaseModel):
    """
    Returned immediately after submitting answers - grading runs in the
    background, so the report isn't ready yet at this point.
    """
    quizz_id:str = Field(description="ID of the quizz being graded")
    status:str = Field(description="Current grading status", default="grading")

class QuestionFeedback(BaseModel):
    """
    Per-question breakdown of correct vs submitted answer
    """
    question_number:int
    question_text:str
    correct_answer:str
    student_answer:str
    is_correct:bool

class ResourceReference(BaseModel):
    """
    A book/page resource for further learning
    """
    book_name:str
    page_number:Optional[list[int]] = None

class QuizzAssessmentPayload(BaseModel):
    """
    What the grading model actually needs to produce via output_schema.
    score/question_feedback/resources are computed in code from the stored
    session data, not by the model - it only needs to write the narrative.
    """
    strengths:List[str] = Field(description="What the student demonstrated understanding of")
    growth_areas:List[str] = Field(description="Where understanding needs improvement, framed constructively")
    current_understanding_level:str = Field(description="Narrative summary of the student's grasp of the topic")
    next_steps:List[str] = Field(description="What the student should focus on next")

class SourceChunk(BaseModel):
    """
    A retrieved chunk used to ground the generated quizz questions
    """
    book_name:Optional[str] = Field(description="Name of the book or syllabus", default=None)
    page_number:Optional[List[int]] = Field(description="Relevant page numbers", default=None)
    content:str = Field(description="The chunk's text content")
    similarity_score:float = Field(description="Retrieval similarity score")

class QuizzAssessmentReport(BaseModel):
    """
    Quizz assessment report
    """
    user_id:str = Field(description="User ID")
    quizz_id:str = Field(description="ID of the quizz this report is for")
    grade:str
    subject:str
    score:int
    total_questions:int
    quizz_level:Optional[QuizzLevel] = Field(description="Student choosen quizz level default to false if not provided", default=None)
    question_feedback:List[QuestionFeedback]
    strengths:List[str] = Field(description="What the student demonstrated understanding of")
    growth_areas:List[str] = Field(description="Where understanding needs improvement, framed constructively")
    current_understanding_level:str = Field(description="Narrative summary of the student's grasp of the topic")
    next_steps:List[str] = Field(description="What the student should focus on next")
    resources:List[ResourceReference] = Field(default_factory=list)
    graded_at:Optional[str] = Field(description="When this report was graded", default=None)

class QuizProgressSummary(BaseModel):
    started:int
    completed:int
    reports_generated:int
    reports:List[QuizzAssessmentReport] = Field(default_factory=list)
