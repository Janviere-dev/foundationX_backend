#!/usr/bin/env python3

import logging

import openai
from fastapi import BackgroundTasks, HTTPException
from fastapi.routing import APIRouter
from services.assessment.assessment import get_assessment_service, IncompleteQuizError
from agents.schemas.quiz_generator_schema import QuizzQuestionRequest, QuizzQuestionResponse
from agents.schemas.quizz_assessor_schema import QuizzAssessmentRequest, QuizzAssessmentReport, QuizzSubmissionAck

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/assessment"
    )

@router.post("/quizz", response_model=QuizzQuestionResponse)
async def generate_quizz(
    quizz_payload:QuizzQuestionRequest
    ) -> QuizzQuestionResponse:
    try:
        return await get_assessment_service().generate_questions(
            quizz_request=quizz_payload
            )
    except IncompleteQuizError as error:
        # the student already has an incomplete quiz pending - hand back
        # the full saved quiz so the client can resume it directly
        raise HTTPException(status_code=409, detail=error.quizz_response.model_dump(mode="json"))
    except openai.APIError:
        raise HTTPException(
            status_code=503,
            detail="Quiz generation is temporarily unavailable, please try again shortly.",
            )
    except Exception:
        logger.exception("Quiz generation failed unexpectedly")
        raise HTTPException(status_code=503, detail="Quiz agent not available.")

@router.post("/quizz/submit", response_model=QuizzSubmissionAck, status_code=202)
async def submit_quizz_answers(
    assessment_payload:QuizzAssessmentRequest,
    background_tasks:BackgroundTasks,
    ) -> QuizzSubmissionAck:
    service = get_assessment_service()
    try:
        ack = await service.submit_answers(assessment_request=assessment_payload)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except Exception:
        logger.exception("Submitting quiz answers failed unexpectedly")
        raise HTTPException(status_code=503, detail="Quiz agent not available.")

    background_tasks.add_task(service.grade_quiz, quizz_id=assessment_payload.quizz_id)
    return ack

@router.get("/quizz/report/{quizz_id}", response_model=QuizzAssessmentReport)
async def get_quizz_report(
    quizz_id:str,
    user_id:str,
    ) -> QuizzAssessmentReport:
    report = await get_assessment_service().get_report(quizz_id=quizz_id, user_id=user_id)
    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Report not found - it may not exist, may not belong to this user, or grading may still be in progress.",
            )
    return report
