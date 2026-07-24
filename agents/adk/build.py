#!/usr/bin/env python3
import asyncio
import logging

import openai
from google.genai.types import Content, Part
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from agents.llm.llm_definitions import LLMDefinition
from agents.prompts.learning_prompt import learning_prompt, learning_instruction
from agents.rag_pipeline.retrieval.retriever import Retrieval
from agents.rag_pipeline.retrieval.init_sentence_transformamer import init_sentence_transformer, init_qdrant_retriever
APP_NAME = "Foundationx_learning"

logger = logging.getLogger(__name__)

class Agents:
    def __init__(self, instructions:str, prompt:str):
        self.__instruction = instructions
        self.__prompt = prompt
        self.llm_definition = LLMDefinition(instructions=self.__instruction, prompt=self.__prompt)
        self.__session_service = InMemorySessionService()

    async def build(self, agent_name:str = "learning_llm", use_fallback:bool = False):
        return await self.llm_definition.learning_llm(agent_name=agent_name, use_fallback=use_fallback)

    async def __run_with_agent(self, agent, user_id:str) -> str:
        runner = Runner(agent=agent, app_name=APP_NAME, session_service=self.__session_service)

        session = await self.__session_service.create_session(app_name=APP_NAME, user_id=user_id)
        message = Content(role="user", parts=[Part(text=self.__prompt)])

        final_text = ""
        async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=message):
            if event.is_final_response() and event.content:
                final_text = "".join(part.text for part in event.content.parts if part.text)

        return final_text

    async def run(self, user_id:str, agent_name:str = "learning_llm") -> str:
        """Build the agent and run one turn with the configured prompt,
        returning the final response text. Falls back to a different model
        and API key (rate limit, connection error, model no longer
        available, etc.) if the primary one fails."""
        try:
            agent = await self.build(agent_name=agent_name)
            return await self.__run_with_agent(agent, user_id=user_id)
        except openai.APIError:
            logger.warning("Primary LLM failed, retrying with fallback model", exc_info=True)
            fallback_agent = await self.build(agent_name=agent_name, use_fallback=True)
            return await self.__run_with_agent(fallback_agent, user_id=user_id)

if __name__ == "__main__":
    grade = "Senior 6"
    subject = "Mathematics"
    learning_query = "Quadratic equations"

    retrieval = Retrieval(
        embedder=init_sentence_transformer(),
        retriver=init_qdrant_retriever()
        )
    retrieved = asyncio.run(retrieval.retrieve_learning_content(
        query=learning_query,
        grade=grade,
        subject=subject,
        top_int=5,
        ))
    context = "\n\n---\n\n".join(document.content for document in retrieved["documents"])

    instruction = learning_instruction.format(
        grade=grade,
        subject=subject,
        learning_query=learning_query,
        )
    instruction = f"Context:\n{context}\n\n{instruction}"

    agent = Agents(instructions=instruction, prompt=learning_prompt)
    result = asyncio.run(agent.run(
        user_id="bode-test-123",
        agent_name="learning_agent"
        ))
    print(result)
    print("______________________________________________________________")
    tab_count = result.count("\t")
    print(f"\nLiteral tab characters (\\t) in raw response: {tab_count}")
    if tab_count:
        first_index = result.index("\t")
        print("First occurrence, repr() of surrounding text:")
        print(repr(result[max(0, first_index - 30):first_index + 10]))
