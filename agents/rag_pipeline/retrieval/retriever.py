#!/usr/bin/env python3
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from haystack.utils import Secret
from haystack.dataclasses import ChatMessage
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from qdrant_client.models import Filter, FieldCondition, MatchText

from agents.rag_pipeline.qdrant_config import init_qdrant
from haystack_integrations.components.generators.google_genai import GoogleGenAIChatGenerator

from agents.rag_pipeline.retrieval.init_sentence_transformamer import init_remote_embedder, init_qdrant_retriever
from core.config import get_settings

if TYPE_CHECKING:
    from haystack_integrations.components.embedders.sentence_transformers import SentenceTransformersTextEmbedder

class Retrieval:
    def __init__(self, embedder:"SentenceTransformersTextEmbedder", retriver:QdrantEmbeddingRetriever):
        self.__embedder = embedder
        self.__retriever = retriver

    async def retrieve_learning_content(self, query:str, subject:str, grade:str, top_int = 5):
        """
        This function retrieve learning content
        """
        query_vector = (await self.__embedder.run(text=query))["embedding"]

        # Built as a native Filter with MatchText explicitly, instead of
        # Haystack's dict-based filters: Haystack auto-picks MatchValue
        # (needs a keyword index) for space-free values and MatchText
        # (needs a text index) for values with a space - but Qdrant only
        # keeps one index type per field, so relying on both meant one
        # kind of value would always break. MatchText works correctly for
        # single-word values too, so it's used consistently for both.
        filters = Filter(
            must=[
                FieldCondition(key="meta.subject", match=MatchText(text=subject)),
                FieldCondition(key="meta.grade", match=MatchText(text=grade)),
                ]
            )
        return self.__retriever.run(
            query_embedding=query_vector,
            filters=filters
            )

def generate_content(prompt: str, context: str = "") -> str:
    full_prompt = f"Context:\n{context}\n\n{prompt}" if context else prompt
    generator = GoogleGenAIChatGenerator(model="gemini-2.5-flash", api_key=Secret.from_token(get_settings().GOOGLE_API_KEY))
    return generator.run(messages=[ChatMessage.from_user(full_prompt)])["replies"][0].text

if __name__ == "__main__":
    retrieval = Retrieval(
        embedder=init_remote_embedder(),
        retriver=init_qdrant_retriever()
        )

    retrieved = asyncio.run(retrieval.retrieve_learning_content(
        query="Retrieve all available chunks on Quadratic Equations",
        grade="Senior 6",
        subject="Mathematics",
        top_int=50)
        )
    #print(retrieved)

    context = "\n\n---\n\n".join(document.content for document in retrieved["documents"])

    print("________________________________________________________________")
    print(generate_content(
        "Explain and provide learning contain that teaches quadratic equations to a Rwandan Senior 6 student in simple terms. Refer to the REB curriculum to explain and build the learning content",
        context=context,
        ))
