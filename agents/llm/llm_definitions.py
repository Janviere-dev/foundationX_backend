#!/usr/bin/env python3

from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from core.config import get_settings

class LLMDefinition:
    def __init__(self, instructions:str, prompt:str):
        self.instructions = instructions
        self.prompt = prompt

    def llm_definition(self, agent_name:str, tools:list=[]):
        return LlmAgent(
            model=LiteLlm(model = get_settings().LLM_MODEL),
            name=agent_name,
            instruction=self.instructions,
            tools=tools
        )

    async def learning_llm(self, agent_name="Learning LLM"):
        return self.llm_definition(agent_name=agent_name)

    async def quiz_llm(self, agent_name:str = "Quizz generator Agent"):
        return self.llm_definition(agent_name=agent_name)
