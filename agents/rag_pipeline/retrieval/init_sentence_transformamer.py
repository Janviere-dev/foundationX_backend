from functools import lru_cache
from haystack.utils import ComponentDevice, Secret
from haystack_integrations.components.embedders.sentence_transformers import SentenceTransformersTextEmbedder
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever

from core.config import get_settings
from agents.rag_pipeline.qdrant_config import init_qdrant

@lru_cache
def init_sentence_transformer() -> SentenceTransformersTextEmbedder:
    """
    Init sentence transformer
    """
    settings = get_settings()
    embedder = SentenceTransformersTextEmbedder(
        model=settings.MODEL_EMBEDDER,
        device=ComponentDevice.from_str(settings.EMBED_DEVICE)
        )
    embedder.warm_up()
    return embedder

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
