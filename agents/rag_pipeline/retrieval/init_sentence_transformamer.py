from __future__ import annotations

from functools import lru_cache

import aiohttp
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever

from core.config import get_settings
from agents.rag_pipeline.qdrant_config import init_qdrant

@lru_cache
def init_sentence_transformer() -> "SentenceTransformersTextEmbedder":
    """
    Init sentence transformer. Imports are local to this function - this is
    the only place in the app that needs sentence-transformers/torch, and
    production deployments (which use init_remote_embedder() instead) don't
    install those packages at all. Importing them at module level here
    would force every caller of this module to pull them in just to import
    the file, even if this function is never called.
    """
    from haystack.utils import ComponentDevice
    from haystack_integrations.components.embedders.sentence_transformers import SentenceTransformersTextEmbedder

    settings = get_settings()
    embedder = SentenceTransformersTextEmbedder(
        model=settings.MODEL_EMBEDDER,
        device=ComponentDevice.from_str(settings.EMBED_DEVICE)
        )
    embedder.warm_up()
    return embedder


class DeepInfraTextEmbedder:
    """Same .run(text=...) -> {"embedding": [...]} shape as
    SentenceTransformersTextEmbedder, but calls the hosted bge-m3 model on
    DeepInfra instead of loading torch/sentence-transformers locally. Unlike
    the local embedder, .run() is a coroutine - the caller must await it."""

    def __init__(self, model: str, api_key: str):
        self.__model = model
        self.__headers = {"Authorization": f"Bearer {api_key}"}

    async def run(self, text: str) -> dict:
        async with aiohttp.ClientSession(headers=self.__headers) as session:
            async with session.post(
                "https://api.deepinfra.com/v1/openai/embeddings",
                json={"input": text, "model": self.__model, "encoding_format": "float"},
                timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                response.raise_for_status()
                data = await response.json()
                return {"embedding": data["data"][0]["embedding"]}


@lru_cache
def init_remote_embedder() -> DeepInfraTextEmbedder:
    """
    Init remote embedder (DeepInfra-hosted bge-m3)
    """
    settings = get_settings()
    return DeepInfraTextEmbedder(
        model=settings.DEEPINFRA_EMBED_MODEL,
        api_key=settings.DEEP_INFRA_KEY,
        )

@lru_cache
def init_qdrant_retriever()-> QdrantEmbeddingRetriever:
    """
    Init qdrant retriever
    """
    top_k = get_settings().TOP_K
    return QdrantEmbeddingRetriever(
        document_store=init_qdrant(),
        top_k=top_k
        )
