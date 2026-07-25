#!/usr/bin/env python3

from google.adk.tools import FunctionTool
from tavily import TavilyClient

from core.config import get_settings


def tavily_search(query: str) -> dict:
    """Search the web for current information not covered by the curriculum
    context already provided (e.g. recent examples, external references,
    further-reading links). Only call this when the given context is
    missing something specific the query needs."""
    client = TavilyClient(api_key=get_settings().TAVILY_API_KEY)
    return client.search(query=query, max_results=5, include_answer=True)


tavily_tool = FunctionTool(tavily_search)
