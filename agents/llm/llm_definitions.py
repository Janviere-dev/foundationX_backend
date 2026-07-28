#!/usr/bin/env python3

import os

from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent
from google.genai.types import (
    GenerateContentConfig,
    ToolConfig,
    FunctionCallingConfig,
    FunctionCallingConfigMode,
    )

from core.config import get_settings
from agents.schemas.learning_schema import LearningResponsePayload
from agents.schemas.quiz_generator_schema import QuizzQuestionPayload
from agents.schemas.quizz_assessor_schema import QuizzAssessmentPayload

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
        if use_fallback:
            model = settings.LLM_MODEL_FALLBACK
            api_key = settings.GOOGLE_API_KEY_FALLBACK
        elif settings.LLM_ENABLED:
            # Paid path, routed through OpenRouter.
            model = settings.LLM_MODEL
            api_key = settings.OPEN_ROUTER_KEY
        else:
            # Free direct-Gemini path, used while debugging so testing
            # doesn't burn paid OpenRouter credit.
            model = settings.LLM_MODEL_FREE
            api_key = settings.GOOGLE_API_KEY_FREE

        temperature = 1.0 if "gemini-3" in model else 0.1

        return LlmAgent(
            model=LiteLlm(model=model, api_key=api_key),
            name=agent_name,
            instruction=self.instructions,
            tools=tools,
            output_schema=output_schema,
            generate_content_config=GenerateContentConfig(
                temperature=temperature,
                top_p=0.9,
                top_k=40,
                tool_config=ToolConfig(
                    function_calling_config=FunctionCallingConfig(
                        mode=FunctionCallingConfigMode.ANY,
                    )
                ) if tools else None,
            ),
        )

    async def learning_llm(self, agent_name="learning_llm", use_fallback:bool=False)->LlmAgent:
        return self.llm_definition(
            agent_name=agent_name,
            output_schema=LearningResponsePayload,
            use_fallback=use_fallback,
        )

    async def quiz_llm(self, agent_name:str = "quiz_generator_agent", use_fallback:bool=False)->LlmAgent:
        return self.llm_definition(
            agent_name=agent_name,
            output_schema=QuizzQuestionPayload,
            use_fallback=use_fallback,
        )

    async def quiz_grader_llm(self, agent_name:str = "quiz_grader_agent", use_fallback:bool=False)->LlmAgent:
        return self.llm_definition(
            agent_name=agent_name,
            output_schema=QuizzAssessmentPayload,
            use_fallback=use_fallback,
        )
