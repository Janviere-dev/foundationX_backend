#!/usr/bin/env python3

from typing import List, Tuple

from agents.adk.build import Agents
from agents.schemas.learning_schema import QuestionDetail
from agents.schemas.quiz_generator_schema import SourceChunk
from agents.schemas.quizz_assessor_schema import QuestionFeedback, ResourceReference, UserResponse


def document_to_source_chunk(document) -> SourceChunk:
    """Build a SourceChunk from a retrieved Haystack Document."""
    return SourceChunk(
        book_name=document.meta.get("file_name"),
        page_number=[document.meta["page_number"]] if document.meta.get("page_number") is not None else None,
        content=document.content,
        similarity_score=document.score,
        )


def build_context(source_chunks: List[SourceChunk]) -> str:
    """Join source chunk contents into a single context block."""
    return "\n\n---\n\n".join(chunk.content for chunk in source_chunks)


def with_context(instruction: str, context: str) -> str:
    """Prepend a context block to an agent instruction."""
    return f"Context:\n{context}\n\n{instruction}"


async def run_agent(instruction: str, prompt: str, agent_builder: str, user_id: str, agent_name: str) -> str:
    """Build and run an agent, returning its raw text/JSON result."""
    agent = Agents(instructions=instruction, prompt=prompt, agent_builder=agent_builder)
    return await agent.run(user_id=user_id, agent_name=agent_name)


def resolve_option_letter(selected_answer: str, options: List[str]) -> str:
    """Resolve a submitted option letter (a/b/c/d/...) to that option's full
    text, so it can be compared against QuestionDetail.answer (which is
    always the full option text). Options are positional: options[0] is
    "a", options[1] is "b", and so on. Anything that isn't a single letter
    in range is returned unchanged (e.g. if a client ever sends the full
    text directly instead of a letter)."""
    letter = selected_answer.strip().lower()
    if len(letter) == 1 and letter.isalpha():
        index = ord(letter) - ord("a")
        if 0 <= index < len(options):
            return options[index]
    return selected_answer


def grade_answers(
        question_details: List[QuestionDetail],
        responses: List[UserResponse],
        ) -> Tuple[int, List[QuestionFeedback]]:
    """Compare submitted answers against correct answers. question_number is
    1-indexed, matching the question's position in the original quiz."""
    answers_by_question = {response.question_number: response.selected_answer for response in responses}
    question_feedback = []
    score = 0
    for index, question in enumerate(question_details, start=1):
        raw_answer = answers_by_question.get(index, "")
        student_answer = resolve_option_letter(raw_answer, question.options)
        is_correct = student_answer.strip().lower() == question.answer.strip().lower()
        if is_correct:
            score += 1
        question_feedback.append(
            QuestionFeedback(
                question_number=index,
                question_text=question.text,
                correct_answer=question.answer,
                student_answer=student_answer,
                is_correct=is_correct,
                )
            )
    return score, question_feedback


def build_resources(source_chunks: List[SourceChunk]) -> List[ResourceReference]:
    """Dedupe source chunks into a resource list by (book_name, page_number)."""
    seen = set()
    resources = []
    for chunk in source_chunks:
        key = (chunk.book_name, tuple(chunk.page_number or []))
        if chunk.book_name and key not in seen:
            seen.add(key)
            resources.append(ResourceReference(book_name=chunk.book_name, page_number=chunk.page_number))
    return resources


def build_quiz_results_summary(question_feedback: List[QuestionFeedback]) -> str:
    """Format graded question feedback as plain text for the grader agent's context."""
    return "\n\n".join(
        f"Q{feedback.question_number}: {feedback.question_text}\n"
        f"Correct answer: {feedback.correct_answer}\n"
        f"Student answered: {feedback.student_answer} ({'correct' if feedback.is_correct else 'incorrect'})"
        for feedback in question_feedback
        )
