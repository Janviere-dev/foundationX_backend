#!/usr/bin/env python3

import logging
from functools import lru_cache
from typing import Optional
from uuid import uuid4

from core.config import get_settings
from agents.rag_pipeline.retrieval.retriever import Retrieval
from agents.rag_pipeline.retrieval.init_sentence_transformamer import init_remote_embedder, init_qdrant_retriever

from agents.prompts.quiz_generator_prompt import quiz_question_instruction, quiz_question_prompt
from agents.prompts.quizz_grader_prompt import quiz_grader_instruction, quiz_grader_prompt
from agents.schemas.learning_schema import QuestionDetail
from agents.schemas.quiz_generator_schema import (
    QuizzQuestionRequest,
    QuizzQuestionResponse,
    QuizzQuestionPayload,
    SourceChunk,
    )
from agents.schemas.quizz_assessor_schema import (
    QuizzAssessmentRequest,
    QuizzAssessmentReport,
    QuizzAssessmentPayload,
    QuizzSubmissionAck,
    UserResponse,
    )
from db.repositories.quiz_repository import QuizSessionRepository
from db.repositories.quiz_report_repository import QuizReportRepository
from services.assessment.assessment_helpers import (
    document_to_source_chunk,
    build_context,
    with_context,
    run_agent,
    grade_answers,
    build_resources,
    build_quiz_results_summary,
    )

logger = logging.getLogger(__name__)

class Assessment:
    def __init__(self):
        self.retriever = Retrieval(
            embedder=init_remote_embedder(),
            retriver=init_qdrant_retriever()
        )
        self.quiz_repository = QuizSessionRepository()
        self.quiz_report_repository = QuizReportRepository()

    async def generate_questions(self, quizz_request:QuizzQuestionRequest) -> QuizzQuestionResponse:
        """
        This function generates quizz question. A student must finish
        (grade) their current quiz before starting a new one.
        """
        pending_session = await self.quiz_repository.find_incomplete_session(quizz_request.user_id)
        if pending_session is not None:
            raise ValueError(
                f"User {quizz_request.user_id} already has an incomplete quiz "
                f"(quizz_id={pending_session['_id']}) - finish and submit it before starting a new one."
                )

        quizz_id = str(uuid4())

        retrieval = await self.retriever.retrieve_learning_content(
            query=quizz_request.learning_query,
            grade=quizz_request.grade,
            subject=quizz_request.subject,
            top_int=get_settings().TOP_K,
            )

        source_chunks = [document_to_source_chunk(document) for document in retrieval["documents"]]

        instruction = quiz_question_instruction.format(
            grade=quizz_request.grade,
            subject=quizz_request.subject,
            number_questions=quizz_request.number_question,
            )
        instruction = with_context(instruction, build_context(source_chunks))

        result = await run_agent(
            instruction=instruction,
            prompt=quiz_question_prompt,
            agent_builder="quiz_llm",
            user_id=quizz_request.user_id,
            agent_name="quiz_generator_llm",
            )

        payload = QuizzQuestionPayload.model_validate_json(result)

        response = QuizzQuestionResponse(
            user_id=quizz_request.user_id,
            quizz_id=quizz_id,
            grade=quizz_request.grade,
            learning_query=quizz_request.learning_query,
            subject=quizz_request.subject,
            number_questions=len(payload.question_details),
            question_details=payload.question_details,
            questions_sources=source_chunks,
            complete=True,
            )

        await self.quiz_repository.create_session(
            quizz_id=quizz_id,
            document=response.model_dump(mode="json"),
            )

        return response

    async def submit_answers(self, assessment_request:QuizzAssessmentRequest) -> QuizzSubmissionAck:
        """
        Store the student's submitted answers. Grading itself runs
        separately as a background task (see grade_quiz) so this returns
        immediately instead of waiting on the LLM call.
        """
        session = await self.quiz_repository.get_session(assessment_request.quizz_id)
        if session is None:
            raise ValueError(f"No quiz found for quizz_id={assessment_request.quizz_id}")

        await self.quiz_repository.save_responses(
            quizz_id=assessment_request.quizz_id,
            responses=[response.model_dump(mode="json") for response in assessment_request.responses],
            )

        return QuizzSubmissionAck(quizz_id=assessment_request.quizz_id, status="grading")

    async def grade_quiz(self, quizz_id:str) -> None:
        """
        Runs as a background task after answers are submitted - grades the
        quiz and saves the report. There's no HTTP request left to report
        errors to by the time this runs, so failures are logged, not
        raised; the client polls get_report and will just see it stay
        unready if this fails.
        """
        try:
            session = await self.quiz_repository.get_session(quizz_id)
            if session is None:
                logger.error("grade_quiz: no quiz found for quizz_id=%s", quizz_id)
                return

            responses = [UserResponse.model_validate(response) for response in session.get("responses", [])]
            question_details = [QuestionDetail.model_validate(question) for question in session["question_details"]]
            source_chunks = [SourceChunk.model_validate(chunk) for chunk in session.get("questions_sources", [])]

            score, question_feedback = grade_answers(question_details, responses)
            resources = build_resources(source_chunks)

            context = f"{build_context(source_chunks)}\n\nQuiz results:\n{build_quiz_results_summary(question_feedback)}"
            instruction = quiz_grader_instruction.format(grade=session["grade"], subject=session["subject"])
            instruction = with_context(instruction, context)

            result = await run_agent(
                instruction=instruction,
                prompt=quiz_grader_prompt,
                agent_builder="quiz_grader_llm",
                user_id=session["user_id"],
                agent_name="quiz_grader_llm",
                )

            payload = QuizzAssessmentPayload.model_validate_json(result)

            report = QuizzAssessmentReport(
                user_id=session["user_id"],
                quizz_id=quizz_id,
                grade=session["grade"],
                subject=session["subject"],
                score=score,
                total_questions=len(question_details),
                question_feedback=question_feedback,
                strengths=payload.strengths,
                growth_areas=payload.growth_areas,
                current_understanding_level=payload.current_understanding_level,
                next_steps=payload.next_steps,
                resources=resources,
                )

            await self.quiz_report_repository.save_report(
                quizz_id=quizz_id,
                report=report.model_dump(mode="json"),
                )
            await self.quiz_repository.mark_graded(quizz_id=quizz_id)
        except Exception:
            logger.exception("grade_quiz failed for quizz_id=%s", quizz_id)

    async def get_report(self, quizz_id:str, user_id:str) -> Optional[QuizzAssessmentReport]:
        """
        Fetch a previously graded report. Returns None if the quiz doesn't
        exist, doesn't belong to this user, or hasn't finished grading yet.
        """
        session = await self.quiz_repository.get_session(quizz_id)
        if session is None or session.get("user_id") != user_id:
            return None
        report = await self.quiz_report_repository.get_report(quizz_id)
        if report is None:
            return None
        return QuizzAssessmentReport.model_validate(report)


@lru_cache
def get_assessment_service() -> Assessment:
    return Assessment()
