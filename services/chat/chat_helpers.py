#!/usr/bin/env python3

from typing import List, Optional

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from agents.adk.build import Agents
from agents.llm.llm_definitions import LLMDefinition
from agents.prompts.chat_summary_prompt import chat_summary_instruction, chat_summary_prompt
from agents.schemas.learning_schema import ArticlesLink, External_ressources, VideoLink
from agents.schemas.quiz_generator_schema import SourceChunk

APP_NAME = "Foundationx_chat"

RECENT_TURNS = 4
SUMMARY_EVERY_N_TURNS = 5


def build_context(source_chunks: List[SourceChunk]) -> str:
    """Join source chunk contents into a single context block."""
    return "\n\n---\n\n".join(chunk.content for chunk in source_chunks)


def with_context(instruction: str, context: str) -> str:
    """Prepend a context block to an agent instruction."""
    return f"Context:\n{context}\n\n{instruction}"


def document_to_source_chunk(document) -> SourceChunk:
    """Build a SourceChunk from a retrieved Haystack Document."""
    return SourceChunk(
        book_name=document.meta.get("file_name"),
        page_number=[document.meta["page_number"]] if document.meta.get("page_number") is not None else None,
        content=document.content,
        similarity_score=document.score,
        )


def build_history_block(turns: List[dict]) -> str:
    """Format prior question/answer turns as plain text for the model."""
    if not turns:
        return ""
    return "\n\n".join(
        f"Student: {turn['question']}\nAssistant: {turn['ai_response']}"
        for turn in turns
        )


def build_chat_instruction(instruction: str, chunk_context: str, summary: Optional[str], history_block: str) -> str:
    """Layer curriculum chunks, the rolling summary (if any), and the most
    recent raw turns on top of the base chat instruction."""
    if summary:
        instruction = (
            f"{instruction}\n\n"
            "SUMMARY OF EARLIER CONVERSATION (for your own context only, do not repeat it verbatim):\n"
            f"{summary}"
            )

    if history_block:
        instruction = (
            f"{instruction}\n\n"
            "RECENT CONVERSATION TURNS:\n"
            f"{history_block}"
            )

    return with_context(instruction, chunk_context)


async def run_chat_agent(instruction: str, question: str, user_id: str, tools: list) -> tuple[str, dict]:
    """Run the chat agent and return (final_text, captured_tool_results).

    Unlike agents/adk/build.py's Agents.run() (used by the single-shot
    learning/quiz flows), this also needs the raw results of any tool calls
    the model made, to build ChatResponse.external_sources in Python rather
    than trusting the model to report them - so it runs its own Runner loop
    instead of reusing that helper.
    """
    llm_definition = LLMDefinition(instructions=instruction, prompt=question)
    agent = await llm_definition.chat_response(agent_name="chat_llm", tools=tools)

    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)
    session = await session_service.create_session(app_name=APP_NAME, user_id=user_id)
    message = Content(role="user", parts=[Part(text=question)])

    final_text = ""
    captured: dict[str, list[dict]] = {}
    async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=message):
        for function_response in event.get_function_responses():
            captured.setdefault(function_response.name, []).append(function_response.response)
        if event.is_final_response() and event.content:
            final_text = "".join(part.text for part in event.content.parts if part.text)

    return final_text, captured


def build_external_resources(question: str, captured: dict) -> Optional[External_ressources]:
    """Turn captured search_web_articles/search_web_videos tool results into
    an External_ressources record. The top picks are trimmed here in Python
    rather than trusting the model's prose to only mention two - the tools
    themselves return up to 5 raw results per call."""
    article_results = [
        item
        for call_result in captured.get("search_web_articles", [])
        for item in call_result.get("results", [])
        ]
    video_results = [
        item
        for call_result in captured.get("search_web_videos", [])
        for item in call_result.get("results", [])
        ]

    if not article_results and not video_results:
        return None

    articles = [
        ArticlesLink(
            article_title=item.get("title") or "Untitled",
            article_description=item.get("snippet") or "Related article retrieved from the web.",
            link=item["url"],
            )
        for item in article_results[:2]
        if item.get("url")
        ] or None

    videos = [
        VideoLink(
            video_title=item.get("title") or "Untitled",
            video_description="Related video tutorial retrieved from YouTube.",
            link=item["url"],
            )
        for item in video_results[:1]
        if item.get("url")
        ] or None

    return External_ressources(
        query=question,
        response="External resources retrieved to supplement the curriculum content.",
        article_retrieved=bool(articles),
        video_retreieved=bool(videos),
        articles=articles,
        videos=videos,
        external_source_retrived=bool(articles or videos),
        )


async def run_summary_agent(grade: str, messages: List[dict], user_id: str) -> str:
    """Condense the full turn history into a short rolling summary, run
    every SUMMARY_EVERY_N_TURNS turns."""
    instruction = chat_summary_instruction.format(grade=grade)
    instruction = with_context(instruction, build_history_block(messages))

    agent = Agents(instructions=instruction, prompt=chat_summary_prompt, agent_builder="chat_summary_llm")
    return await agent.run(user_id=user_id, agent_name="chat_summary_llm")
