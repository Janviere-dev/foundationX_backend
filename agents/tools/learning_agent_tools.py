#!/usr/bin/env python3

from typing import List

from google.adk.tools import FunctionTool, ToolContext
from tavily import TavilyClient
from tavily import AsyncTavilyClient

from agents.schemas.learning_schema import LearningResponsePayload, Checkpoint_question
from core.config import get_settings


async def submit_learning_response(
        learning_plan: List[str],
        learning_content: str,
        checkpoints_questions_response: List[Checkpoint_question],
        tool_context: ToolContext,
) -> dict:
    """
    Call this exactly once, as your final action, with the complete
    structured lesson content.

    Args:
        learning_plan: Step by step lesson plan
        learning_content: The full lesson content
        checkpoints_questions_response: Checkpoint questions for the lesson
    """
    # Flat top-level parameters instead of one nested "response" object -
    # some providers (e.g. via OpenRouter) don't reliably preserve a single
    # deeply nested object argument and the model ends up skipping the
    # structure entirely. Pydantic still validates/coerces each field here
    # (including converting dict items in the list to Checkpoint_question).
    payload = LearningResponsePayload(
        learning_plan=learning_plan,
        learning_content=learning_content,
        checkpoints_questions_response=checkpoints_questions_response,
        )

    tool_context.actions.skip_summarization = True
    return payload.model_dump(mode="json")

async def search_web_articles(
        query:str,
        ) -> dict:
    """
    This tool searches the web for articles and further reading on a topic.
    You may use this tool whenever you need to supplement the chunks with further information
    and when the user specifically ask for further ressources. Select only two best article/book that explains the topic
    Args:
        query: the topic to search for
    """
    settings = get_settings()
    client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
    response = await client.search(
        query=query,
        search_depth="basic",
        max_results=5
        )
    return {
        "results": [
            {
                "title":ressources.get("title"),
                "url":ressources.get("url"),
                "snippet":ressources.get("content","")[:200]
                } for ressources in response.get("results", [])
                ]
            }

async def search_web_videos(
        query:str
        ) -> dict:
    """
    This tool searches the web for videos and further tutorials.
    You may use this tool whenever you need to supplement the chunks with further information
    and when the user request for further ressources. Select only one best video tutorial
    Args:
        query: The topic to search for videos about.
    """
    settings = get_settings()
    client = AsyncTavilyClient(api_key=settings.TAVILY_API_KEY)
    response = await client.search(
        query=query,
        search_depth=settings.SEARCH_DEPTH,
        max_results=5,
        include_domains=["youtube.com"]
        )
    return {
        "results": [
            {
                "title":ressources.get("title"),
                "url":ressources.get("url")
                } for ressources in response.get("results", [])
                ]
            }
 
learning_agent_tool = [
    FunctionTool(submit_learning_response),
    FunctionTool(search_web_articles),
    FunctionTool(search_web_videos)
    ]
