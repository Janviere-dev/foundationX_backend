#!/usr/bin/env python3

import os

from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.genai.types import GenerateContentConfig

from core.config import get_settings
from agents.schemas.learning_schema import GenerateLearningResponse
from agents.tools.tavily_tool import tavily_tool

os.environ.setdefault(
    "ADK_SUPPRESS_GEMINI_LITELLM_WARNINGS",
    str(get_settings().ADK_SUPPRESS_GEMINI_LITELLM_WARNINGS),
)

class LLMDefinition:
    def __init__(self, instructions:str, prompt:str):
        self.instructions = instructions
        self.prompt = prompt

    def llm_definition(self, agent_name:str, tools:list=[], output_schema=None, use_fallback:bool=False)->LlmAgent:
        settings = get_settings()
        model = settings.LLM_MODEL_FALLBACK if use_fallback else settings.LLM_MODEL
        api_key = settings.GOOGLE_API_KEY_FALLBACK if use_fallback else settings.GOOGLE_API_KEY
        return LlmAgent(
            model=LiteLlm(model=model, api_key=api_key),
            name=agent_name,
            instruction=self.instructions,
            tools=tools,
            output_schema=output_schema,
            generate_content_config=GenerateContentConfig(
                temperature=0.1,
                top_p=0.9,
                top_k=40,
                max_output_tokens=8192,
                frequency_penalty=0.3,
            ),
        )

    async def learning_llm(self, agent_name="learning_llm", use_fallback:bool=False)->LlmAgent:
        return self.llm_definition(
            agent_name=agent_name,
            # tools=[tavily_tool],  # disabled for demo - conflicts with output_schema, see Tavily branch
            output_schema=GenerateLearningResponse,
            use_fallback=use_fallback,
        )

    async def quiz_llm(self, agent_name:str = "quiz_generator_agent")->LlmAgent:
        return self.llm_definition(agent_name=agent_name)
